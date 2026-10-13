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
  - `search_exercises(query, muscle_group, limit)`: Full-text and muscle-group search across the exercise database.
  - `get_exercise_details(exercise_name)`: Retrieves detailed cues, setup instructions, and equipment specifications.
  - `add_exercise(name, muscle_group, equipment, difficulty, instructions, cues)`: Adds custom movements to the database.
  - `get_personal_records(exercise_name)`: Fetches current PR leaderboard and milestones.
  - `record_personal_record(exercise_name, weight_lbs, reps, notes)`: Stores explicit personal records.
  - `log_workout_session(exercise_name, sets, reps, weight_lbs, notes)`: Atomically computes total volume load, logs the workout session, checks against current PRs, and updates `personal_records` when a new record is achieved.

### 2. 🧮 Strength & Conditioning Math
- **Wired Function Tool**:
  - `calculate_one_rep_max(weight_lbs, reps)`: Computes estimated 1-Rep Max using consensus averaging between Epley (`w * (1 + r / 30)`) and Brzycki (`w * 36 / (37 - r)`) equations, derives percentage training zones (95% down to 65%), and estimates rep maximums (3RM, 5RM, 8RM, 10RM).

### 3. 🎨 Multimodal Media Generation & Google Cloud Storage
- **Public Storage Bucket**: `gs://liftmetrics-media-fde3effbf431` configured with public object viewing permissions.
- **Image Generation**:
  - **Model**: `gemini-3.1-flash-lite-image` in `global` region.
  - **Tool**: `generate_exercise_form_image(exercise_name, focus_cue)` generates anatomical diagrams illustrating form cues, saves the file to the ADK session artifacts, and uploads to Cloud Storage for persistent public access.
- **Omni Video Motion Generation**:
  - **Model**: `gemini-omni-flash-preview` in `global` region via the Vertex AI Interactions API.
  - **Tool**: `generate_exercise_motion_video(exercise_name, focus_cue)` renders a short coaching video clip demonstrating movement cadence, bar path, and joint angles, saves the MP4 into ADK session artifacts, and uploads to Cloud Storage.

### 4. 🃏 Rich A2UI Interface
- Configured with A2UI v0.8 Basic Catalog schema manager (`a2ui.basic_catalog.provider.BasicCatalog`, `a2ui.schema.manager.A2uiSchemaManager`) and `after_model_callback=a2ui_callback`.
- Converts agent responses into interactive visual components:
  - **Cards & Badges**: Cleanly formatted training plans and exercise summaries.
  - **Rows & Columns**: Structured percentage tables and set/rep workout splits.
  - **Images**: Embedded visual diagrams directly rendered inside cards.

### 5. 🧠 Cross-Session Long-Term Memory (Memory Bank)
- Configured with `PreloadMemoryTool()` in `root_agent.tools` and `after_agent_callback=generate_memories_callback`.
- Connects to Vertex AI Agent Engine Memory Bank to retain user preferences, injury history, and training goals across separate user sessions.

### 6. 🐍 Sandboxed Code Execution
- Integrated `AgentEngineSandboxCodeExecutor` backed by Vertex AI Agent Engine.
- Safely executes Python code in an isolated cloud sandbox for complex volume equations, progression periodization, or custom analytics.

### 7. 🌐 External Nutrition & Anatomy APIs
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
│   ├── workout_service.py     # 1RM math calculations and Firestore logging logic
│   ├── media_service.py       # Gemini 3.1 image generation and Omni video generation
│   ├── external_service.py    # Open Food Facts and WGER external API clients
│   ├── a2ui_utils.py          # A2UI response formatting callback and schema helpers
│   └── seed_firestore.py      # Firestore database seeding script
├── frontend/
│   ├── main.py                # FastAPI proxy communicating over the A2A protocol
│   ├── requirements.txt       # Frontend dependencies (a2a-sdk, fastapi, uvicorn)
│   └── static/
│       └── index.html         # Web chat interface with A2UI card renderer
├── tests/
│   └── unit/                  # Unit test suite for workout math and media services
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

---

## 🧪 Running Automated Unit Tests

Run the test suite using pytest:
```bash
uv run pytest tests/unit
```
