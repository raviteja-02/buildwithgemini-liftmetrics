# 🏋️‍♂️ LiftMetrics - AI Workout & PR Coach

![LiftMetrics Demo](liftmetrics_demo.gif)

LiftMetrics is an autonomous, agentic strength and conditioning coach built with the Google Agent Development Kit (ADK), Gemini 3 (`gemini-3.8-flash`), and Google Cloud Agent Platform. It designs periodized strength routines, logs training sessions to Firestore, automatically tracks and celebrates personal records (PRs), computes 1-Rep Max (1RM) percentage targets, queries nutritional macronutrients, generates anatomical form diagrams with Gemini Image models, creates short coaching motion clips with Google Omni, and renders visual training cards using A2UI.

---

## 🌟 Capabilities & Wired Google Cloud Services

Based strictly on the codebase in `app/` and configuration in `agents-cli-manifest.yaml`:

### 1. 🗄️ Google Cloud Firestore Backend
- **Project**: Dedicated Google Cloud project (`qwiklabs-gcp-03-fde3effbf431`).
- **Collections**:
  - `exercises`: Catalog of compound and accessory movements with technical instructions, biomechanical cues, difficulty, and targeted muscle groups.
  - `workout_sessions`: Historical session logs with sets, reps, weight (lbs), total volume load, and notes.
  - `personal_records`: All-time PR records per lift with timestamps and previous bests.
- **Wired Function Tools**:
  - `list_all_exercises(category)`: Lists all 18 curated movements categorized by muscle group (**Arms**, **Chest**, **Back**, **Shoulders**, **Legs**, **Core**) with equipment, difficulty, and rep targets.
  - `search_exercises(query, category)`: Fuzzy and multi-token keyword search across exercise names, aliases, target muscles, and equipment.
  - `get_exercise_details(exercise_name)`: Returns complete biomechanical execution guides, body posture/alignment, concentric/eccentric movement phases, set/rep targets (Hypertrophy 8-12 reps, Strength 6-8 reps, Endurance 12-15 reps), form cues, and common mistakes to avoid (e.g. for **Dumbbell Bicep Curls**, Barbell Squat, RDL, Bench Press).
  - `add_exercise(name, category, primary_muscle, equipment, difficulty, default_sets_reps, form_cues)`: Adds custom movements to the database.
  - `get_personal_records(exercise_name)`: Fetches current PR leaderboard and milestones.
  - `record_personal_record(exercise_name, weight_lbs, reps, notes)`: Stores explicit personal records.
  - `log_workout_session(exercise_name, sets, reps, weight_lbs, notes)`: Atomically computes total volume load, logs the workout session, checks against current PRs, and updates `personal_records` when a new record is achieved.

### 2. 🧮 Strength & Conditioning Math & Dual-Unit System
- **Wired Function Tools**:
  - `calculate_one_rep_max(weight, reps, unit)`: Primary metric system defaults to Kilograms (`kg`) with imperial (`lbs`) backward compatibility. Computes estimated 1RM using consensus averaging between Epley (`w * (1 + r / 30)`) and Brzycki (`w * 36 / (37 - r)`) equations, derives percentage training zones (95% down to 65%), and estimates rep maximums (3RM, 5RM, 8RM, 10RM).
  - `calculate_plate_breakdown(target_weight, bar_weight, unit)`: Olympic barbell sleeve math for metric `[25, 20, 15, 10, 5, 2.5, 1.25] kg` plates or imperial `[45, 35, 25, 10, 5, 2.5] lb` plates. Generates exact per-sleeve loads, collar requirements, and ASCII barbell diagrams.
  - `calculate_lifter_rank_and_stats(bodyweight, deadlift, squat, bench, overhead_press, unit)`: Gamified RPG strength progression featuring 7 rank tiers (Iron Novice, Bronze Lifter, Silver Athlete, Gold Warrior, Platinum Beast, Diamond Titan, Desi Baahubali / Iron God), DOTS strength ratio, XP progress, and unlocked gym badges (*Century Squatter*, *2x BW Deadlift Club*, *Bench Maharaja*, *Desi Strength Pioneer*).

### 3. 🍛 Indian & Global Budget Nutrition Engine (`app/diet_service.py`)
- **Wired Function Tool**:
  - `generate_budget_diet_plan(goal, daily_budget_inr, diet_type, bodyweight_kg, target_calories, currency)`
