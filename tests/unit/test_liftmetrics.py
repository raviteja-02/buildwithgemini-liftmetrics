import pytest
from app.workout_service import calculate_one_rep_max

def test_calculate_one_rep_max_single():
    res = calculate_one_rep_max(300.0, 1, unit="lbs")
    assert res["estimated_1rm_lbs"] == 300.0
    assert "90%" in res["training_percentages"]
    assert res["training_percentages"]["90%"] == 270.0

def test_calculate_one_rep_max_multi_rep():
    res = calculate_one_rep_max(200.0, 5, unit="lbs")
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
def test_calculate_plate_breakdown_metric():
    from app.workout_service import calculate_plate_breakdown
    # 140 kg on 20kg bar = 60kg per side -> 25 + 25 + 10 = 60kg
    res = calculate_plate_breakdown(140.0, 20.0, "kg")
    assert res["status"] == "success"
    assert res["target_weight"] == 140.0
    assert res["weight_per_sleeve"] == 60.0
    assert res["plates_per_sleeve"]["25 kg"] == 2
    assert res["plates_per_sleeve"]["10 kg"] == 1
    assert "Sleeve" in res["ascii_diagram"]

def test_calculate_plate_breakdown_empty_bar():
    from app.workout_service import calculate_plate_breakdown
    res = calculate_plate_breakdown(20.0, 20.0, "kg")
    assert res["status"] == "success"
    assert "Empty barbell" in res["message"]

def test_calculate_lifter_rank_and_stats():
    from app.workout_service import calculate_lifter_rank_and_stats
    # 70kg lifter with 180kg deadlift, 140kg squat, 100kg bench = 420kg total = 6.0x BW -> Level 6 Diamond Titan
    res = calculate_lifter_rank_and_stats(bodyweight=70.0, deadlift=180.0, squat=140.0, bench=100.0, unit="kg")
    assert res["status"] == "success"
    assert res["level"] == 6
    assert "Diamond Titan" in res["rank_title"]
    assert "Desi Strength Pioneer" in res["unlocked_badges"][0]
    assert len(res["unlocked_badges"]) >= 3

def test_calculate_one_rep_max_metric_defaults():
    from app.workout_service import calculate_one_rep_max
    # 100kg x 5 reps
    res = calculate_one_rep_max(100.0, 5, "kg")
    assert res["primary_unit"] == "kg"
    assert res["estimated_1rm_kg"] > 100.0
    assert res["estimated_1rm_lbs"] > 220.0
    assert "90%" in res["training_percentages_kg"]

def test_list_all_exercises():
    from app.agent import list_all_exercises
    res = list_all_exercises()
    assert res["status"] == "success"
    assert res["total_exercises"] >= 15
    assert "Arms" in res["categories"]
    assert "Chest" in res["categories"]
    assert "Back" in res["categories"]
    assert "Legs" in res["categories"]

def test_bicep_curls_form_movement_posture_and_reps():
    from app.agent import get_exercise_details, search_exercises
    # Direct match on the user's exact phrasing
    res = get_exercise_details("how to perform bicep curls with dumbells")
    assert "error" not in res
    assert res["name"] == "Dumbbell Bicep Curl"
    assert "Biceps Brachii" in res["primary_muscle"]
    assert "body_posture" in res
    assert "feet shoulder-width" in res["body_posture"].lower()
    assert "movement_execution" in res
    assert "concentric" in res["movement_execution"].lower()
    assert "supinating wrists" in res["movement_execution"].lower()
    assert "recommended_reps" in res
    assert "8-12 reps" in res["recommended_reps"]
    assert "common_mistakes" in res

    # Verify search also finds it
    search_res = search_exercises("bicep curls with dumbells")
    assert len(search_res) >= 1
    assert any("Bicep Curl" in x.get("name", "") for x in search_res)

