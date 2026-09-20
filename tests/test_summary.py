from tonal_service import build_summary


def test_build_summary_exposes_workout_aggregates():
    data = {
        "exportedAt": "2026-09-08T00:00:00+00:00",
        "profile": {"totalWorkouts": 2, "totalVolume": 1200},
        "workouts": [
            {
                "id": "w1",
                "beginTime": "2026-09-07T00:00:00Z",
                "workoutTitle": "Upper Body",
                "workoutType": "PROGRAM",
                "totalVolume": 800,
                "totalReps": 20,
                "durationSeconds": 1800,
                "workoutSetActivity": [
                    {"movementId": "bench", "weight": 50, "repCount": 10, "oneRepMax": 70, "rangeOfMotion": 0.9},
                    {"movementId": "bench", "weight": 60, "repCount": 10, "oneRepMax": 80, "rangeOfMotion": 0.95},
                ],
            },
            {
                "id": "w2",
                "beginTime": "2026-08-01T00:00:00Z",
                "workoutTitle": "Lower Body",
                "workoutType": "CUSTOM",
                "totalVolume": 400,
                "totalReps": 10,
                "durationSeconds": 1200,
                "workoutSetActivity": [
                    {"movementId": "squat", "weight": 40, "repCount": 10, "oneRepMax": 55, "rangeOfMotion": 0.8},
                ],
            },
        ],
        "strengthScoreHistory": [{"overall": 500, "upper": 520, "lower": 480, "core": 450}],
        "currentStrengthScores": {"parsed": {"regions": {}, "muscles": {}}},
    }

    summary = build_summary(data)

    assert summary["profile"]["total_workouts"] == 2
    assert summary["profile"]["total_reps"] == 30
    assert summary["profile"]["total_sets"] == 3
    assert summary["latest_workout"]["set_count"] == 2
    assert summary["latest_workout"]["movement_count"] == 1
    assert summary["latest_workout"]["max_weight"] == 60
    assert summary["records"]["max_set_weight"] == 60
    assert summary["records"]["max_one_rep_max"] == 80
    assert summary["workout_types"]["PROGRAM"] == 1
    assert summary["workout_types"]["CUSTOM"] == 1
    assert summary["strength"]["overall"] == 500
    assert len(summary["recent_workouts"]) == 2


def test_transient_sync_error_preserves_tokens(monkeypatch, tmp_path):
    import tonal_service

    token_file = tmp_path / "tokens.json"
    monkeypatch.setattr(tonal_service, "TOKEN_FILE", str(token_file))
    monkeypatch.setattr(tonal_service, "_tokens", {"id_token": "good", "refresh_token": "refresh"})
    monkeypatch.setattr(tonal_service, "_sync_with_token", lambda token: (_ for _ in ()).throw(RuntimeError("temporary upstream timeout")))

    tonal_service.sync_once()

    assert tonal_service._tokens.get("id_token") == "good"
    assert tonal_service._state["auth_required"] is False
    assert tonal_service._state["status"] == "error"


def test_auth_failure_refreshes_and_retries(monkeypatch, tmp_path):
    import tonal_service

    token_file = tmp_path / "tokens.json"
    monkeypatch.setattr(tonal_service, "TOKEN_FILE", str(token_file))
    monkeypatch.setattr(tonal_service, "_tokens", {"id_token": "expired", "refresh_token": "refresh"})
    calls = []

    def fake_sync(token):
        calls.append(token)
        if token == "expired":
            raise tonal_service.TonalAuthenticationError("rejected")

    monkeypatch.setattr(tonal_service, "_sync_with_token", fake_sync)
    monkeypatch.setattr(
        tonal_service,
        "refresh_authentication",
        lambda token: {"id_token": "fresh", "access_token": "fresh-access"},
    )

    tonal_service.sync_once()

    assert calls == ["expired", "fresh"]
    assert tonal_service._tokens["id_token"] == "fresh"
    assert tonal_service._tokens["refresh_token"] == "refresh"
    assert tonal_service._state["auth_required"] is False


