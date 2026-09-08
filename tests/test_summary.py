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
