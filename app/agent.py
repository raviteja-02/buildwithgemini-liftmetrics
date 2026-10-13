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
from app.seed_exercises import EXERCISE_CATALOG
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


def list_all_exercises(category: str = "") -> Dict[str, Any]:
    """List all exercises in the LiftMetrics database, grouped by muscle group / category.

    Args:
        category: Optional filter by category (e.g. 'Arms', 'Chest', 'Back', 'Shoulders', 'Legs', 'Core').

    Returns:
        A dictionary with categories containing lists of exercises, total count, and guidance.
    """
    db = get_db()
    items = []
    try:
        docs = db.collection("exercises").stream()
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            items.append(d)
    except Exception as e:
        logger.warning(f"Error fetching exercises from Firestore: {e}")

    # Fallback to local catalog if Firestore returned nothing
    if not items:
        items = list(EXERCISE_CATALOG)

    cat_filter = category.strip().lower()
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for item in items:
        item_cat = str(item.get("category", "Other")).strip()
        if cat_filter and cat_filter not in item_cat.lower():
            continue
        if item_cat not in grouped:
            grouped[item_cat] = []
        grouped[item_cat].append({
            "name": item.get("name"),
            "category": item_cat,
            "primary_muscle": item.get("primary_muscle"),
            "equipment": item.get("equipment"),
            "difficulty": item.get("difficulty", "Intermediate"),
            "default_sets_reps": item.get("default_sets_reps", "3 sets of 8-12 reps"),
            "form_cues": item.get("form_cues", ""),
        })

    total_count = sum(len(ex_list) for ex_list in grouped.values())
    return {
        "status": "success",
        "total_exercises": total_count,
        "categories": grouped,
        "note": "Call `get_exercise_details` with any exercise name for step-by-step body posture, movement biomechanics, rep ranges, and common mistakes.",
    }


def search_exercises(query: str = "", category: str = "") -> List[Dict[str, Any]]:
    """Search or list exercises in the catalog stored in Firestore.

    Args:
        query: Optional keyword to search within exercise name, primary muscle, equipment, or aliases.
        category: Optional category filter (e.g. 'Chest', 'Legs', 'Back', 'Shoulders', 'Arms', 'Core').

    Returns:
        A list of matching exercise dictionaries from Firestore.
    """
    db = get_db()
    items = []
    try:
        docs = db.collection("exercises").stream()
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            items.append(d)
    except Exception as e:
        logger.warning(f"Error searching exercises from Firestore: {e}")

    if not items:
        items = list(EXERCISE_CATALOG)

    results = []
    q_lower = query.strip().lower()
    cat_lower = category.strip().lower()

    stop_words = {"how", "to", "perform", "with", "the", "a", "an", "do", "execute", "proper", "form", "correct", "for"}
    query_tokens = set(
        re.sub(r"[^\w]", "", w.lower().rstrip("s"))
        for w in q_lower.split()
        if w.lower() not in stop_words and len(w) > 2
    )

    for data in items:
        # Category filter
        doc_category = str(data.get("category", "")).lower()
        if cat_lower and cat_lower not in doc_category:
            continue

        # Query keyword search
        if q_lower:
            name = str(data.get("name", "")).lower()
            muscle = str(data.get("primary_muscle", "")).lower()
            equip = str(data.get("equipment", "")).lower()
            aliases = [str(a).lower() for a in data.get("aliases", [])]
            alias_str = " ".join(aliases)

            # Direct substring match
            if q_lower in name or q_lower in muscle or q_lower in equip or q_lower in alias_str:
                results.append(data)
                continue

            # Token overlap check
            item_text = f"{name} {muscle} {equip} {alias_str}"
            item_tokens = set(
                re.sub(r"[^\w]", "", w.lower().rstrip("s"))
                for w in item_text.split()
                if len(w) > 2
            )
            if query_tokens and len(query_tokens & item_tokens) >= 1:
                results.append(data)
                continue
        else:
            results.append(data)

    return results


