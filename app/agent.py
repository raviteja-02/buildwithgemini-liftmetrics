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
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

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
from app.diet_service import generate_budget_diet_plan
from app.external_service import fetch_nutrition_facts, lookup_external_muscle_info
from app.media_service import generate_exercise_form_image, generate_exercise_motion_video
from app.workout_service import (
    calculate_lifter_rank_and_stats,
    calculate_one_rep_max,
    calculate_plate_breakdown,
    generate_progress_chart,
    log_workout_session,
)

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

def consult_training_science(query: str) -> str:
    """Consult evidence-based sports science guidelines for hypertrophy, volume landmarks, rest intervals, and fatigue management.

    Args:
        query: Specific exercise science question (e.g. 'optimal rest between heavy sets', 'hypertrophy volume landmarks', 'RPE vs RIR guidance').

    Returns:
        Evidence-based sports science guidelines and recommendations.
    """
    try:
        corpus_file = os.path.join(os.path.dirname(__file__), "..", "scripts", "corpus_resource.txt")
        if os.path.exists(corpus_file):
            with open(corpus_file, "r") as f:
                corpus_name = f.read().strip()
            if corpus_name:
                import vertexai
                from vertexai.preview import rag

                vertexai.init(project=PROJECT_ID, location="us-central1")
                resp = rag.retrieval_query(
                    rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
                    text=query,
                    similarity_top_k=3,
                )
                contexts = [ctx.text for ctx in resp.contexts.contexts if ctx.text]
                if contexts:
                    return "Scientific Knowledge Retrieval:\n" + "\n\n---\n\n".join(contexts)
    except Exception as e:
        logger.warning(f"RAG retrieval query error: {e}")

    # Grounded fallback: read from verified sports science reference guide
    guide_path = os.path.join(os.path.dirname(__file__), "..", "training_science_guide.txt")
    if os.path.exists(guide_path):
        with open(guide_path, "r") as f:
            content = f.read()
        return f"Evidence-Based Sports Science Guidelines:\n{content[:2500]}"
    return "Sports Science Reference: Optimal hypertrophy volume is 10-20 sets/muscle/week with 2-3 mins rest for compounds and 1-2 mins for isolations."


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are LiftMetrics, an over-engineered, highly addictive, autonomous AI Workout & Nutrition Coach engineered in India for gym-goers both in India and worldwide.\n\n"
        "METRIC CONVENTION & INDIAN SYSTEM DEFAULTS:\n"
        "- In accordance with Indian fitness standards (and international Olympic/IPF standards), your PRIMARY default metric is Kilograms (kg), standard 20kg Olympic barbells, and Indian Rupees (₹) for nutrition budgets, while always seamlessly providing dual conversions for global users (lbs and $).\n"
        "- Always express weight primarily in 'kg' (e.g. '100 kg (220.5 lbs)') unless the user explicitly asks in lbs.\n\n"
        "STRICT BUDGET-FIRST DIET & BALANCED NUTRITION PROTOCOL:\n"
        "- Balanced Nutrition Coverage: You cover all 5 fitness goals: (1) Strength / Powerlifting, (2) Body Recomposition, (3) Weight Gain / Bulking, (4) Weight Loss / Cutting, and (5) Athletic Endurance.\n"
        "- MANDATORY INTERVIEW: Whenever a user asks for a diet, meal plan, or nutrition guidance, you MUST check if they have provided their daily or monthly diet budget. If not provided, ASK them explicitly:\n"
        "  1. What is your daily food budget in INR (₹) or USD ($)? (e.g., ₹100/day student budget, ₹250/day standard, ₹500/day elite).\n"
        "  2. What is your dietary preference? (Pure Veg, Eggetarian, Non-Veg, Vegan).\n"
        "  3. What is your primary fitness goal? (Strength, Recomposition, Clean Bulking, Fat Loss Cutting, Endurance).\n"
        "- Once confirmed, invoke `generate_budget_diet_plan` to provide their optimized meal plan, cost-per-gram-of-protein, and budget hacks (featuring Indian staples like Soya chunks, Sattu, Paneer, Eggs, Chicken breast, Curd/Dahi, Dal).\n\n"
        "BARBELL PLATE MATH PROTOCOL:\n"
        "- When a lifter asks what plates to load on the bar for any target weight, invoke `calculate_plate_breakdown` to give them the exact sleeve breakdown and ASCII bar diagram.\n\n"
        "LIFTER RPG GAMIFICATION & CELEBRATION PROTOCOL:\n"
        "- When a lifter inquires about their strength level, rank, or badges, invoke `calculate_lifter_rank_and_stats` to compute their level (Iron Novice -> Bronze -> Silver -> Gold -> Platinum -> Diamond -> Desi Baahubali / Iron God).\n"
        "- Cheer on lifters with high-energy gym enthusiasm ('Shabash! Dangal mode on!').\n\n"
        "ALL AVAILABLE TOOLS:\n"
        "- `calculate_one_rep_max`: Accurately compute estimated 1RM and working percentages in both KG and LBS.\n"
        "- `calculate_plate_breakdown`: Compute exact sleeve plate loading on a 20kg bar (or 45lb bar) with ASCII diagram.\n"
        "- `calculate_lifter_rank_and_stats`: Compute RPG lifter level, XP, DOTS ratio, and achievement badges.\n"
        "- `generate_budget_diet_plan`: Generate macro-optimized, budget-friendly meal plans for all fitness goals.\n"
        "- `log_workout_session`: Log workouts with sets, reps, weight (kg/lbs); calculates volume load; checks and updates PRs.\n"
        "- `generate_progress_chart`: Plot visual dark-mode strength and volume progression graphs uploaded to Cloud Storage.\n"
        "- `consult_training_science`: Consult evidence-based exercise science guidelines (hypertrophy volume, rest intervals, RPE/RIR).\n"
        "- `generate_exercise_form_image`: Generate visual form guide diagrams saved to public Cloud Storage.\n"
        "- `generate_exercise_motion_video`: Generate coaching video clips using Google's Omni model saved to Cloud Storage and session artifacts.\n"
        "- `search_exercises`: Search and recommend exercises from the Firestore catalog.\n"
        "- `get_exercise_details`: Fetch technical execution cues and specifications.\n"
        "- `add_exercise`: Add new exercises to the Firestore catalog.\n"
        "- `get_personal_records`: View user personal records.\n"
        "- `record_personal_record`: Explicitly store PRs.\n"
        "- `fetch_nutrition_facts`: Fetch live macronutrient data from Open Food Facts.\n"
        "- `lookup_external_muscle_info`: Fetch anatomical muscle details from WGER Workout Manager.\n"
        "- Python Code Sandbox: Execute Python in an isolated sandbox for volume equations or analytics.\n"
        "- Memory Bank: Durable facts and preferences remembered across sessions.\n\n"
        f"{a2ui_instruction}"
    ),
    tools=[
        PreloadMemoryTool(),
        calculate_one_rep_max,
        calculate_plate_breakdown,
        calculate_lifter_rank_and_stats,
        generate_budget_diet_plan,
        log_workout_session,
        generate_progress_chart,
        consult_training_science,
        generate_exercise_form_image,
        generate_exercise_motion_video,
        search_exercises,
        get_exercise_details,
        add_exercise,
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
