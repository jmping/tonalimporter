#!/usr/bin/env python3
"""Local Tonal companion service for Home Assistant.

The service never requires Tonal credentials in environment variables. Home Assistant
submits credentials only when authentication is needed; the password is used for the
OAuth exchange and is not persisted by this service.
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from sync_workouts import (
    apply_workout_titles,
    authenticate,
    build_activity_names,
    build_custom_workouts,
    download_workouts,
    fetch_workout_catalog,
    get_current_strength_scores,
    get_strength_score_history,
    get_user_info,
    get_user_profile,
)

HOST = os.getenv("TONAL_SERVICE_HOST", "0.0.0.0")
PORT = int(os.getenv("TONAL_SERVICE_PORT", "8787"))
SYNC_INTERVAL_MINUTES = int(os.getenv("TONAL_SYNC_INTERVAL_MINUTES", "180"))
TOKEN_FILE = os.getenv("TONAL_TOKEN_FILE", "/data/tonal_token.json")

_state_lock = threading.Lock()
_state: Dict[str, Any] = {
    "status": "auth_required",
    "auth_required": True,
    "last_sync": None,
    "last_error": None,
    "summary": {},
}

_token_lock = threading.Lock()
_tokens: Dict[str, Any] = {}


def _parse_dt(value: str):
    if not value:
        return None
    value = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _load_tokens() -> None:
    global _tokens
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and data.get("id_token"):
            with _token_lock:
                _tokens = data
            with _state_lock:
                _state.update({"status": "starting", "auth_required": False})
    except FileNotFoundError:
        return
    except Exception as exc:  # noqa: BLE001
        with _state_lock:
            _state["last_error"] = f"Could not load saved Tonal token: {exc}"


def _save_tokens(tokens: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(TOKEN_FILE) or ".", exist_ok=True)
    temp = f"{TOKEN_FILE}.tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(tokens, handle, separators=(",", ":"))
    os.chmod(temp, 0o600)
    os.replace(temp, TOKEN_FILE)


def _set_tokens(tokens: Dict[str, Any]) -> None:
    global _tokens
    with _token_lock:
        _tokens = tokens
    _save_tokens(tokens)
    with _state_lock:
        _state.update({"auth_required": False, "status": "starting", "last_error": None})


def _clear_tokens(error: Optional[str] = None) -> None:
    global _tokens
    with _token_lock:
        _tokens = {}
    try:
        os.remove(TOKEN_FILE)
    except FileNotFoundError:
        pass
    with _state_lock:
        _state.update({
            "status": "auth_required",
            "auth_required": True,
            "last_error": error,
        })


def build_summary(export_data: Dict[str, Any]) -> Dict[str, Any]:
    workouts = export_data.get("workouts", [])
    now = datetime.now(timezone.utc)
    latest = workouts[0] if workouts else {}

    def count_since(days: int) -> int:
        cutoff = now - timedelta(days=days)
        return sum(
            1 for workout in workouts
            if (_parse_dt(workout.get("beginTime")) or datetime.min.replace(tzinfo=timezone.utc)) >= cutoff
        )

    def volume_since(days: int) -> float:
        cutoff = now - timedelta(days=days)
        total = 0.0
        for workout in workouts:
            dt = _parse_dt(workout.get("beginTime"))
            if dt and dt >= cutoff:
                total += float(workout.get("totalVolume") or 0)
        return total

    strength_history = export_data.get("strengthScoreHistory") or []
    strength_latest = strength_history[0] if strength_history else {}
    parsed_current = ((export_data.get("currentStrengthScores") or {}).get("parsed") or {})

    return {
        "exported_at": export_data.get("exportedAt"),
        "profile": {
            "total_workouts": (export_data.get("profile") or {}).get("totalWorkouts", len(workouts)),
            "total_volume": (export_data.get("profile") or {}).get("totalVolume"),
        },
        "latest_workout": {
            "id": latest.get("id") or latest.get("workoutActivityID"),
            "begin_time": latest.get("beginTime"),
            "title": latest.get("workoutTitle"),
            "type": latest.get("workoutType"),
            "total_volume": latest.get("totalVolume"),
            "total_reps": latest.get("totalReps"),
            "duration": latest.get("duration") or latest.get("durationSeconds") or latest.get("workoutDuration"),
        },
        "rolling": {
            "workouts_7d": count_since(7),
            "workouts_30d": count_since(30),
            "volume_7d": volume_since(7),
            "volume_30d": volume_since(30),
        },
        "strength": {
            "overall": strength_latest.get("overall") or (parsed_current.get("regions") or {}).get("Overall"),
            "upper": strength_latest.get("upper") or (parsed_current.get("regions") or {}).get("Upper"),
            "lower": strength_latest.get("lower") or (parsed_current.get("regions") or {}).get("Lower"),
            "core": strength_latest.get("core") or (parsed_current.get("regions") or {}).get("Core"),
            "regions": parsed_current.get("regions", {}),
            "muscles": parsed_current.get("muscles", {}),
        },
    }


def authenticate_interactively(email: str, password: str) -> None:
    tokens = authenticate(email, password)
    if not tokens.get("id_token"):
        raise RuntimeError("Tonal authentication did not return an id_token")
    _set_tokens(tokens)
    sync_once()


def sync_once() -> None:
    with _token_lock:
        id_token = _tokens.get("id_token")
    if not id_token:
        _clear_tokens()
        return

    try:
        user_info = get_user_info(id_token)
        user_id = user_info.get("id")
        profile = get_user_profile(id_token, user_id)
        workouts = download_workouts(id_token, user_id)
        workout_catalog = fetch_workout_catalog(id_token, workouts)
        apply_workout_titles(workouts, workout_catalog)
        workouts.sort(key=lambda x: x.get("beginTime", ""), reverse=True)

        export_data = {
            "version": "3.0",
            "exportedAt": datetime.now(timezone.utc).isoformat(),
            "user": user_info,
            "profile": profile,
            "workouts": workouts,
            "activityNames": build_activity_names(workouts),
            "workoutCatalog": workout_catalog,
            "customWorkouts": build_custom_workouts(workouts, workout_catalog),
            "strengthScoreHistory": get_strength_score_history(id_token, user_id),
            "currentStrengthScores": get_current_strength_scores(id_token, user_id),
        }
        summary = build_summary(export_data)
        with _state_lock:
            _state.update({
                "status": "ok",
                "auth_required": False,
                "last_sync": datetime.now(timezone.utc).isoformat(),
                "last_error": None,
                "summary": summary,
            })
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        if "401" in message or "403" in message or "token" in message.lower():
            _clear_tokens("Tonal authentication expired or was rejected")
            return
        with _state_lock:
            _state.update({"status": "error", "last_error": message})


def sync_loop() -> None:
    while True:
        sync_once()
        time.sleep(max(60, SYNC_INTERVAL_MINUTES * 60))


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 16384:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):  # noqa: N802
        with _state_lock:
            snapshot = json.loads(json.dumps(_state))
        if self.path == "/health":
            self._send_json({
                "status": snapshot["status"],
                "auth_required": snapshot["auth_required"],
                "last_sync": snapshot["last_sync"],
                "last_error": snapshot["last_error"],
            })
            return
        if self.path in ("/", "/summary"):
            self._send_json(snapshot)
            return
        self._send_json({"error": "not found"}, 404)

    def do_POST(self):  # noqa: N802
        if self.path == "/auth":
            payload = self._read_json()
            email = str(payload.get("email", "")).strip()
            password = str(payload.get("password", ""))
            if not email or not password:
                self._send_json({"ok": False, "error": "email and password are required"}, 400)
                return
            try:
                authenticate_interactively(email, password)
                self._send_json({"ok": True})
            except Exception as exc:  # noqa: BLE001
                self._send_json({"ok": False, "error": str(exc)}, 401)
            return
        if self.path == "/sync":
            sync_once()
            with _state_lock:
                snapshot = json.loads(json.dumps(_state))
            self._send_json(snapshot)
            return
        self._send_json({"error": "not found"}, 404)

    def log_message(self, format, *args):  # noqa: A003
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))


def main() -> None:
    _load_tokens()
    worker = threading.Thread(target=sync_loop, daemon=True)
    worker.start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Tonal service listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
