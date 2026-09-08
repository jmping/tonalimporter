#!/usr/bin/env python3
"""Small HTTP companion service for exposing Tonal data to Home Assistant."""

import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

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
EMAIL = os.getenv("TONAL_EMAIL")
PASSWORD = os.getenv("TONAL_PASSWORD")

_state_lock = threading.Lock()
_state: Dict[str, Any] = {
    "status": "starting",
    "last_sync": None,
    "last_error": None,
    "summary": {},
}


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


def build_summary(export_data: Dict[str, Any]) -> Dict[str, Any]:
    workouts = export_data.get("workouts", [])
    now = datetime.now(timezone.utc)
    latest = workouts[0] if workouts else {}

    def count_since(days: int) -> int:
        cutoff = now - timedelta(days=days)
        return sum(1 for w in workouts if (_parse_dt(w.get("beginTime")) or datetime.min.replace(tzinfo=timezone.utc)) >= cutoff)

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

    latest_duration = latest.get("duration") or latest.get("durationSeconds") or latest.get("workoutDuration")

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
            "duration": latest_duration,
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


def sync_once() -> None:
    if not EMAIL or not PASSWORD:
        raise RuntimeError("TONAL_EMAIL and TONAL_PASSWORD must be set")

    tokens = authenticate(EMAIL, PASSWORD)
    id_token = tokens["id_token"]
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
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "last_error": None,
            "summary": summary,
        })


def sync_loop() -> None:
    while True:
        try:
            sync_once()
        except Exception as exc:  # noqa: BLE001
            with _state_lock:
                _state.update({
                    "status": "error",
                    "last_error": str(exc),
                })
        time.sleep(max(60, SYNC_INTERVAL_MINUTES * 60))


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        with _state_lock:
            snapshot = json.loads(json.dumps(_state))

        if self.path == "/health":
            self._send_json({
                "status": snapshot["status"],
                "last_sync": snapshot["last_sync"],
                "last_error": snapshot["last_error"],
            }, 200 if snapshot["status"] != "error" else 503)
            return
        if self.path in ("/", "/summary"):
            self._send_json(snapshot)
            return
        self._send_json({"error": "not found"}, 404)

    def log_message(self, format, *args):  # noqa: A003
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))


def main() -> None:
    worker = threading.Thread(target=sync_loop, daemon=True)
    worker.start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Tonal service listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
