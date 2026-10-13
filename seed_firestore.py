"""Seed script to populate initial exercise catalog and PR data in Firestore."""

from google.cloud import firestore

# CRITICAL: Hardcode the project ID as a string.
# Never derive from google.auth.default() or GOOGLE_CLOUD_PROJECT on Agent Platform.
PROJECT_ID = "qwiklabs-gcp-03-fde3effbf431"

SEEDED_EXERCISES = [
    {
        "id": "barbell-bench-press",
        "name": "Barbell Bench Press",
        "category": "Chest",
        "primary_muscle": "Pectoralis Major",
        "secondary_muscles": ["Triceps", "Anterior Deltoids"],
        "equipment": "Barbell, Flat Bench",
        "difficulty": "Intermediate",
        "default_sets_reps": "3-4 sets of 6-8 reps",
        "form_cues": (
            "Plant feet firmly on the floor. Retract and depress shoulder blades into the bench. "
            "Grip bar slightly wider than shoulder width. Lower bar with control to lower chest "
            "with elbows at ~45 degrees, then drive upward explosively without flaring elbows."
        ),
    },
    {
        "id": "barbell-back-squat",
        "name": "Barbell Back Squat",
        "category": "Legs",
        "primary_muscle": "Quadriceps",
        "secondary_muscles": ["Glutes", "Hamstrings", "Core", "Erector Spinae"],
        "equipment": "Barbell, Squat Rack",
        "difficulty": "Intermediate",
        "default_sets_reps": "3-4 sets of 5-8 reps",
        "form_cues": (
            "Rest bar securely on upper traps. Brace core 360 degrees. Break at hips and knees "
            "simultaneously. Descend under control until thighs are parallel to the floor or lower. "
            "Drive feet through the midfoot to return to standing lockout."
        ),
    },
    {
        "id": "conventional-deadlift",
        "name": "Conventional Barbell Deadlift",
        "category": "Back",
        "primary_muscle": "Posterior Chain",
        "secondary_muscles": ["Hamstrings", "Glutes", "Erector Spinae", "Lats", "Forearms"],
        "equipment": "Barbell, Bumper Plates",
        "difficulty": "Advanced",
        "default_sets_reps": "3 sets of 5 reps",
        "form_cues": (
            "Stand with feet hip-width, barbell directly over midfoot. Hinge at hips and grip bar "
            "just outside shins. Pull slack out of the barbell and engage lats like squeezing oranges "
            "in your armpits. Push the ground away, keeping the bar close to your body until lockout."
        ),
    },
    {
        "id": "overhead-press",
        "name": "Overhead Barbell Press",
        "category": "Shoulders",
        "primary_muscle": "Deltoids",
        "secondary_muscles": ["Triceps", "Upper Chest", "Core"],
        "equipment": "Barbell, Squat Rack",
        "difficulty": "Intermediate",
        "default_sets_reps": "3 sets of 8-10 reps",
        "form_cues": (
            "Grip bar just outside shoulders with forearms vertical. Squeeze glutes and brace core. "
            "Press bar straight vertically, tilting head slightly back to let bar clear chin, then "
            "bring head through window at top lockout."
        ),
    },
    {
        "id": "pull-ups",
        "name": "Pull-Ups",
        "category": "Back",
        "primary_muscle": "Latissimus Dorsi",
        "secondary_muscles": ["Biceps", "Rhomboids", "Core"],
        "equipment": "Pull-Up Bar",
        "difficulty": "Intermediate",
        "default_sets_reps": "3 sets of 6-12 reps",
        "form_cues": (
            "Take an overhand grip slightly wider than shoulder width. Initiate by pulling shoulder "
            "blades down and back. Drive elbows toward your hips until chin clears bar. Lower under "
            "strict control to a full stretch."
        ),
    },
    {
        "id": "romanian-deadlift",
        "name": "Romanian Deadlift (RDL)",
        "category": "Legs",
        "primary_muscle": "Hamstrings",
        "secondary_muscles": ["Glutes", "Lower Back"],
        "equipment": "Barbell or Dumbbells",
        "difficulty": "Intermediate",
        "default_sets_reps": "3-4 sets of 8-12 reps",
        "form_cues": (
            "Hold weight in front of thighs with slight, soft knee bend. Push hips back as far as "
            "possible while keeping spine neutral and bar skimming down legs. Reverse direction when "
            "hamstrings are fully stretched by squeezing glutes and driving hips forward."
        ),
    },
]

SEEDED_PRS = [
    {
        "id": "bench-press-pr",
        "exercise_name": "Barbell Bench Press",
        "weight_lbs": 225.0,
        "reps": 1,
        "date": "2026-10-01",
        "notes": "Smooth single, paused at chest.",
    },
    {
        "id": "squat-pr",
        "exercise_name": "Barbell Back Squat",
        "weight_lbs": 315.0,
        "reps": 1,
        "date": "2026-10-05",
        "notes": "Solid depth, clean lockout.",
    },
]


def seed_database():
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)

    # 1. Seed exercises
    print("Seeding 'exercises' collection...")
    for item in SEEDED_EXERCISES:
        doc_ref = db.collection("exercises").document(item["id"])
        doc_ref.set(item)
        print(f"  ✓ Seeded exercise: {item['name']} ({item['id']})")

    # 2. Seed personal records
    print("Seeding 'personal_records' collection...")
    for pr in SEEDED_PRS:
        doc_ref = db.collection("personal_records").document(pr["id"])
        doc_ref.set(pr)
        print(f"  ✓ Seeded PR: {pr['exercise_name']} - {pr['weight_lbs']} lbs ({pr['id']})")

    print("\n✅ Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
