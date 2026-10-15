# Kestrel Home — Intelligent Service-Request Routing System (Variant B)

An end-to-end, privacy-preserving machine learning service designed to replace Kestrel Home Appliances' ₹3.2 lakh/year third-party vendor service-routing bot. The system automatically classifies inbound customer service requests into seven active operational queues with **95.04% holdout accuracy**, incorporates calibrated confidence scores, detects Policy §3 billing edge cases, and provides human-readable explanations.

---

## 1. Project Overview & Business Value

- **The Problem:** Kestrel's external routing bot costs ₹3.2 lakh annually (~₹26,667/month). Historical resolution logs reveal that the bot misrouted **22.83% of inbound tickets**, causing **3,902 inter-team transfers** that cost Kestrel **₹15.13 lakh annually** in direct handling time and repeat contacts (Operations Policy v4.1, §4).
- **The Solution:** A locally hosted, calibrated linear classifier combining word-level TF-IDF and structured intake features. The system runs 100% on CPU with zero variable token fees, zero external API calls, and sub-10ms latency.
- **Key Results:**
  - **95.04% Holdout Accuracy** on out-of-time requests (beating the 90.0% stakeholder threshold).
  - **0.9485 Macro F1-Score** across all seven queues.
  - **Guaranteed Annual Net Savings:** ₹2.60 lakh/year in eliminated license fees.
  - **Potential Transfer Savings:** ₹4.50 to ₹7.50 lakh/year in reduced desk transfers.

---

## 2. System Architecture & Project Structure

```text
kestrel-routing/
├── README.md                      # Comprehensive deployment & replication guide
├── requirements.txt               # Locked production dependencies
├── predictions.csv                # Official predictions for test_unlabelled.csv (2,178 rows)
├── memo.md                        # One-page executive decision memo to Ritu Deshpande
├── submission_form.md             # Completed submission form & AI-tool disclosure
├── data/
│   └── raw/                       # Pristine assignment files (train, test, policy, teams)
├── src/
│   ├── __init__.py                # Package root
│   ├── data.py                    # Data loaders, text cleaners, alias mapping, splits
│   ├── train.py                   # Model pipeline training & joblib export
│   ├── predict.py                 # Predictor engine, feature attribution, policy checks
│   ├── api.py                     # FastAPI REST service (/health, /predict)
│   └── ui.py                      # Streamlit interactive service desk console
├── models/
│   ├── kestrel_routing_model.joblib # Serialized production pipeline (3.1 MB)
│   └── model_metadata.json        # Artifact metadata, metrics & versioning
├── tests/
│   ├── test_data.py               # Data loading, cleaning, Mojibake & schema tests
│   ├── test_model.py              # Prediction outputs, calibration & edge cases
│   ├── test_api.py                # FastAPI endpoint integration tests
│   └── test_submission.py         # predictions.csv contract verification
├── scripts/
│   ├── inspect_data.py            # Exploratory data audit & transfer cost calculator
│   ├── generate_predictions.py    # Generates root-level predictions.csv
│   └── validate_submission.py     # Schema, row count, sequence, and label validator
├── docs/
│   ├── assignment_inventory.md    # Complete dataset audit & stakeholder context
│   ├── data_dictionary.md         # Schema, column dtypes & leakage rules
│   ├── assumptions_and_decisions.md # Technical decisions & modeling rationale
│   └── demo_script.md             # 3-minute video recording walkthrough script
├── evidence/
│   ├── metrics.json               # Comprehensive evaluation metrics breakdown
│   ├── model_comparison.csv       # Baseline vs combined model comparison
│   ├── classification_report.txt  # Per-class precision, recall, and F1 table
│   ├── failure_cases.csv          # Audited validation misclassifications
│   └── confusion_matrix.png       # Confusion matrix visualization
└── .gitignore                     # Git configuration
```

---

## 3. Environment Setup & Prerequisites

- **Python Version:** Python 3.10+ (tested on Python 3.10.0 Windows and Linux).
- **Hardware Requirements:** Any standard 2-core CPU with 4GB RAM. No GPU required.
- **External APIs:** **None.** No paid API keys or hosted model credentials are used.

### Setup Instructions

#### Windows (PowerShell):
```powershell
# Clone or navigate to the repository
cd "C:\Users\MOHIT KUMAR\Desktop\kestrel-routing"

# Optional: Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

#### macOS / Linux (Bash):
```bash
# Clone or navigate to the repository
cd /path/to/kestrel-routing

# Optional: Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 4. Execution Commands

Every command is tested, fully functional, and runnable directly from the repository root:

### 4.1 Inspect Data & Historical Routing Costs
```bash
python scripts/inspect_data.py
```
*Computes historical dataset shapes, transfer rates, desk disagreement, and annualized routing waste.*

### 4.2 Train & Evaluate Model
```bash
python src/train.py
```
*Trains on historical requests, evaluates temporal holdout, and serializes `models/kestrel_routing_model.joblib`.*

### 4.3 Generate Production Predictions
```bash
python scripts/generate_predictions.py
```
*Applies production model to `test_unlabelled.csv` and outputs `predictions.csv` at the repository root.*

### 4.4 Validate Submission File Contract
```bash
python scripts/validate_submission.py
```
*Verifies row counts (2,178), schema `['request_id', 'team']`, ID sequences, zero nulls, and canonical labels.*

### 4.5 Run Complete Test Suite
```bash
python -m pytest -v
```
*Runs all 22 automated tests covering data loading, Mojibake cleaning, alias mapping, model inference, API endpoints, and submission verification.*