- **Core Architecture & Coverage**:
  - **5 Training Goals**: Strength & Powerlifting, Body Recomposition, Clean Hypertrophy Bulking, Fat Loss / Cutting, and High-Carb Endurance.
  - **4 Dietary Lifestyles**: Pure Vegetarian (no meat, no eggs; paneer, soya chunks, sattu, curd, dal), Eggetarian (vegetarian + eggs), Non-Vegetarian (chicken breast, fish, eggs, dairy), and Vegan (100% plant-based).
  - **3 Budget Tiers in INR & USD**:
    - *Hostel / Student Budget*: ₹100–₹150 / day (~$1.20–$1.80) — High-ROI protein staples.
    - *Working Professional*: ₹160–₹350 / day (~$1.90–$4.10) — Balanced whole foods and clean dairy.
    - *Elite / Premium Athlete*: ₹360+ / day (~$4.20+) — Whey isolate, salmon/chicken, and premium nuts.
  - **Protein Cost-Efficiency Rankings**: Automatically calculates cost-per-gram-of-protein to maximize nutrition per rupee spent (e.g., Soya Chunks @ ₹0.29/g protein vs. Chana Sattu @ ₹0.40/g protein vs. Eggs @ ₹1.16/g protein).
  - **Mandatory Interview Protocol**: The agent proactively prompts users for their daily budget and dietary preferences before generating personalized meal plans.

### 4. 🎨 Multimodal Media Generation & Google Cloud Storage
- **Public Storage Bucket**: `gs://liftmetrics-media-fde3effbf431` configured with public object viewing permissions.
- **Image Generation**:
  - **Model**: `gemini-3.1-flash-lite-image` in `global` region.
  - **Tool**: `generate_exercise_form_image(exercise_name, focus_cue)` generates anatomical diagrams illustrating form cues, saves the file to the ADK session artifacts, and uploads to Cloud Storage for persistent public access.
- **Omni Video Motion Generation**:
  - **Model**: `gemini-omni-flash-preview` in `global` region via the Vertex AI Interactions API.
  - **Tool**: `generate_exercise_motion_video(exercise_name, focus_cue)` renders a short coaching video clip demonstrating movement cadence, bar path, and joint angles, saves the MP4 into ADK session artifacts, and uploads to Cloud Storage.

### 5. 📈 Visual Progression Charts & Volume Analytics
- **Tool**: `generate_progress_chart(exercise_name, metric)`
- Dynamically renders high-resolution dark-themed progression charts combining:
  - Dual-axis visualizations: estimated 1RM progression lines and volume load bar distributions over historical workout logs.
  - Generates PNG charts with Matplotlib, saves to ADK session artifacts, and uploads to public Google Cloud Storage (`gs://liftmetrics-media-fde3effbf431/charts/`).

### 6. 🔬 Evidence-Based Sports Science Knowledge Grounding
- **Tool**: `consult_training_science(query)`
- Grounds workout recommendations, fatigue management, and periodization into peer-reviewed sports science:
  - Hypertrophy volume landmarks: Maintenance Volume (MV), Minimum Effective Volume (MEV), Maximum Adaptive Volume (MAV), and Maximum Recoverable Volume (MRV).
  - Scientific rest interval guidelines: 2–3+ minutes for heavy compound lifts (Squat, Bench, Deadlift) and 60–90 seconds for metabolic isolation movements.
  - Proactive RPE (Rate of Perceived Exertion) and RIR (Reps in Reserve) intensity scaling.

### 7. 🃏 Rich A2UI Interface & Addictive Web Frontend
- Configured with A2UI v0.8 Basic Catalog schema manager (`a2ui.basic_catalog.provider.BasicCatalog`, `a2ui.schema.manager.A2uiSchemaManager`) and `after_model_callback=a2ui_callback`.
- Converts agent responses into interactive visual components: Cards, Badges, Tables, Rows, Columns, and embedded images.
- **Gamified & Addictive UI Controls**:
  - **Interactive Barbell Plate Calculator Modal**: Visual sleeve loading calculator with live Olympic plate diagrams and direct coach query shortcut.
  - **Dual-Unit Metric Switcher (`[🇮🇳 KG / 🇺🇸 LBS]`)**: Instant one-click toggle adapting all calculator defaults, plate sets, and prompt chips.
  - **Streak & Rank Header Badges**: Visual display of active consistency streak and lifter RPG status (`🔥 14-Day Streak | 👑 Diamond Lifter`).
  - **PR Fanfare & Confetti Triggers**: Real-time canvas confetti explosions and synthesized Web Audio brass victory chords whenever a personal record or Baahubali milestone is logged.
  - **In-Header Rest Interval Timer**: Web Audio API countdown timer with 60s, 90s, and 3-minute presets, pause/resume, and audio beep alerts.
  - **Workout Log Exporter**: One-click download of the complete training session history as a Markdown file.

### 8. 🧠 Cross-Session Long-Term Memory (Memory Bank)
- Configured with `PreloadMemoryTool()` in `root_agent.tools` and `after_agent_callback=generate_memories_callback`.
- Connects to Vertex AI Agent Engine Memory Bank to retain user preferences, injury history, and training goals across separate user sessions.

### 9. 🐍 Sandboxed Code Execution
- Integrated `AgentEngineSandboxCodeExecutor` backed by Vertex AI Agent Engine.
- Safely executes Python code in an isolated cloud sandbox for complex volume equations, progression periodization, or custom analytics.

### 10. 🌐 External Nutrition & Anatomy APIs
- **Wired Function Tools**:
  - `fetch_nutrition_facts(food_query)`: Queries the Open Food Facts API (with USDA reference fallback) to fetch calories, protein, carbohydrates, and fats per 100g.
  - `lookup_external_muscle_info(muscle_name)`: Queries the WGER Workout Manager REST API for scientific anatomical muscle details and primary/secondary target groups.

