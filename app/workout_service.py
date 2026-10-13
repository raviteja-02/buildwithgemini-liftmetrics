"""Workout calculations and logging service for LiftMetrics."""

import datetime
import re
from typing import Any, Dict, List, Optional
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-fde3effbf431"

_db: Optional[firestore.Client] = None


def get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def _slugify(text: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"[-\s]+", "-", clean)


def calculate_one_rep_max(weight_lbs: float, reps: int) -> Dict[str, Any]:
    """Calculate estimated 1-Rep Max (1RM) and working weight percentages.

    Args:
        weight_lbs: The weight lifted in pounds (lbs).
        reps: The number of repetitions completed (>= 1).

    Returns:
        A dictionary with estimated 1RM, working weight percentages, and estimated rep maxes.
    """
    if weight_lbs <= 0 or reps <= 0:
        return {"error": "Weight and reps must both be positive numbers."}

    if reps == 1:
        est_1rm = float(weight_lbs)
        epley = float(weight_lbs)
        brzycki = float(weight_lbs)
    elif reps > 30:
        return {"error": "Repetitions over 30 cannot reliably estimate 1-rep max."}
    else:
        # Standard Epley formula: w * (1 + r / 30)
        epley = weight_lbs * (1.0 + (reps / 30.0))
        # Standard Brzycki formula: w * 36 / (37 - r)
        brzycki = weight_lbs * (36.0 / (37.0 - reps))
        est_1rm = (epley + brzycki) / 2.0

    est_1rm_rounded = round(est_1rm, 1)

    # Standard training percentages
    percentages = {
        "95%": round(est_1rm * 0.95, 1),
        "90%": round(est_1rm * 0.90, 1),
        "85%": round(est_1rm * 0.85, 1),
        "80%": round(est_1rm * 0.80, 1),
        "75%": round(est_1rm * 0.75, 1),
        "70%": round(est_1rm * 0.70, 1),
        "65%": round(est_1rm * 0.65, 1),
    }

    # Estimated working rep maxes
    rep_maxes = {
        "3RM (Heavy Strength)": round(est_1rm / (1.0 + (3.0 / 30.0)), 1),
        "5RM (Strength / Power)": round(est_1rm / (1.0 + (5.0 / 30.0)), 1),
        "8RM (Hypertrophy)": round(est_1rm / (1.0 + (8.0 / 30.0)), 1),
        "10RM (Muscular Endurance)": round(est_1rm / (1.0 + (10.0 / 30.0)), 1),
    }

    return {
        "input_weight_lbs": weight_lbs,
        "input_reps": reps,
        "estimated_1rm_lbs": est_1rm_rounded,
        "epley_estimate_lbs": round(epley, 1),
        "brzycki_estimate_lbs": round(brzycki, 1),
        "training_percentages": percentages,
        "recommended_working_rep_weights": rep_maxes,
    }


def log_workout_session(
    exercise_name: str,
    sets: int,
    reps: int,
    weight_lbs: float,
    notes: str = "",
) -> Dict[str, Any]:
    """Log a workout session to Firestore, compute volume load, and update PR if achieved.

    Args:
        exercise_name: Name of the exercise performed (e.g. 'Barbell Back Squat').
        sets: Number of sets completed.
        reps: Number of reps per set.
        weight_lbs: Weight used in pounds (lbs).
        notes: Optional session observations (e.g. 'RPE 8, felt smooth').

    Returns:
        Session confirmation details including total volume load and new PR status.
    """
    if sets <= 0 or reps <= 0 or weight_lbs < 0:
        return {"error": "Sets, reps, and weight must be positive."}

    db = get_db()
    today_str = datetime.date.today().isoformat()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    volume_load_lbs = round(sets * reps * weight_lbs, 1)

    # 1. Save session to 'workout_sessions'
    session_data = {
        "exercise_name": exercise_name.strip(),
        "sets": int(sets),
        "reps": int(reps),
        "weight_lbs": float(weight_lbs),
        "volume_load_lbs": volume_load_lbs,
        "notes": notes.strip(),
        "date": today_str,
        "created_at": now_iso,
    }
    session_ref = db.collection("workout_sessions").add(session_data)[1]
    session_id = session_ref.id

    # 2. Check personal record for this exercise
    target_clean = exercise_name.strip().lower()
    existing_pr_doc = None
    prev_pr_weight = 0.0

    for doc in db.collection("personal_records").stream():
        data = doc.to_dict()
        doc_ex = str(data.get("exercise_name", "")).lower()
        if target_clean in doc_ex or doc_ex in target_clean:
            existing_pr_doc = doc
            prev_pr_weight = float(data.get("weight_lbs", 0.0))
            break

    is_new_pr = False

    if existing_pr_doc is not None:
        if weight_lbs > prev_pr_weight:
            is_new_pr = True
            pr_data = {
                "id": existing_pr_doc.id,
                "exercise_name": exercise_name.strip(),
                "weight_lbs": float(weight_lbs),
                "reps": int(reps),
                "date": today_str,
                "notes": f"Achieved during workout session! {notes}".strip(),
                "updated_at": now_iso,
            }
            db.collection("personal_records").document(existing_pr_doc.id).set(pr_data)
    else:
        # First recorded PR for this exercise
        is_new_pr = True
        pr_id = _slugify(f"{exercise_name}-pr")
        pr_data = {
            "id": pr_id,
            "exercise_name": exercise_name.strip(),
            "weight_lbs": float(weight_lbs),
            "reps": int(reps),
            "date": today_str,
            "notes": f"Initial PR recorded! {notes}".strip(),
            "updated_at": now_iso,
        }
        db.collection("personal_records").document(pr_id).set(pr_data)

    return {
        "status": "success",
        "session_id": session_id,
        "exercise_name": exercise_name,
        "sets": sets,
        "reps": reps,
        "weight_lbs": weight_lbs,
        "volume_load_lbs": volume_load_lbs,
        "is_new_pr": is_new_pr,
        "previous_pr_lbs": prev_pr_weight if existing_pr_doc else None,
        "message": (
            f"🎉 NEW PERSONAL RECORD! {weight_lbs} lbs (previously {prev_pr_weight} lbs)"
            if is_new_pr and existing_pr_doc
            else f"🎉 FIRST PR SET! {weight_lbs} lbs"
            if is_new_pr
            else f"Logged {sets}x{reps} @ {weight_lbs} lbs (Total volume: {volume_load_lbs} lbs)."
        ),
    }