---

## 5. Running the Local Service & User Interface

### 5.1 Launch the FastAPI Routing Service
Start the REST API on `http://127.0.0.1:8000`:
```bash
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```
Interactive OpenAPI documentation will be available at `http://127.0.0.1:8000/docs`.

### 5.2 Launch the Streamlit Desk Console
In a separate terminal, launch the agent web application:
```bash
streamlit run src/ui.py
```
Open `http://localhost:8501` in your browser. The UI allows agents to test real customer messages, select presets, view assigned queues, observe calibrated confidence, and read Policy §3 explanation notes.

---

## 6. API Specification & Synthetic Examples

### Health Check: `GET /health`
```bash
curl -X GET "http://127.0.0.1:8000/health"
```
**Response (200 OK):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0",
  "available_classes": [
    "Billing",
    "Filters & Consumables",
    "Installs & Demo",
    "Product Advice",
    "Repairs",
    "Returns & Replacement",
    "Warranty Claims"
  ]
}
```

### Route Service Request: `POST /predict`
#### Example 1: Physical Repair Query (Synthetic Data)
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "request_id": "SR510823",
       "channel": "chat",
       "product_family": "Water Purifier",
       "warranty_status": "in_warranty",
       "request_text": "water purifier leaking water from bottom, please send technician"
     }'
```
**Response (200 OK):**
```json
{
  "request_id": "SR510823",
  "predicted_team": "Filters & Consumables",
  "confidence": 0.8336,
  "reasons": [
    "Model signals: Customer metadata: product family Water Purifier; Matching text phrase 'purifier leaking'; Matching text phrase 'water'."
  ],
  "review_recommended": false,
  "runner_up_team": "Repairs",
  "runner_up_confidence": 0.1619
}
```

#### Example 2: Payment for Installation (Policy §3 Edge Case)
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "request_id": "SR510824",
       "channel": "ivr",
       "product_family": "Ceiling Fan",
       "warranty_status": "in_warranty",
       "request_text": "i paid online for installation but technician did not arrive"
     }'
```
**Response (200 OK):**
```json
{
  "request_id": "SR510824",
  "predicted_team": "Billing",
  "confidence": 0.6341,
  "reasons": [
    "Model signals: Matching text phrase 'paid'; Matching text phrase 'not'; Matching text phrase 'but'.",
    "Policy §3 Advisory: Customer mentions payment alongside technician/service keywords. Per Policy §3, requests belong in Billing only when the payment mechanism itself is disputed. Desk review strongly advised to verify whether ticket should be routed to Installs or Repairs."
  ],
  "review_recommended": true,
  "runner_up_team": "Installs & Demo",
  "runner_up_confidence": 0.3650
}
```

---

## 7. Model Evaluation & Benchmark Summary

All evaluation results are stored under `evidence/`:

| Model Architecture | Train N | Val N | Holdout Accuracy | Macro F1 | Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Majority Baseline (`Repairs`)** | 8,687 | 2,135 | 28.90% | 0.0641 | Naive floor benchmark |
| **TF-IDF + Logistic Regression** | 8,687 | 2,135 | 93.54% | 0.9364 | Text-only unigram/bigram |
| **TF-IDF + LinearSVC** | 8,687 | 2,135 | 94.19% | 0.9425 | Uncalibrated linear SVM |
| **Combined (Text + Structured) + LogReg** | 8,687 | 2,135 | 94.61% | 0.9445 | Adds one-hot metadata |
| **Selected: Combined + Calibrated LinearSVC** | **8,687** | **2,135** | **95.04%** | **0.9485** | **Calibrated probabilities & policy checks** |

---

## 8. Critical Assumptions & Known Limitations

1. **Target Objective vs Operational Reality:** Training targeted `team_label` to satisfy stakeholder Ritu Deshpande's 90%+ bar. However, retrospective analysis confirmed the historical bot misrouted 22.8% of requests. We added automated Policy §3 warnings and ambiguity review flags to mitigate inherited label errors.
2. **Team Renaming Boundary:** Effective 15 Jan 2026, `Installations` became `Installs & Demo` and `Consumables` became `Filters & Consumables`. The test set is strictly post-rename (July–Sept 2026); our pipeline canonicalizes all training labels to the seven active queues so zero obsolete names are output.
3. **Ambiguous Inquiries:** Requests such as *"please call me about purifier"* lack explicit fault tokens. Our system outputs `review_recommended: true` for supervisor triage rather than blindly guessing.

---

## 9. Data Privacy Notice (Policy §10)

In accordance with Kestrel Operations Policy v4.1, §10:
- All customer and ticket records are processed strictly on local hardware.
- No customer records or transcripts are transmitted to third-party endpoints or commercial cloud LLMs.
- All illustrative examples in tests and documentation use synthetic or redacted data.
- The repository contains no API keys, private credentials, or unauthorized exports.

---

## 10. Troubleshooting

- **`ModuleNotFoundError: No module named 'src'`:**  
  Always execute commands from the repository root (e.g. `python -m pytest` or `python src/train.py`), where `PROJECT_ROOT` path resolution is active.
- **Port 8000 Conflict:**  
  If port 8000 is occupied, run FastAPI on an alternate port:
  ```bash
  python -m uvicorn src.api:app --host 127.0.0.1 --port 8080
  ```
  Then launch Streamlit pointing to the new port:
  ```bash
  API_URL="http://127.0.0.1:8080" streamlit run src/ui.py
  ```
