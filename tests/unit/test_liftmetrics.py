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
