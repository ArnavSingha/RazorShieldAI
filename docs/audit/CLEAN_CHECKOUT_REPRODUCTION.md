# RAZORSHIELD AI — CLEAN CHECKOUT REPRODUCTION GUIDE

**Target:** Independent Hackathon Judge / Technical Auditor  
**Estimated Setup Time:** Under 3 minutes from clean clone  
**Operating Systems Supported:** Windows (PowerShell), macOS / Linux (Bash)

---

## 1. Prerequisites
- **Python:** 3.11 or higher
- **Node.js:** v18.0.0 or higher (`npm` v9+)
- **Git:** Standard git client
- *(Optional)* **Gemini API Key:** For live Gemini 3.6 Flash reasoning (the application includes full `DeterministicFallbackLLMProvider` if key is absent).

---

## 2. Step-by-Step Reproduction Instructions

### Step 1: Clone Repository
```bash
git clone https://github.com/your-org/RazorShield-AI.git
cd "RazorShield AI"
```

### Step 2: Set Up Python Backend Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 3: Set Up Environment Variables
Create a local `.env` file in the project root:
```env
APP_ENV=development
SECRET_KEY=razorshield_super_secure_secret_key_2026_dev_mode
AUDIT_HMAC_SECRET=razorshield_audit_merkle_secret_key_2026
GEMINI_API_KEY=your_gemini_api_key_here  # Optional: triggers deterministic fallback if omitted
GEMINI_MODEL=gemini-3.6-flash
DATABASE_URL=sqlite:///./razorshield_local.db
LOG_LEVEL=INFO
```

### Step 4: Run the Held-Out Benchmark with 1 Command
```bash
python scripts/run_evaluation.py
```
**Expected Output:**
```text
========================================================================================
RAZORSHIELD AI — TRACK 02 HELD-OUT EVALUATION COMPLETE
========================================================================================
- Dataset: data/evaluation/test.jsonl (500 records: 77 fraud, 423 benign)
- RULES_ONLY     : Precision=21.36%, Recall=81.82%, F1=33.88%, FPR=54.85%
- ML_ONLY        : Precision=44.83%, Recall=50.65%, F1=47.56%, FPR=11.35%
- RULES_PLUS_ML  : Precision=15.27%, Recall=89.61%, F1=26.09%, FPR=90.54%
- RULES_ML_GRAPH : Precision=15.51%, Recall=87.01%, F1=26.33%, FPR=86.29%
========================================================================================
Metrics saved to: docs/evaluation/HELDOUT_EVALUATION.md and data/evaluation/results/metrics.json
```

### Step 5: Run Automated Test Suite (96 Tests)
```bash
pytest backend/tests -v
```
**Expected Result:** `96 passed, 1 skipped, 0 failed` in $< 30$ seconds.

### Step 6: Start Full Local Application

**Terminal 1 (Backend API):**
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
*Health Check:* Open `http://127.0.0.1:8000/api/health` $\rightarrow$ `{"status": "healthy"}`

**Terminal 2 (Frontend Command Center):**
```bash
npm install
npm run dev
```
*UI Access:* Open `http://localhost:3000` in browser.

---

## 3. Dependency & Environment Audit

| Component | Dependency Type | Fallback Mode |
| :--- | :--- | :--- |
| **Gemini 3.6 Flash** | Cloud API (Google Generative AI) | Automatic `DeterministicFallbackLLMProvider` generates structured briefs offline |
| **Database** | SQLite (`razorshield_local.db`) | Automatic schema creation on first startup |
| **Graph Storage** | In-memory heterogeneous graph | Dynamic graph accumulation during runtime |
| **ML Engine** | `scikit-learn` IsolationForest | Trains and persists automatically on startup |
