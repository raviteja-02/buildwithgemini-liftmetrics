# 🏋️‍♂️ LiftMetrics AI — Autonomous Agentic Strength & Conditioning Coach

![LiftMetrics Demo](liftmetrics_demo.gif)

**LiftMetrics AI** is an autonomous, multimodal strength and conditioning agent built with the **Google Agent Development Kit (ADK)**, **Gemini 3**, **FastAPI**, and **Google Cloud Firestore**. It designs periodized strength routines, logs training sessions, automatically tracks and celebrates personal records (PRs), computes 1-Rep Max (1RM) percentage targets, calculates cost-per-gram protein nutrition plans, generates anatomical form diagrams and motion coaching clips, and renders interactive A2UI training cards.

---

## ✨ Key Capabilities

- **Autonomous Tool-Calling Coaching Engine:** Periodized strength programming, RPE/RIR autoregulation, and evidence-based hypertrophy volume landmarks (MV, MEV, MAV, MRV).
- **Strength Math & Dual-Unit Engine (`KG` / `LBS`):**
  - Consensus 1-Rep Max (1RM) calculator averaging Epley and Brzycki equations with percentage training zones (65%–95%).
  - Olympic Barbell Plate Calculator with visual per-sleeve plate breakdowns.
  - Gamified Lifter Progression & DOTS strength ratio scoring across 7 rank tiers.
- **Persistent Cloud Firestore Telemetry:** Tracks exercise catalogs, historical workout session volume loads, and automatic all-time Personal Record (PR) detection.
- **Budget & Macro Nutrition Engine:** Calculates daily macro targets and optimizes meal plans by protein cost-efficiency across Vegetarian, Eggetarian, Non-Vegetarian, and Vegan diets (in both `INR` and `USD`).
- **Multimodal Form & Progress Visualization:**
  - Generates anatomical exercise form guides and short coaching motion clips via Gemini multimodal models.
  - Renders dual-axis 1RM and volume progression charts stored in Google Cloud Storage.
- **Interactive A2UI Web Frontend:** Built with FastAPI and the Agent-to-Agent (A2A) protocol, featuring live plate calculator modals, rest interval timers, PR celebration effects, and Markdown session export.

---

## 🛠️ Technology Stack

- **AI & Agent Framework:** Google Agent Development Kit (ADK), Gemini 3 (`gemini-3.8-flash`), Vertex AI Agent Engine Memory Bank, A2UI v0.8
- **Backend & API:** Python 3.11+, FastAPI, Uvicorn, Agent-to-Agent (A2A) Protocol
- **Database & Cloud:** Google Cloud Firestore, Google Cloud Storage, Google Cloud Run
- **External Integrations:** Open Food Facts API, USDA Nutrition Fallback, WGER Workout Manager REST API

---

## 🚀 Local Quick Start

### Prerequisites
- Python 3.11+ and [`uv`](https://docs.astral.sh/uv/)
- Google Cloud Application Default Credentials (`gcloud auth application-default login`)

### 1. Run via ADK Playground or CLI
```bash
# Interactive web playground
agents-cli playground

# Direct CLI query
agents-cli run "Calculate my 1RM for Bench Press: 100 kg for 5 reps and show working percentages"
```

### 2. Run the FastAPI Web Frontend
```bash
cd frontend
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
```

### 3. Run Automated Unit Tests
```bash
uv run pytest tests/unit
```

---

## 👤 Author

**Raviteja Thipparthi**  
- Portfolio: [traviteja-portfolio.vercel.app](https://traviteja-portfolio.vercel.app)  
- LinkedIn: [linkedin.com/in/raviteja-thipparthi](https://www.linkedin.com/in/raviteja-thipparthi)  
- Email: [raviteja@nexuscode.in](mailto:raviteja@nexuscode.in)
