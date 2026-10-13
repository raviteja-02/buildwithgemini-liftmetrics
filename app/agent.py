# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import re
from typing import Any, Dict, List, Optional

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore
from google.genai import types

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from app.a2ui_utils import a2ui_callback
from app.external_service import fetch_nutrition_facts, lookup_external_muscle_info
from app.media_service import generate_exercise_form_image, generate_exercise_motion_video
from app.workout_service import calculate_one_rep_max, log_workout_session

MODEL = "gemini-3.8-flash"

# CRITICAL: Hardcode the project ID as a string.
# Never derive from google.auth.default() or GOOGLE_CLOUD_PROJECT;
# on Agent Platform those return the project number, which breaks Firestore.
PROJECT_ID = "qwiklabs-gcp-03-fde3effbf431"
AGENT_ENGINE_ID = "4494360431162294272"
AGENT_ENGINE_RESOURCE = "projects/282829779330/locations/us-east1/reasoningEngines/4494360431162294272"

_db: Optional[firestore.Client] = None


def get_db() -> firestore.Client:
    """Returns a singleton Firestore client configured for the project."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def _slugify(text: str) -> str:
    """Generate a clean slug identifier from a name."""
    clean = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"[-\s]+", "-", clean)


def search_exercises(query: str = "", category: str = "") -> List[Dict[str, Any]]:
    """Search or list exercises in the catalog stored in Firestore.

    Args:
        query: Optional keyword to search within exercise name, primary muscle, or equipment.
        category: Optional category filter (e.g. 'Chest', 'Legs', 'Back', 'Shoulders', 'Arms').

    Returns:
        A list of matching exercise dictionaries from Firestore.
    """
    db = get_db()
    docs = db.collection("exercises").stream()
    results = []
    q_lower = query.strip().lower()
    cat_lower = category.strip().lower()

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        # Category filter
        doc_category = str(data.get("category", "")).lower()
        if cat_lower and cat_lower not in doc_category:
            continue

        # Query keyword search
        if q_lower:
            name = str(data.get("name", "")).lower()
            muscle = str(data.get("primary_muscle", "")).lower()
            equip = str(data.get("equipment", "")).lower()
            if q_lower not in name and q_lower not in muscle and q_lower not in equip:
                continue

        results.append(data)

    return results


def get_exercise_details(exercise_name: str) -> Dict[str, Any]:
    """Get full details and form cues for a specific exercise from Firestore.

    Args:
        exercise_name: Name or identifier of the exercise (e.g. 'Barbell Bench Press', 'pull-ups').

    Returns:
        The exercise record with form cues and specifications, or an error dictionary if not found.
    """
    db = get_db()
    slug_id = _slugify(exercise_name)

    # 1. Direct document lookup by slug
    doc = db.collection("exercises").document(slug_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data

    # 2. Case-insensitive search by name
    target = exercise_name.strip().lower()
    for item in db.collection("exercises").stream():
        data = item.to_dict()
        if target in str(data.get("name", "")).lower():
            data["id"] = item.id
            return data

    return {"error": f"Exercise '{exercise_name}' not found in the catalog."}


def add_exercise(
    name: str,
    category: str,
    primary_muscle: str,
    equipment: str,
    form_cues: str,
    default_sets_reps: str = "3 sets of 8-12 reps",
    difficulty: str = "Intermediate",
) -> Dict[str, Any]:
    """Add a new exercise into the Firestore catalog.

    Args:
        name: Name of the exercise (e.g. 'Incline Dumbbell Press').
        category: Category (e.g. 'Chest', 'Legs', 'Back', 'Shoulders', 'Arms').
        primary_muscle: Targeted main muscle (e.g. 'Upper Pectorals').
        equipment: Equipment needed (e.g. 'Dumbbells, Adjustable Bench').
        form_cues: Step-by-step coaching cues for proper posture and execution.
        default_sets_reps: Standard recommended sets and reps (e.g. '3-4 sets of 8-10 reps').
        difficulty: Difficulty level ('Beginner', 'Intermediate', 'Advanced').

    Returns:
        Confirmation dictionary with the created exercise details and document ID.
    """
    db = get_db()
    doc_id = _slugify(name)
    data = {
        "id": doc_id,
        "name": name.strip(),
        "category": category.strip(),
        "primary_muscle": primary_muscle.strip(),
        "equipment": equipment.strip(),
        "form_cues": form_cues.strip(),
        "default_sets_reps": default_sets_reps.strip(),
        "difficulty": difficulty.strip(),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    db.collection("exercises").document(doc_id).set(data)
    return {"status": "success", "message": f"Added exercise '{name}' to Firestore.", "exercise": data}


def record_personal_record(
    exercise_name: str,
    weight_lbs: float,
    reps: int = 1,
    notes: str = "",
) -> Dict[str, Any]:
    """Record or update a Personal Record (PR) for an exercise in Firestore.

    Args:
        exercise_name: Name of the exercise (e.g. 'Barbell Bench Press').
        weight_lbs: Weight achieved in pounds (lbs).
        reps: Repetitions performed (defaults to 1 for 1RM).
        notes: Optional notes on the lift (e.g. 'Paused rep, felt strong').

    Returns:
        Confirmation dictionary containing the stored PR record.
    """
    db = get_db()
    slug_id = _slugify(f"{exercise_name}-pr")
    today = datetime.date.today().isoformat()
    data = {
        "id": slug_id,
        "exercise_name": exercise_name.strip(),
        "weight_lbs": float(weight_lbs),
        "reps": int(reps),
        "date": today,
        "notes": notes.strip(),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    db.collection("personal_records").document(slug_id).set(data)
    return {"status": "success", "message": f"Recorded PR for {exercise_name}: {weight_lbs} lbs x {reps} rep(s).", "pr": data}


def get_personal_records(exercise_name: str = "") -> List[Dict[str, Any]]:
    """Retrieve personal records (PRs) from Firestore.

    Args:
        exercise_name: Optional exercise name to filter PRs. If omitted, returns all PRs.

    Returns:
        A list of personal record dictionaries.
    """
    db = get_db()
    docs = db.collection("personal_records").stream()
    prs = []
    target = exercise_name.strip().lower()

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if not target or target in str(data.get("exercise_name", "")).lower():
            prs.append(data)

    return prs


# WRITE: Cross-session Memory Bank callback
async def generate_memories_callback(callback_context: CallbackContext):
    """Saves session highlights, user preferences, and PR milestones into Memory Bank."""
    await callback_context.add_session_to_memory()
    return None


# Agent Platform isolated Code Execution Sandbox
code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE
)

# A2UI Schema Manager for v0.8 Rich Card & Table Generation
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description="LiftMetrics, an expert workout coach, biomechanics specialist, and personal record (PR) tracker.",
    workflow_description=(
        "Analyze the user's fitness request and return structured UI when appropriate. "
        "Help users calculate their 1-rep max, log workouts and PRs, search exercises, "
        "generate visual form diagrams, fetch nutrition facts, and build progressive training plans."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are LiftMetrics, an expert fitness coach and personal record (PR) specialist.\n"
        "You have tools connected to a Firestore database, math calculator, external fitness APIs, and image generator:\n"
        "- `search_exercises`: Search and recommend exercises from the Firestore catalog.\n"
        "- `get_exercise_details`: Fetch technical execution cues and specifications.\n"
        "- `add_exercise`: Add new exercises to the Firestore catalog.\n"
        "- `calculate_one_rep_max`: Accurately compute estimated 1-Rep Max and working percentage targets (Epley/Brzycki).\n"
        "- `log_workout_session`: Log workouts with sets, reps, and weight; calculates total volume load; automatically checks and updates PRs.\n"
        "- `generate_exercise_form_image`: Generate visual form guide diagrams saved to public Cloud Storage.\n"
        "- `generate_exercise_motion_video`: Generate short exercise motion coaching video clips using Google's Omni model (gemini-omni-flash-preview) saved to public Cloud Storage and session artifacts.\n"
        "- `get_personal_records`: View user personal records.\n"
        "- `record_personal_record`: Explicitly store PRs.\n"
        "- `fetch_nutrition_facts`: Fetch live macronutrient data (protein, carbs, fat, calories) from Open Food Facts.\n"
        "- `lookup_external_muscle_info`: Fetch anatomical muscle details and diagrams from WGER Workout Manager.\n"
        "- Python Code Sandbox: You can run Python in an isolated sandbox to perform volume calculations, progression equations, or statistical analysis.\n"
        "- Memory Bank: Durable facts and preferences (injuries, training goals, preferred equipment) are remembered across sessions.\n\n"
        f"{a2ui_instruction}"
    ),
    tools=[
        PreloadMemoryTool(),
        search_exercises,
        get_exercise_details,
        add_exercise,
        calculate_one_rep_max,
        log_workout_session,
        generate_exercise_form_image,
        generate_exercise_motion_video,
        get_personal_records,
        record_personal_record,
        fetch_nutrition_facts,
        lookup_external_muscle_info,
    ],
    code_executor=code_executor,
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
