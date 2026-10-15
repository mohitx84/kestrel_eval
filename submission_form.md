# Project Submission Form & AI Tool Disclosure

### 1. Project Title & Identifier
- **Project Name:** Kestrel Home Service-Request Routing Service (Variant B)
- **Repository Root:** `c:\Users\MOHIT KUMAR\Desktop\kestrel-routing`
- **Output Submission Artifact:** `predictions.csv` (2,178 rows, matching `sample_submission.csv`)

---

### 2. Project & Approach Summary
We built an end-to-end, locally reproducible machine learning service that replaces Kestrel Home Appliances' ₹3.2 lakh/year third-party vendor routing bot. The project ingests inbound customer requests across four channels (chat, WhatsApp, IVR, email) and seven product lines, routing them to seven active destination queues in accordance with Operations Policy v4.1.

The core architecture combines a calibrated linear classifier (`CalibratedClassifierCV(LinearSVC)`) on n-gram TF-IDF text features and one-hot encoded metadata with an explainability and policy-checking layer. Beyond reproducing historical routing, the solution addresses major operational failure modes identified in historical resolution logs (where 22.83% of requests were misrouted by the vendor bot), integrating automated Policy §3 Billing safeguards, calibrated confidence scores, and ambiguity detection for human review.

---

### 3. Expected Performance & Validation Results
- **Validation Protocol:** Strict Temporal Holdout (Train on tickets created before 1 April 2026, $N=8,687$; evaluate on tickets created from 1 April 2026 to 30 June 2026, $N=2,135$).
- **Held-Out Accuracy (Target Agreement):** **95.04%** (Comfortably exceeds the 90.0% target).
- **Macro F1-Score:** **0.9485**.
- **Weighted F1-Score:** **0.9504**.
- **Majority Class Baseline (`Repairs`):** 28.90% Accuracy (Macro F1: 0.0641).
- **Stratified Holdout Comparison (80/20):** 95.52% Accuracy (Macro F1: 0.9538).
- **Test Set Predictions:** 2,178 out-of-time production tickets (July–September 2026). Test labels are unlabelled in the assignment pack; no fabricated test score is claimed.

---

### 4. Technical Stack & Tools Used
- **Programming Language:** Python 3.10
- **Data Manipulation:** `pandas` (v2.0+), `numpy` (v1.24+)
- **Machine Learning:** `scikit-learn` (`TfidfVectorizer`, `OneHotEncoder`, `ColumnTransformer`, `Pipeline`, `LinearSVC`, `CalibratedClassifierCV`, `DummyClassifier`, `metrics`)
- **Model Serialization:** `joblib`
- **API Framework:** `FastAPI` (v0.110+) with `uvicorn` and `pydantic` (v2.5+)
- **User Interface:** `Streamlit` (v1.30+)
- **Testing & Verification:** `pytest` (22 comprehensive unit and integration tests passing)
- **Plotting & Reporting:** `matplotlib`, `seaborn`

---

### 5. Paid API Disclosure & Runtime Constraints
- **Were any paid or proprietary external AI APIs used during training or inference?**  
  **NO.** Zero external API calls, hosted LLMs, or paid commercial endpoints were used.
- **Inference Runtime:** 100% local CPU inference execution. Average latency per request is under 10 milliseconds.
- **Financial Predictability:** Zero variable token costs, answering Finance Controller Farhan Sheikh's explicit constraint.

---

### 6. AI Assistance & Engineering Tool Disclosure
- **AI Coding Assistant:** Google Antigravity IDE (Gemini agentic pair programmer).
- **Specific Tasks Assisted:**
  - Automated inspection of raw data shapes, Mojibake encoding patterns, and timezone offsets.
  - Generating scikit-learn pipeline boilerplate and cross-validation scaffolding.
  - Writing comprehensive pytest test suites covering edge cases, policy rules, and API endpoints.
  - Creating the interactive Streamlit user interface and FastAPI contract.
  - Drafting formatted technical documentation and business memos based on actual computed data.

---

### 7. Approaches Attempted & Discarded (With Empirical Reasons)

1. **Majority Class Classifier (`DummyClassifier`):**
   - *Result:* 28.90% Accuracy, 0.0641 Macro F1.
   - *Reason Discarded:* Essential as a floor benchmark, but vastly insufficient for production routing.
2. **Text-Only TF-IDF + Logistic Regression:**
   - *Result:* 93.54% Accuracy, 0.9364 Macro F1 on temporal split.
   - *Reason Discarded:* Performed well, but was surpassed by SVM and did not take advantage of structured metadata (`product_family`, `channel`, `warranty_status`).
3. **TF-IDF with Character N-grams (3–5 char):**
   - *Result:* 93.86% Accuracy, 0.9392 Macro F1.
   - *Reason Discarded:* High feature dimensionality (over 45,000 features) increased memory footprint without improving accuracy over word-level (1,2)-grams with sublinear TF scaling.
4. **Uncalibrated LinearSVC:**
   - *Result:* 94.19% Accuracy, but raw decision function output margins are uncalibrated distance metrics rather than probabilities.
   - *Reason Discarded:* Lacked true posterior probabilities required for confidence scoring and human-review gating. Replaced with `CalibratedClassifierCV(LinearSVC)` with 3-fold Platt calibration.
5. **Training Directly on `final_team` from `resolution_log.csv` as Target:**
   - *Reason Discarded:* Discarded for the primary classifier because stakeholder Ritu Deshpande explicitly defined the project gate as 90%+ match with historical intake routing (`team_label`). Retrospective resolution logs were instead used for error analysis and operational quality assessment.

---

### 8. Known Limitations & Remaining Risks

1. **Policy §3 Billing Ambiguity:** Customers frequently mention payment status when asking for physical service (e.g., "i paid for repair"). While our system incorporates automated policy detection and review flags, edge cases where a customer has both an invoice dispute AND a physical breakdown require operational human triage.
2. **Short, Vague Text:** Tickets consisting solely of "please call me about purifier" lack sufficient linguistic tokens to discern whether the issue is a filter purchase, leak breakdown, or usage inquiry. The system flags these with `review_recommended: true` rather than forcing a blind guess.
3. **Distributional Drift:** Should Kestrel launch new product categories (e.g., dishwashers) or new queues, the model must be updated with new training samples and retraining pipelines.

---

### 9. Deliverables Verification Table

| Deliverable Artifact | Repository Path | Status |
| :--- | :--- | :--- |
| Submission Predictions | `predictions.csv` | Verified (2,178 rows, exact schema, canonical names) |
| Executive Memo | `memo.md` | Verified (Addressed to Ritu Deshpande) |
| Submission Form | `submission_form.md` | Verified (Complete disclosures) |
| Source Code | `src/` (`data.py`, `train.py`, `predict.py`, `api.py`, `ui.py`) | Verified (Modular, PEP-8 compliant) |
| Trained Model Artifact | `models/kestrel_routing_model.joblib` | Verified (3.1 MB serialized pipeline) |
| Test Suite | `tests/` (`test_data.py`, `test_model.py`, `test_api.py`, `test_submission.py`) | Verified (22/22 tests passing) |
| Metrics & Evidence | `evidence/` (`metrics.json`, `model_comparison.csv`, `classification_report.txt`, `confusion_matrix.png`, `failure_cases.csv`) | Verified |
| Documentation | `docs/` (`assignment_inventory.md`, `data_dictionary.md`, `assumptions_and_decisions.md`, `demo_script.md`) | Verified |
