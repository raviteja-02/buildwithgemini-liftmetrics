#!/usr/bin/env python3
"""
Seed comprehensive exercise catalog into Firestore for LiftMetrics.
Includes detailed biomechanical form cues, body posture, movement execution,
and set/rep recommendations across all major muscle groups.
"""

import sys
import os
from typing import List, Dict, Any
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-fde3effbf431"

EXERCISE_CATALOG: List[Dict[str, Any]] = [
    # --- ARMS / BICEPS & TRICEPS ---
    {
        "id": "dumbbell-bicep-curl",
        "name": "Dumbbell Bicep Curl",
        "aliases": [
            "bicep curls with dumbells",
            "bicep curls with dumbbells",
            "dumbbell bicep curls",
            "dumbbell curl",
            "standing dumbbell bicep curl",
            "bicep curl",
        ],
        "category": "Arms",
        "primary_muscle": "Biceps Brachii (Short & Long Heads)",
        "secondary_muscles": ["Brachialis", "Brachioradialis", "Forearm Flexors"],
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "body_posture": (
            "Stand tall with feet shoulder-width apart, knees slightly soft (unlocked). "
            "Chest held high, shoulder blades retracted and depressed (pulled back and down). "
            "Engage core and glutes firmly to lock your pelvis and prevent lower-back arching or torso sway. "
            "Arms hang at sides with elbows tucked directly against your ribcage."
        ),
        "movement_execution": (
            "1. Setup: Hold dumbbells at sides with a neutral grip (palms facing inward).\n"
            "2. Concentric Phase: Curl weights upward in a smooth arc while actively supinating wrists (turn palms to face the ceiling/shoulders as you ascend). Keep elbows stationary pinned to your ribs.\n"
            "3. Peak Contraction: Squeeze biceps forcefully at the top (near shoulder height) for 1 full second without allowing elbows to drift forward.\n"
            "4. Eccentric Phase: Slowly lower dumbbells back down under strict control (2-3 second negative) until elbows reach full extension for a complete bicep stretch."
        ),
        "recommended_reps": (
            "- Hypertrophy (Muscle Growth): 3-4 sets of 8-12 reps (stopping 1-2 reps shy of failure, RIR 1-2).\n"
            "- Strength / Power: 4 sets of 6-8 reps with heavier dumbbells and strict tempo.\n"
            "- Muscular Endurance & Pump: 3 sets of 12-15 reps with 60s rest intervals."
        ),
        "default_sets_reps": "3-4 sets of 8-12 reps",
        "form_cues": "Elbows pinned to ribs, full wrist supination at top, 3-second negative descent, zero torso swinging.",
        "common_mistakes": [
            "Swinging the torso or using hip momentum to heave the dumbbells up.",
            "Letting elbows drift forward, shifting tension onto anterior deltoids.",
            "Cutting the bottom range of motion short instead of achieving a full stretch.",
            "Allowing wrists to hyperextend (flop backward) under load."
        ],
    },
    {
        "id": "dumbbell-hammer-curl",
        "name": "Dumbbell Hammer Curl",
        "aliases": ["hammer curl", "hammer curls", "dumbbell hammer curls"],
        "category": "Arms",
        "primary_muscle": "Brachialis & Brachioradialis",
        "secondary_muscles": ["Biceps Brachii (Long Head)", "Forearms"],
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "body_posture": "Stand tall, shoulder blades packed, core braced, dumbbells held with neutral grip (thumbs pointing up) throughout the entire movement.",
        "movement_execution": "Curl dumbbells toward shoulders maintaining strict neutral palms-in grip. Squeeze brachialis at peak, lower slowly over 2-3 seconds.",
        "recommended_reps": "3-4 sets of 8-12 reps for thick forearm and arm development.",
        "default_sets_reps": "3 sets of 10-12 reps",
        "form_cues": "Thumbs up throughout, elbows pinned to sides, control the eccentric descent.",
        "common_mistakes": ["Elbow flaring outward", "Torso swinging"],
    },
    {
        "id": "barbell-bicep-curl",
        "name": "Barbell Bicep Curl",
        "aliases": ["barbell curl", "straight bar curl", "ez bar curl"],
        "category": "Arms",
        "primary_muscle": "Biceps Brachii",
        "secondary_muscles": ["Brachialis", "Forearms"],
        "equipment": "Barbell or EZ-Curl Bar",
        "difficulty": "Intermediate",
        "body_posture": "Athletic stance, feet shoulder-width, supinated grip shoulder-width apart, elbows pinned against the ribcage.",
        "movement_execution": "Curl bar upward in a smooth arc to chin level without rocking backwards. Lower bar under control to full elbow lockout.",
        "recommended_reps": "3-4 sets of 6-10 reps for progressive bicep overload.",
        "default_sets_reps": "3-4 sets of 8-10 reps",
        "form_cues": "Lock shoulders down, drive wrists towards shoulders, controlled 2-second negative.",
        "common_mistakes": ["Rocking hips back and forward", "Bouncing the bar at the bottom"],
    },
    {
        "id": "tricep-overhead-extension",
        "name": "Seated Overhead Dumbbell Tricep Extension",
        "aliases": ["overhead tricep extension", "dumbbell tricep extension", "overhead dumbbell extension"],
        "category": "Arms",
        "primary_muscle": "Triceps Brachii (Long Head)",
        "secondary_muscles": ["Triceps Medial & Lateral Heads"],
        "equipment": "Dumbbell, Bench with back support",
        "difficulty": "Intermediate",
        "body_posture": "Sit upright with back supported. Hold dumbbell vertically overhead with both hands cup-gripping the top plate. Core tight.",
        "movement_execution": "Lower dumbbell behind head by flexing elbows to ~90 degrees, keeping upper arms vertical near ears. Press upward extending elbows fully.",
        "recommended_reps": "3 sets of 10-12 reps with 60-90s rest.",
        "default_sets_reps": "3 sets of 10-12 reps",
        "form_cues": "Keep elbows pointing forward not flared wide, full stretch behind neck.",
        "common_mistakes": ["Excessive elbow flaring", "Arching lower back off the bench"],
    },
    {
        "id": "tricep-rope-pushdown",
        "name": "Cable Tricep Rope Pushdown",
        "aliases": ["tricep pushdown", "cable rope pushdown", "rope pushdowns"],
        "category": "Arms",
        "primary_muscle": "Triceps Brachii (Lateral & Medial Heads)",
        "secondary_muscles": ["Triceps Long Head"],
        "equipment": "Cable Tower, Rope Attachment",
        "difficulty": "Beginner",
        "body_posture": "Hinge slightly at hips (~15 degrees), elbows glued to your sides, chest upright.",
        "movement_execution": "Push rope down and spread ends apart at bottom of motion. Squeeze triceps hard, return until forearms are parallel to floor.",
        "recommended_reps": "3-4 sets of 10-15 reps.",
        "default_sets_reps": "3-4 sets of 12-15 reps",
        "form_cues": "Flare rope ends apart at bottom, lock elbows in place, resist the stack on the way up.",
        "common_mistakes": ["Shoulders rolling forward", "Using bodyweight to press down"],
    },

    # --- CHEST ---
    {
        "id": "barbell-bench-press",
        "name": "Barbell Bench Press",
        "aliases": ["bench press", "flat bench press", "barbell bench"],
        "category": "Chest",
        "primary_muscle": "Pectoralis Major (Mid/Lower Sternocostal)",
        "secondary_muscles": ["Triceps Brachii", "Anterior Deltoids"],
        "equipment": "Olympic Barbell, Flat Bench",
        "difficulty": "Intermediate",
        "body_posture": "5-point contact (head, upper back, glutes on bench, both feet flat on floor). Retract and depress scapulae to create a stable base.",
        "movement_execution": "Unrack bar over chest, lower with control to lower sternum with elbows tucked at 45-75 degrees. Press upward explosively.",
        "recommended_reps": "3-5 sets of 4-8 reps for strength and mass.",
        "default_sets_reps": "3-4 sets of 6-8 reps",
        "form_cues": "Feet anchored, squeeze bar tight, touch mid/lower chest, drive through feet.",
        "common_mistakes": ["Elbows flaring at 90 degrees", "Bouncing bar off sternum"],
    },
    {
        "id": "incline-dumbbell-press",
        "name": "Incline Dumbbell Press",
        "aliases": ["incline dumbbell bench press", "incline press", "dumbbell incline press"],
        "category": "Chest",
        "primary_muscle": "Pectoralis Major (Clavicular / Upper Chest)",
        "secondary_muscles": ["Anterior Deltoids", "Triceps Brachii"],
        "equipment": "Adjustable Bench (30-45 deg), Dumbbells",
        "difficulty": "Intermediate",
        "body_posture": "Set bench to 30-45 degree incline. Scapulae retracted, feet flat on floor, dumbbells held at chest level.",
        "movement_execution": "Press dumbbells upward and slightly inward in an arc. Lower under control until dumbbells reach chest level for deep stretch.",
        "recommended_reps": "3-4 sets of 8-12 reps.",
        "default_sets_reps": "3-4 sets of 8-10 reps",
        "form_cues": "30-degree incline optimal, elbows at 45 degrees, full stretch at bottom.",
        "common_mistakes": ["Incline too steep (>45 deg shifts to shoulders)", "Clanging dumbbells together at top"],
    },
    {
        "id": "dumbbell-chest-fly",
        "name": "Dumbbell Chest Fly",
        "aliases": ["chest fly", "dumbbell flyes", "flat dumbbell fly"],
        "category": "Chest",
        "primary_muscle": "Pectoralis Major",
        "secondary_muscles": ["Anterior Deltoids"],
        "equipment": "Flat Bench, Dumbbells",
        "difficulty": "Intermediate",
        "body_posture": "Lie flat on bench, slight bend in elbows locked throughout movement, feet flat on floor.",
        "movement_execution": "Lower weights outward in wide arc until chest is stretched. Squeeze chest to bring weights back above chest.",
        "recommended_reps": "3 sets of 10-15 reps.",
        "default_sets_reps": "3 sets of 12-15 reps",
        "form_cues": "Hug a tree motion, maintain static elbow bend, feel deep pectoral stretch.",
        "common_mistakes": ["Bending elbows into a press", "Dropping dumbbells too deep causing shoulder strain"],
    },

    # --- BACK ---
    {
        "id": "conventional-deadlift",
        "name": "Conventional Barbell Deadlift",
        "aliases": ["deadlift", "barbell deadlift", "conventional deadlift"],
        "category": "Back",
        "primary_muscle": "Posterior Chain (Erector Spinae, Gluteus Maximus, Hamstrings)",
        "secondary_muscles": ["Latissimus Dorsi", "Trapezius", "Forearms / Grip", "Core"],
        "equipment": "Olympic Barbell, Bumper/Iron Plates",
        "difficulty": "Advanced",
        "body_posture": "Feet hip-width apart, barbell over mid-foot. Hinge at hips, grip bar just outside knees. Spine neutral, lats engaged.",
        "movement_execution": "Push floor away through heels, extending hips and knees simultaneously. Lock out hips tall at top. Hinge back down under control.",
        "recommended_reps": "3-5 sets of 3-5 reps for raw strength.",
        "default_sets_reps": "3 sets of 5 reps",
        "form_cues": "Bar against shins, chest proud, pull slack out of bar, push floor away.",
        "common_mistakes": ["Rounding lower back", "Bar drifting away from body"],
    },
    {
        "id": "pull-ups",
        "name": "Pull-Ups",
        "aliases": ["pull up", "pullups", "chin-ups", "chin ups"],
        "category": "Back",
        "primary_muscle": "Latissimus Dorsi",
        "secondary_muscles": ["Biceps Brachii", "Teres Major", "Rhomboids", "Middle/Lower Trapezius"],
        "equipment": "Pull-Up Bar",
        "difficulty": "Intermediate",
        "body_posture": "Pronated grip slightly wider than shoulders. Core braced, legs straight or crossed, hollow-body position.",
        "movement_execution": "Initiate by depressing scapulae, then pull chest toward bar until chin clears. Lower under control to dead hang.",
        "recommended_reps": "3-4 sets of 6-10 reps (or bodyweight to failure).",
        "default_sets_reps": "3-4 sets of 8-10 reps",
        "form_cues": "Lead with chest, drive elbows into back pockets, full dead hang at bottom.",
        "common_mistakes": ["Kicking legs or kipping", "Half reps without chin over bar"],
    },
    {
        "id": "barbell-bent-over-row",
        "name": "Barbell Bent-Over Row",
        "aliases": ["barbell row", "bent over row", "pendlay row"],
        "category": "Back",
        "primary_muscle": "Latissimus Dorsi & Rhomboids",
        "secondary_muscles": ["Trapezius", "Posterior Deltoids", "Biceps Brachii"],
        "equipment": "Olympic Barbell",
        "difficulty": "Intermediate",
        "body_posture": "Hinge at hips to ~45-degree torso angle. Knees soft, lower back arched/neutral, overhand grip.",
        "movement_execution": "Pull barbell toward belly button driving elbows toward ceiling. Squeeze shoulder blades together at top. Lower slowly.",
        "recommended_reps": "3-4 sets of 6-10 reps.",
        "default_sets_reps": "3-4 sets of 8 reps",
        "form_cues": "Pull to lower ribs, squeeze scapulae, keep torso angle frozen.",
        "common_mistakes": ["Standing upright during reps", "Jerking weight with lower back"],
    },

    # --- SHOULDERS ---
    {
        "id": "overhead-press",
        "name": "Overhead Barbell Press",
        "aliases": ["military press", "ohp", "standing barbell shoulder press", "overhead press"],
        "category": "Shoulders",
        "primary_muscle": "Anterior Deltoids",
        "secondary_muscles": ["Lateral Deltoids", "Triceps Brachii", "Upper Pectorals", "Core"],
        "equipment": "Olympic Barbell",
        "difficulty": "Intermediate",
        "body_posture": "Stand with feet shoulder-width. Grip bar just outside shoulders. Elbows slightly forward of bar. Squeeze glutes and core.",
        "movement_execution": "Press bar straight overhead moving head back slightly to clear chin. Lock out overhead with head through window. Lower to clavicle.",
        "recommended_reps": "3-4 sets of 5-8 reps.",
        "default_sets_reps": "3-4 sets of 6-8 reps",
        "form_cues": "Squeeze glutes tight, bar path straight, push head through window at lockout.",
        "common_mistakes": ["Arching lumbar spine excessively", "Pressing bar forward in an arc"],
    },
    {
        "id": "dumbbell-lateral-raise",
        "name": "Standing Dumbbell Lateral Raise",
        "aliases": ["lateral raise", "side lateral raise", "dumbbell side raises"],
        "category": "Shoulders",
        "primary_muscle": "Lateral Deltoids (Side Shoulders)",
        "secondary_muscles": ["Anterior Deltoids", "Trapezius"],
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "body_posture": "Stand tall or hinge slightly forward (~10 deg). Dumbbells at sides, elbows soft, shoulders relaxed.",
        "movement_execution": "Raise arms out to sides in scapular plane (30 deg forward) until parallel to floor. Lead with elbows. Lower under control over 2s.",
        "recommended_reps": "3-4 sets of 12-15 reps.",
        "default_sets_reps": "3-4 sets of 12-15 reps",
        "form_cues": "Pour the water slightly with pinkies up, lead with elbows, pause 1s at parallel.",
        "common_mistakes": ["Shrugging traps up to ears", "Swinging heavy weights with hips"],
    },

    # --- LEGS ---
    {
        "id": "barbell-back-squat",
        "name": "Barbell Back Squat",
        "aliases": ["back squat", "squat", "barbell squat"],
        "category": "Legs",
        "primary_muscle": "Quadriceps & Gluteus Maximus",
        "secondary_muscles": ["Hamstrings", "Adductors", "Calves", "Core / Spinal Erectors"],
        "equipment": "Olympic Barbell, Squat Rack",
        "difficulty": "Intermediate",
        "body_posture": "Bar across upper traps (high bar) or rear delts (low bar). Feet shoulder-width apart, toes turned out 15-30 degrees. Brace core 360 degrees.",
        "movement_execution": "Break at hips and knees simultaneously. Descend until hip crease is below parallel. Drive up through midfoot.",
        "recommended_reps": "3-5 sets of 5-8 reps.",
        "default_sets_reps": "3-4 sets of 6-8 reps",
        "form_cues": "Chest proud, knees track over toes, hit depth below parallel, drive through mid-foot.",
        "common_mistakes": ["Knees caving inward (valgus collapse)", "Heels rising off floor"],
    },
    {
        "id": "romanian-deadlift",
        "name": "Romanian Deadlift (RDL)",
        "aliases": ["rdl", "romanian deadlift", "barbell rdl", "dumbbell rdl"],
        "category": "Legs",
        "primary_muscle": "Hamstrings & Gluteus Maximus",
        "secondary_muscles": ["Erector Spinae", "Lats", "Forearms"],
        "equipment": "Barbell or Dumbbells",
        "difficulty": "Intermediate",
        "body_posture": "Stand tall holding weight in front. Feet hip-width apart. Soft bend in knees kept constant.",
        "movement_execution": "Push hips straight back like trying to touch a wall behind you. Slide bar down shins until deep hamstring stretch. Drive hips forward.",
        "recommended_reps": "3-4 sets of 8-12 reps.",
        "default_sets_reps": "3-4 sets of 8-10 reps",
        "form_cues": "Soft knees, push hips back to wall, keep bar glued to legs, neutral neck.",
        "common_mistakes": ["Squatting down instead of hip hinging", "Rounding upper or lower spine"],
    },
    {
        "id": "dumbbell-bulgarian-split-squat",
        "name": "Dumbbell Bulgarian Split Squat",
        "aliases": ["bulgarian split squat", "split squat", "rear foot elevated split squat"],
        "category": "Legs",
        "primary_muscle": "Quadriceps & Gluteus Maximus",
        "secondary_muscles": ["Hamstrings", "Adductors", "Calves"],
        "equipment": "Dumbbells, Bench",
        "difficulty": "Advanced",
        "body_posture": "Elevate rear foot on bench laces-down. Front foot planted ~3 feet ahead. Torso upright or slight forward lean for glute bias.",
        "movement_execution": "Lower rear knee toward floor until front thigh is parallel. Drive through front heel to return to top.",
        "recommended_reps": "3 sets of 8-12 reps per leg.",
        "default_sets_reps": "3 sets of 10 reps per leg",
        "form_cues": "90-degree angle on front knee, control descent, push through front heel.",
        "common_mistakes": ["Front foot too close to bench causing knee strain", "Losing balance due to narrow stance"],
    },

    # --- CORE ---
    {
        "id": "hanging-leg-raise",
        "name": "Hanging Leg Raise",
        "aliases": ["leg raise", "hanging knee raise", "hanging leg raises"],
        "category": "Core",
        "primary_muscle": "Rectus Abdominis (Lower Abs)",
        "secondary_muscles": ["Hip Flexors", "Obliques", "Forearms / Grip"],
        "equipment": "Pull-Up Bar",
        "difficulty": "Intermediate",
        "body_posture": "Hang from bar with overhand grip, shoulders engaged (scapular pull), body stationary without swinging.",
        "movement_execution": "Tilt pelvis back and curl knees or straight legs upward to chest level. Squeeze abs at top, lower slowly without swinging.",
        "recommended_reps": "3-4 sets of 10-15 reps.",
        "default_sets_reps": "3 sets of 12 reps",
        "form_cues": "Roll pelvis upward, avoid swinging momentum, 2-second negative descent.",
        "common_mistakes": ["Kipping and swinging from shoulders", "Only using hip flexors without posterior pelvic tilt"],
    },
    {
        "id": "plank",
        "name": "Forearm Plank",
        "aliases": ["plank", "core plank", "forearm plank hold"],
        "category": "Core",
        "primary_muscle": "Transverse Abdominis & Rectus Abdominis",
        "secondary_muscles": ["Glutes", "Shoulders", "Quadriceps"],
        "equipment": "Floor Mat",
        "difficulty": "Beginner",
        "body_posture": "Forearms on ground, elbows below shoulders. Feet together or hip-width. Straight line from head to heels.",
        "movement_execution": "Engage abs as if bracing for a punch. Squeeze glutes and quads tight. Hold position breathing steadily.",
        "recommended_reps": "3 sets of 45-60 second holds.",
        "default_sets_reps": "3 sets of 45-60 seconds",
        "form_cues": "Belly button into spine, squeeze glutes, do not let hips sag or hike up.",
        "common_mistakes": ["Hips sagging toward floor", "Butt sticking high in the air"],
    },
]


def seed_database():
    """Upload or update all exercises in the Firestore collection."""
    db = firestore.Client(project=PROJECT_ID)
    print(f"Connecting to Firestore for project: {PROJECT_ID}")
    collection_ref = db.collection("exercises")

    count = 0
    for ex in EXERCISE_CATALOG:
        doc_id = ex["id"]
        collection_ref.document(doc_id).set(ex, merge=True)
        count += 1
        print(f"[{count}/{len(EXERCISE_CATALOG)}] Upserted: {ex['name']} ({doc_id})")

    print(f"\n Successfully seeded {count} exercises into Firestore!")


if __name__ == "__main__":
    seed_database()