def get_exercise_details(exercise_name: str) -> Dict[str, Any]:
    """Get full biomechanical details, body posture, movement execution, and rep targets for an exercise.

    Args:
        exercise_name: Name or search query for the exercise (e.g. 'bicep curls with dumbells', 'Dumbbell Bicep Curl', 'Barbell Bench Press').

    Returns:
        The exercise record with body posture, movement execution phases, rep targets, and form cues.
    """
    db = get_db()
    slug_id = _slugify(exercise_name)

    all_items = []
    try:
        docs = db.collection("exercises").stream()
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            all_items.append(d)
    except Exception as e:
        logger.warning(f"Error fetching exercises: {e}")

    if not all_items:
        all_items = list(EXERCISE_CATALOG)

    target = exercise_name.strip().lower()

    # 1. Direct ID or slug lookup
    for item in all_items:
        if item.get("id") == slug_id or item.get("id") == target:
            return item

    # 2. Exact name or exact alias match
    for item in all_items:
        if str(item.get("name", "")).lower() == target:
            return item
        aliases = [str(a).lower() for a in item.get("aliases", [])]
        if target in aliases:
            return item

    # 3. Substring containment in name or aliases
    for item in all_items:
        name_lower = str(item.get("name", "")).lower()
        if target in name_lower or name_lower in target:
            return item
        for a in item.get("aliases", []):
            a_lower = str(a).lower()
            if target in a_lower or a_lower in target:
                return item

    # 4. Token overlap ranking (handles queries like 'how to perform bicep curls with dumbells')
    stop_words = {"how", "to", "perform", "with", "the", "a", "an", "do", "execute", "proper", "form", "correct", "for"}
    query_tokens = set(
        re.sub(r"[^\w]", "", w.lower().rstrip("s"))
        for w in exercise_name.split()
        if w.lower() not in stop_words and len(w) > 2
    )

    best_match = None
    best_score = 0
    for item in all_items:
        alias_str = " ".join(item.get("aliases", []))
        item_text = item.get("name", "") + " " + alias_str + " " + item.get("equipment", "")
        item_tokens = set(
            re.sub(r"[^\w]", "", w.lower().rstrip("s"))
            for w in item_text.split()
            if len(w) > 2
        )
        score = len(query_tokens & item_tokens)
        if score > best_score:
            best_score = score
            best_match = item

    if best_match and best_score >= 1:
        return best_match

    return {"error": f"Exercise '{exercise_name}' not found in the catalog. Call `list_all_exercises` to view all available exercises."}


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
        "EXERCISE CATALOG & MOVEMENT DIRECTORY PROTOCOL:\n"
        "- When a user asks to see or list exercises (e.g. 'list all exercises', 'show exercises', 'what exercises do you have', 'movement catalog'):\n"
        "  Invoke `list_all_exercises` to return the complete library grouped into Arms, Chest, Back, Shoulders, Legs, and Core with primary muscles and equipment.\n\n"
        "EXERCISE EXECUTION & BIOMECHANICAL FORM COACHING PROTOCOL:\n"
        "- When a user asks how to perform any exercise (such as 'how to perform bicep curls with dumbells' or 'dumbbell bicep curl'):\n"
        "  Always invoke `get_exercise_details` and provide a comprehensive, structured coaching breakdown covering:\n"
        "  1. Target Muscles: Primary muscle (e.g., Biceps Brachii - short & long heads) and secondary muscles (Brachialis, Brachioradialis, Forearms).\n"
        "  2. Body Posture & Setup: Feet shoulder-width apart, knees unlocked, tall chest, scapulae retracted & depressed (shoulders down and back), core/glutes braced to eliminate sway, elbows pinned against ribs.\n"
        "  3. Movement Execution: Step-by-step guide with concentric curl with active wrist supination (turning palms toward the ceiling), 1-second peak squeeze at apex, and strict 2-3 second eccentric lowering to full elbow lockout/stretch.\n"
        "  4. Sets & Repetitions Guidance: Rep ranges for Hypertrophy (3-4 sets of 8-12 reps, RIR 1-2), Strength/Mass (4 sets of 6-8 reps), and Muscular Endurance (3 sets of 12-15 reps).\n"
        "  5. Critical Form Cues & Mistakes to Avoid: Zero torso swinging/hip heave, no elbow flare or forward drift, full range of motion (no half reps), neutral wrists.\n"
        "  6. Visual Cue: Offer or invoke `generate_exercise_form_image` to generate a visual form guide diagram.\n\n"
        "ALL AVAILABLE TOOLS:\n"
        "- `list_all_exercises`: List all exercises in the catalog grouped by muscle group (Arms, Chest, Back, Shoulders, Legs, Core).\n"
        "- `get_exercise_details`: Fetch technical execution cues, body posture, biomechanics, and set/rep targets for any movement.\n"
        "- `search_exercises`: Search and recommend exercises from the Firestore catalog.\n"
        "- `add_exercise`: Add new exercises to the Firestore catalog.\n"
        "- `calculate_one_rep_max`: Accurately compute estimated 1RM and working percentages in both KG and LBS.\n"
        "- `calculate_plate_breakdown`: Compute exact sleeve plate loading on a 20kg bar (or 45lb bar) with ASCII diagram.\n"
        "- `calculate_lifter_rank_and_stats`: Compute RPG lifter level, XP, DOTS ratio, and achievement badges.\n"
        "- `generate_budget_diet_plan`: Generate macro-optimized, budget-friendly meal plans for all fitness goals.\n"
        "- `log_workout_session`: Log workouts with sets, reps, weight (kg/lbs); calculates volume load; checks and updates PRs.\n"
        "- `generate_progress_chart`: Plot visual dark-mode strength and volume progression graphs uploaded to Cloud Storage.\n"
        "- `consult_training_science`: Consult evidence-based exercise science guidelines (hypertrophy volume, rest intervals, RPE/RIR).\n"
        "- `generate_exercise_form_image`: Generate visual form guide diagrams saved to public Cloud Storage.\n"
        "- `generate_exercise_motion_video`: Generate coaching video clips using Google's Omni model saved to Cloud Storage and session artifacts.\n"
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
        list_all_exercises,
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
