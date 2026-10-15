# Assumptions and Technical Decisions — Kestrel Home Service-Request Routing

## 1. Executive Summary & Strategy

This document formally records all data science, engineering, and business assumptions and decisions adopted for the Kestrel Home Service-Request Routing project (Variant B). Every technical decision is grounded in empirical verification of the assignment files and alignment with Kestrel Operations Policy v4.1.

---

## 2. Core Business & Modeling Decisions

### 2.1 Target Definition & Dual-Objective Architecture
- **Decision:** Train the production classification model on `team_label` (canonicalized to the 7 active team names).
- **Rationale:** 
  - *Objective A (Target Agreement):* Stakeholder Ritu Deshpande established a 90%+ agreement threshold with historical bot routing decisions to authorize replacing the third-party vendor bot.
  - *Objective B (Operational Quality):* Historical routing log analysis proves the vendor bot misrouted 22.83% of requests, causing 3,902 inter-team transfers costing ₹18.91 lakh over 15 months (~₹15.13 lakh/year). Therefore, while the classifier learns the historical pattern, our system includes policy-aware explanation checks, confidence thresholds, and human-review flags to mitigate known bot defects in production.

### 2.2 Canonicalization of Team Aliases
- **Decision:** Map historical aliases (`Installations` $\rightarrow$ `Installs & Demo`, `Consumables` $\rightarrow$ `Filters & Consumables`) to their official active names across all training data and model targets.
- **Evidence:** 
  - Operations Policy §5 explicitly mandates that effective 15 January 2026, `Installations` became `Installs & Demo` and `Consumables` became `Filters & Consumables`, with no change in responsibilities.
  - Verification of `train.csv` confirmed that the old names terminated on 14 January 2026, and the new names began immediately on 15 January 2026.
  - The production evaluation set (`test_unlabelled.csv`) spans 1 July 2026 to 30 September 2026 (100% post-renaming). Predicting obsolete aliases would violate the destination contract and cause operational failures.
  - Canonicalization ensures that all 10,822 historical training examples contribute to the statistical learning of the 7 active destination queues.

### 2.3 Validation Protocol & Temporal Integrity
- **Decision:** Use a strictly time-aware out-of-time holdout split as primary evaluation, complemented by stratified cross-validation for stability verification.
  - *Temporal Split:* Training on tickets created prior to 1 April 2026 ($N=8,687$), evaluating on tickets created from 1 April 2026 to 30 June 2026 ($N=2,135$, ~20%).
- **Rationale:** 
  - `test_unlabelled.csv` is strictly chronological (July–September 2026) following historical data. A temporal split accurately reflects production drift, seasonality, and the absence of legacy Zoho tickets.
  - Results: Temporal holdout achieved **95.04% Accuracy (Macro F1: 0.9485)**, while stratified holdout achieved **95.52% Accuracy (Macro F1: 0.9538)**. Both significantly exceed the 90.0% threshold.

---

## 3. Data Leakage Prevention Controls

Strict architectural boundaries were enforced to prevent any leakage from target outcomes or future resolution events:

| Feature / Artifact | Intake Status | Leakage Risk | Architectural Decision |
| :--- | :--- | :--- | :--- |
| `request_text` | Available at intake | None | Core text feature. Preprocessed and transformed using TF-IDF fit strictly on training splits. |
| `channel` | Available at intake | None | Categorical feature. One-hot encoded inside fitted ColumnTransformer. |
| `product_family` | Available at intake | None | Categorical feature. One-hot encoded inside fitted ColumnTransformer. |
| `warranty_status` | Available at intake | None | Categorical feature. One-hot encoded inside fitted ColumnTransformer. |
| `request_id` | Metadata | High (if used as feature) | Strictly isolated as an opaque key for joining and submission; never passed into feature matrices. |
| `created_at_ist` | Metadata | High (if used as feature) | Excluded from feature space. Utilized solely to partition temporal validation splits. |
| `source` | System origin | Ambiguous | Test data is 100% `crm`. Excluded from model features to avoid memorizing legacy platform artifacts. |
| `first_team` | Post-intake event | Complete Target Leakage | Excluded. 100% identical to `team_label`. |
| `final_team` | Post-resolution outcome | Future Data Leakage | Excluded from training features. Used solely in offline error auditing. |
| `transfers` | Post-resolution outcome | Future Data Leakage | Excluded from training features. |
| `resolved_at` | Post-resolution timestamp | Future Data & Corrupted Timezone | Excluded from training features. |

---

## 4. Text Processing & Legacy Zoho Artifacts

- **Observation:** 480 tickets in `train.csv` (all from `legacy_zoho`) contained UTF-8 Mojibake artifacts (`â€¦` for ellipsis, `â€“` for dashes, accented vowels such as `urgént`, `paymént`).
- **Mitigation Pipeline:**
  1. Unicode NFKD decomposition to map accented characters (`é` $\rightarrow$ `e`).
  2. Regex replacement for known Zoho Mojibake sequences.
  3. ASCII encoding sanitization to remove stray non-ASCII bytes.
  4. Lowercasing, punctuation normalization, and whitespace collapse.
  5. Sublinear TF-IDF scaling ($1 + \log(\text{tf})$) with unigrams and bigrams (min_df=2) to capture domain phrases (`water purifier`, `spare blade`, `invoice copy`, `not working`).

---

## 5. Model Architecture & Selection Rationale

- **Selected Model:** `CalibratedClassifierCV(LinearSVC(C=0.8), cv=3)` wrapped in a unified scikit-learn `Pipeline` with `ColumnTransformer`.
- **Why Selected over Alternatives:**
  1. **Empirical Superiority:** Outperformed all baselines (Majority: 28.90%, Logistic Regression: 94.61%, LinearSVC: 94.19%), reaching **95.04% holdout accuracy and 0.9485 Macro F1**.
  2. **Calibrated Probabilities:** Standard SVMs output uncalibrated margin distances. Wrapping `LinearSVC` with 3-fold Platt calibration provides genuine, reliable posterior probabilities for production confidence estimation.
  3. **Zero Variable AI API Cost:** Runs 100% locally on CPU in <10ms per inference, requiring zero GPU and generating zero API usage bills, directly answering Finance Controller Farhan Sheikh's mandate.
  4. **Interpretability & Transparency:** Directly exposes underlying feature weights ($w \cdot x$), enabling mathematical extraction of top positive drivers for customer explanation.
  5. **Compact Footprint:** Serialized model artifact is under 3MB, easily versioned in Git/Docker without Large File Storage (LFS).

---

## 6. Explainability, Confidence & Review Policy

1. **Feature Attribution:** Top positive tokens and metadata signals for the predicted class are computed from the linear decision function and translated into plain-English reasons.
2. **Confidence Calibration:** Calibrated probability of the winning class is output as `confidence`.
3. **Ambiguity & Policy Verification:**
   - *Policy §3 (Billing vs Repair/Install):* If the customer text mentions "paid", "payment", or "emi", but also includes repair/installation terms ("broken", "leaking", "installer", "slot", "technician"), the reason explicitly notes: *"Customer mentions payment alongside service/repair terms. Policy §3 specifies Billing is strictly for payment defects; routing prioritized primary service need."*
   - *Review Recommendation:* `review_recommended: true` is triggered whenever:
     - Calibrated confidence $< 0.65$, OR
     - Confidence margin between the top 2 candidate teams $< 0.15$, OR
     - An ambiguous request without actionable intent is detected.