def test_rejected_refresh_requires_reauth(monkeypatch, tmp_path):
    import tonal_service

    token_file = tmp_path / "tokens.json"
    monkeypatch.setattr(tonal_service, "TOKEN_FILE", str(token_file))
    monkeypatch.setattr(tonal_service, "_tokens", {"id_token": "expired", "refresh_token": "bad-refresh"})
    monkeypatch.setattr(
        tonal_service,
        "_sync_with_token",
        lambda token: (_ for _ in ()).throw(tonal_service.TonalAuthenticationError("rejected")),
    )
    monkeypatch.setattr(
        tonal_service,
        "refresh_authentication",
        lambda token: (_ for _ in ()).throw(tonal_service.TonalAuthenticationError("refresh rejected")),
    )

    tonal_service.sync_once()

    assert tonal_service._tokens == {}
    assert tonal_service._state["auth_required"] is True


def test_transient_sync_error_preserves_tokens(monkeypatch, tmp_path):
    import tonal_service

    token_file = tmp_path / "tokens.json"
    monkeypatch.setattr(tonal_service, "TOKEN_FILE", str(token_file))
    monkeypatch.setattr(tonal_service, "_tokens", {"id_token": "good", "refresh_token": "refresh"})
    tonal_service._state["auth_required"] = False
    tonal_service._state["auth_failures"] = 0

    def fail_sync(_token):
        raise RuntimeError("temporary upstream timeout")

    monkeypatch.setattr(tonal_service, "_sync_with_token", fail_sync)
    tonal_service.sync_once()

    assert tonal_service._tokens.get("id_token") == "good"
    assert tonal_service._state["auth_required"] is False
    assert tonal_service._state["auth_failures"] == 0
    assert tonal_service._state["status"] == "error"


def test_auth_failure_refreshes_and_resets_counter(monkeypatch, tmp_path):
    import tonal_service

    token_file = tmp_path / "tokens.json"
    monkeypatch.setattr(tonal_service, "TOKEN_FILE", str(token_file))
    monkeypatch.setattr(tonal_service, "_tokens", {"id_token": "expired", "refresh_token": "refresh"})
    tonal_service._state["auth_required"] = False
    tonal_service._state["auth_failures"] = 2

    calls = []

    def fake_sync(token):
        calls.append(token)
        if token == "expired":
            raise tonal_service.TonalAuthenticationError("rejected")
        tonal_service._state["auth_failures"] = 0

    monkeypatch.setattr(tonal_service, "_sync_with_token", fake_sync)
    monkeypatch.setattr(
        tonal_service,
        "refresh_authentication",
        lambda _token: {"id_token": "fresh", "access_token": "fresh-access"},
    )

    tonal_service.sync_once()

    assert calls == ["expired", "fresh"]
    assert tonal_service._tokens["id_token"] == "fresh"
    assert tonal_service._tokens["refresh_token"] == "refresh"
    assert tonal_service._state["auth_required"] is False
    assert tonal_service._state["auth_failures"] == 0


def test_reauth_only_after_three_consecutive_auth_failures(monkeypatch, tmp_path):
    import tonal_service

    token_file = tmp_path / "tokens.json"
    monkeypatch.setattr(tonal_service, "TOKEN_FILE", str(token_file))
    monkeypatch.setattr(tonal_service, "AUTH_FAILURE_THRESHOLD", 3)
    monkeypatch.setattr(tonal_service, "_tokens", {"id_token": "expired", "refresh_token": "bad-refresh"})
    tonal_service._state["auth_required"] = False
    tonal_service._state["auth_failures"] = 0

    def reject_sync(_token):
        raise tonal_service.TonalAuthenticationError("rejected")

    def reject_refresh(_token):
        raise tonal_service.TonalAuthenticationError("refresh rejected")

    monkeypatch.setattr(tonal_service, "_sync_with_token", reject_sync)
    monkeypatch.setattr(tonal_service, "refresh_authentication", reject_refresh)

    tonal_service.sync_once()
    assert tonal_service._state["auth_failures"] == 1
    assert tonal_service._state["auth_required"] is False
    assert tonal_service._tokens

    tonal_service.sync_once()
    assert tonal_service._state["auth_failures"] == 2
    assert tonal_service._state["auth_required"] is False
    assert tonal_service._tokens

    tonal_service.sync_once()
    assert tonal_service._state["auth_failures"] == 3
    assert tonal_service._state["auth_required"] is True
    assert tonal_service._tokens == {}
