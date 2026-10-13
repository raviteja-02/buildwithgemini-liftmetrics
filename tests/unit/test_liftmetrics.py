import pytest
from app.workout_service import calculate_one_rep_max

def test_calculate_one_rep_max_single():
    res = calculate_one_rep_max(300.0, 1)
    assert res["estimated_1rm_lbs"] == 300.0
    assert "90%" in res["training_percentages"]
    assert res["training_percentages"]["90%"] == 270.0

def test_calculate_one_rep_max_multi_rep():
    res = calculate_one_rep_max(200.0, 5)
    assert res["estimated_1rm_lbs"] > 200.0
    assert "5RM (Strength / Power)" in res["recommended_working_rep_weights"]

def test_calculate_one_rep_max_invalid():
    res = calculate_one_rep_max(-10.0, 5)
    assert "error" in res

def test_consult_training_science():
    from app.agent import consult_training_science
    res = consult_training_science("hypertrophy volume guidelines")
    assert "hypertrophy" in res.lower()
    assert len(res) > 50

def test_generate_progress_chart():
    from app.workout_service import generate_progress_chart
    res = generate_progress_chart("Deadlift")
    assert res["status"] == "success"
    assert res["exercise_name"] == "Deadlift"
    assert res["image_url"].startswith("https://storage.googleapis.com/")