---

## 📋 Planned, Not Yet Implemented

The following features from the initial concept brief are planned for future releases:
- **Wearable Device Sync**: Direct integration with Apple HealthKit, Garmin Connect, and WHOOP APIs for automated heart rate and recovery imports.
- **Computer-Vision Joint Angle Analysis**: Real-time webcam video pose estimation for live barbell velocity and joint flexion feedback.

---

## 🏗️ Repository Structure

```
liftmetrics/
├── app/
│   ├── agent.py               # Root ADK agent, system instructions, and tool bindings
│   ├── diet_service.py        # Indian & global budget nutrition engine and cost-per-gram protein rankings
│   ├── workout_service.py     # 1RM math, plate calculator, lifter RPG ranks, Firestore logging, and Matplotlib charts
│   ├── media_service.py       # Gemini 3.1 image generation and Omni video generation
│   ├── external_service.py    # Open Food Facts and WGER external API clients
│   ├── a2ui_utils.py          # A2UI response formatting callback and schema helpers
│   ├── seed_exercises.py      # Comprehensive 18-exercise database seed script (posture, execution, reps)
│   └── seed_firestore.py      # Firestore database seeding script
├── frontend/
│   ├── Dockerfile             # Container definition for Cloud Run deployment
│   ├── main.py                # FastAPI proxy communicating over the A2A protocol
│   ├── requirements.txt       # Frontend dependencies (a2a-sdk, fastapi, uvicorn)
│   └── static/
│       └── index.html         # Web chat UI, plate modal, unit switcher, confetti/fanfare, timer, and A2UI renderer
├── tests/
│   ├── unit/                  # Unit test suite (20 tests for diet, workout math, exercise catalog, media, charts)
│   │   ├── test_diet_service.py # Tests for budget diet plans, USD conversion, and protein cost rankings
│   │   ├── test_liftmetrics.py  # Tests for 1RM, plate math, RPG ranks, exercise catalog, bicep curl form & reps
│   │   ├── test_media_service.py# Tests for Gemini image generation and Cloud Storage upload
│   │   └── test_external_service.py # Tests for Open Food Facts & WGER APIs
│   └── eval/                  # Agent evaluation suite (datasets, LLM judge, eval configs)
│       ├── datasets/          # 8 domain-specific eval cases (1RM, logging, form guides, volume, budget diet, plate math, RPG rank, bicep curls)
│       ├── eval_config.yaml   # Configured metrics (MULTI_TURN_TASK_SUCCESS, turn count)
│       └── response_quality.py # In-process judge metric evaluator
├── training_science_guide.txt # Evidence-based strength and hypertrophy science knowledge base
├── liftmetrics_demo.gif       # Optimized looping screen recording of the agent in action
├── liftmetrics_demo.webm      # Full WebM demo recording
├── pyproject.toml             # Python package configuration and dependencies
└── agents-cli-manifest.yaml   # Agent manifest configuration
```

---

## 🚀 Local Setup & Execution Instructions

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Authenticated Google Cloud credentials:
  ```bash
  gcloud auth application-default login
  ```

### 1. Test Locally via CLI
Query the agent directly from the command line:
```bash
# Calculate 1-Rep Max and training targets
agents-cli run "Calculate my 1RM for Bench Press: 225 lbs for 5 reps, and show my working percentages"

# Log a session to Firestore
agents-cli run "Log a workout session: Deadlift 3 sets of 5 reps at 405 lbs"

# Request a visual form guide
agents-cli run "Show me proper form for Romanian Deadlift with a visual guide"

# Generate a visual progression chart
agents-cli run "Plot my progress chart for Deadlift"
```

### 2. Launch the Local Development Playground
Launch the ADK Playground dev UI with interactive chat, memory inspection, and artifact previews:
```bash
agents-cli playground
```
The playground server starts locally and can be accessed through your browser dev server port.

### 3. Run the Custom Web Frontend
Run the FastAPI A2A proxy server and chat frontend:
```bash
cd frontend
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
```

### 4. Deploy Frontend to Google Cloud Run
Deploy the frontend container directly to Google Cloud Run using Cloud Build:
```bash
gcloud run deploy liftmetrics-frontend \
  --source frontend \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/282829779330/locations/us-east1/reasoningEngines/4494360431162294272",AGENT_DIRECTORY="app"
```

---

## 🧪 Running Automated Unit Tests & Evaluation Suite

### 1. Automated Unit Tests
Run the pytest test suite:
```bash
uv run pytest tests/unit
```

### 2. Agent Evaluation Suite (`agents-cli eval`)
Run the evaluation benchmark across domain-specific test cases (1RM calculations, workout logging, form guides, and training science):
```bash
agents-cli eval run --dataset tests/eval/datasets/liftmetrics-eval.json --config tests/eval/eval_config.yaml
```
Traces and detailed scoring reports will be saved to `artifacts/traces/` and `artifacts/grade_results/`.

