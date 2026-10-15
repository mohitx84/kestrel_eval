# Assignment Inventory — Kestrel Home Service-Request Routing (Variant B)

## 1. Executive Summary & Purpose

This document provides a comprehensive inventory and audit of all data, policy, and stakeholder communication files supplied for the Kestrel Home Service-Request Routing engagement. It establishes the ground truth, identifies data quality caveats and legacy migration artifacts, and defines the technical and business boundaries for model development.

---

## 2. Inventory of Provided Files

All files were located in `data/` and mirrored into `data/raw/` preserving pristine copies without modification.

| File Name | Size (Bytes) | Row Count | Column Count | Description & Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `train.csv` | 1,475,821 | 10,822 | 8 | Historical service requests from 1 Apr 2025 to 30 Jun 2026 with historical routing labels (`team_label`). |
| `test_unlabelled.csv` | 260,777 | 2,178 | 7 | Out-of-time production requests from 1 Jul 2026 to 30 Sep 2026 awaiting routing predictions. |
| `resolution_log.csv` | 589,679 | 10,822 | 5 | Operational outcomes of historical requests: `first_team`, `final_team`, `transfers`, and `resolved_at`. |
| `teams.csv` | 808 | 7 | 3 | Official team names, effective rename dates (15 Jan 2026), and operational responsibilities. |
| `sample_submission.csv` | 37,042 | 2,178 | 2 | Contractual output schema defining expected columns (`request_id`, `team`) and row sequence. |
| `ops-policy.pdf` | 3,244 | 1 page | N/A | Kestrel Operations Policy v4.1 detailing routing rules, transfer costs, team changes, and data privacy. |
| `email-thread.txt` | 2,841 | 50 lines | N/A | Internal stakeholder discussions highlighting business constraints, known failure modes, and headcount goals. |
| `README.txt` | 1,157 | 23 lines | N/A | Data pack specification and column descriptions. |

---

## 3. Stakeholder Requirements & Business Context

From `email-thread.txt` and `ops-policy.pdf`:

1. **Ritu Deshpande (Head of D2C Operations — Decision Maker):**
   - Goal: Replace the external vendor routing bot currently costing ₹3.2 lakh annually (~₹26,667/month).
   - Target: 90%+ agreement with historical routing labels (`team_label`).
   - Headcount planning: Needs accurate reporting on which functional queues experience the highest demand.

2. **Farhan Sheikh (Finance Controller):**
   - Constraint: Strict financial predictability. Refuses to swap the fixed ₹3.2 lakh vendor license for an unpredictable, usage-scaled AI API bill (e.g., hosted LLM token costs).
   - Requirement: Definite monthly run cost in writing before authorizing any switch.

3. **Meenal Joshi (Service Desk Manager):**
   - Pain Point 1: Misrouted billing tickets. Half of the Billing queue some weeks consists of customers stating they already paid for an installation or repair; these are transferred out immediately.
   - Pain Point 2: Consumables queue regularly receives purifier breakdowns.
   - Pain Point 3: Highly ambiguous requests (e.g., "please call me about my purifier") cannot be routed deterministically without customer clarification.
   - Core Metric: Excessive transfers consume the majority of desk agent capacity.

4. **Tanmay Kulkarni (Data & IT Admin):**
   - Data Origin: Explains that `team_label` reflects the queue assigned by the legacy vendor bot at ticket creation, not verified ground truth.
   - Renaming: Two teams were renamed partway through the dataset (effective 15 Jan 2026).
   - Migration Artifacts: Pre-1 Oct 2025 records were migrated from `legacy_zoho`. They contain encoding glitches (Mojibake) and unadjusted UTC resolution timestamps.

---

## 4. Policy Rules & Economic Parameters (Policy v4.1)

- **§3 Routing Policy:**
  - Inbound requests (IVR transcript, chat, WhatsApp, email) are routed upon ticket creation.
  - *Billing Rule:* A request belongs to `Billing` ONLY when the problem is the payment mechanism itself (invoice, GST, double charge, refund, EMI conversion, coupons). Simply mentioning that payment was completed for an installation or repair does **not** make it a Billing ticket.
- **§4 Operational Cost Penalties:**
  - Each inter-team transfer costs **₹305** in direct agent handling time.
  - Each misrouted request generates on average one extra customer contact costing **₹260**.
  - Total operational penalty per misrouted request: **₹565** (plus additional ₹305 for subsequent transfers).
  - Technician on-site visit cost: ₹540.
  - Vendor routing bot license: ₹3,20,000 per year (~₹26,667 per month).
- **§5 Team Renaming (Effective 15 Jan 2026):**
  - `Installations` $\rightarrow$ `Installs & Demo`
  - `Consumables` $\rightarrow$ `Filters & Consumables`
  - Core team responsibilities remain identical.
- **§9 Systems & Timestamp Discrepancy:**
  - `< 2025-10-01`: Data hosted in Zoho Desk (`source == 'legacy_zoho'`).
  - `≥ 2025-10-01`: Data hosted in internal Kestrel CRM (`source == 'crm'`).
  - Creation timestamps are in Indian Standard Time (IST, UTC+5:30).
  - Resolution timestamps from `legacy_zoho` were extracted in UTC and **never converted to IST** during migration.
- **§10 Data Privacy:**
  - Strict prohibition against uploading customer data, request text, or logs to public repositories or external APIs.

---

## 5. Verification of Raw Data & File Integrity

### 5.1 Dataset Dimensions and Completeness

- **`train.csv`**: 10,822 rows, 8 columns. Exactly 0 null values across all columns.
- **`test_unlabelled.csv`**: 2,178 rows, 7 columns. Exactly 0 null values across all columns.
- **`resolution_log.csv`**: 10,822 rows, 5 columns. Exactly 0 null values.
- **`sample_submission.csv`**: 2,178 rows, 2 columns (`request_id`, `team`).

### 5.2 Key Integrity and Relational Joins

- **Primary Key:** `request_id` (format `SR######`).
- **Train to Resolution Log Join:**
  - Train unique IDs: 10,822 (0 duplicates).
  - Resolution Log unique IDs: 10,822 (0 duplicates).
  - Intersection: 10,822 (100% 1-to-1 match).
  - `first_team` in `resolution_log.csv` matches `team_label` in `train.csv` in **10,822 out of 10,822 rows (100.0%)**.
- **Test to Sample Submission Match:**
  - Test unique IDs: 2,178 (0 duplicates).
  - Sample submission unique IDs: 2,178 (0 duplicates).
  - Exact row-by-row sequence match: 100% verified (`sub['request_id'] == test['request_id']`).

### 5.3 Chronological Timeline & Source Breakdown

| Dataset | Date Range (IST) | Span | `source` Breakdown | Renaming Phase |
| :--- | :--- | :--- | :--- | :--- |
| `train.csv` (Zoho) | 2025-04-01 00:31 to 2025-09-30 23:00 | 6.0 mos | 4,320 `legacy_zoho` (100%) | Historical (`Installations`, `Consumables`) |
| `train.csv` (CRM-Pre) | 2025-10-01 00:37 to 2026-01-14 18:37 | 3.5 mos | 2,752 `crm` (100%) | Historical (`Installations`, `Consumables`) |
| `train.csv` (CRM-Post) | 2026-01-15 15:58 to 2026-06-30 23:33 | 5.5 mos | 3,750 `crm` (100%) | Renamed (`Installs & Demo`, `Filters & Consumables`) |
| `test_unlabelled.csv` | 2026-07-01 00:31 to 2026-09-30 23:00 | 3.0 mos | 2,178 `crm` (100%) | Renamed (`Installs & Demo`, `Filters & Consumables`) |

*Finding:* The test dataset is strictly out-of-time (July–September 2026), occurs entirely after the 15 Jan 2026 renaming date, and contains 100% modern CRM records.

---

## 6. Target Label Analysis & Team Alias Canonicalization

### 6.1 Raw `team_label` Distribution in `train.csv`

| Raw `team_label` | Count | Percentage | Effective Era | Canonical Destination Label |
| :--- | :--- | :--- | :--- | :--- |
| `Repairs` | 3,129 | 28.91% | All | `Repairs` |
| `Billing` | 1,656 | 15.30% | All | `Billing` |
| `Product Advice` | 1,180 | 10.90% | All | `Product Advice` |
| `Returns & Replacement` | 1,174 | 10.85% | All | `Returns & Replacement` |
| `Warranty Claims` | 1,040 | 9.61% | All | `Warranty Claims` |
| `Consumables` | 927 | 8.57% | Pre-15 Jan 2026 | `Filters & Consumables` |
| `Installations` | 745 | 6.88% | Pre-15 Jan 2026 | `Installs & Demo` |
| `Filters & Consumables` | 531 | 4.91% | Post-15 Jan 2026 | `Filters & Consumables` |
| `Installs & Demo` | 440 | 4.07% | Post-15 Jan 2026 | `Installs & Demo` |
| **Total** | **10,822** | **100.00%** | | |

### 6.2 Canonical Class Distribution (7 Functional Queues)

When mapped to official destination teams:
1. `Repairs`: 3,129 (28.91%)
2. `Billing`: 1,656 (15.30%)
3. `Filters & Consumables`: 1,458 (13.47%) — *(927 Consumables + 531 Filters & Consumables)*
4. `Installs & Demo`: 1,185 (10.95%) — *(745 Installations + 440 Installs & Demo)*
5. `Product Advice`: 1,180 (10.90%)
6. `Returns & Replacement`: 1,174 (10.85%)
7. `Warranty Claims`: 1,040 (9.61%)

**Crucial Decision:** The model target must be standardized to the 7 canonical destination queues during training so that historical samples from `Installations` and `Consumables` provide full learning signals to the renamed classes. Under no circumstance may the model output obsolete aliases (`Installations`, `Consumables`) on the test set.

---

## 7. Resolution Log & Transfer Audit (Operational Ground Truth)

Auditing `resolution_log.csv` against `train.csv` revealed critical operational insights:

1. **Bot Routing Accuracy vs. Reality:**
   - The vendor bot's initial routing (`first_team`) agreed with the team that closed the ticket (`final_team`) in only **8,351 out of 10,822 requests (77.17%)**.
   - **2,471 requests (22.83%)** were closed by a completely different team than where the bot initially sent them.
2. **Transfer Statistics:**
   - 0 transfers: 8,126 requests (75.09%)
   - 1 transfer: 1,490 requests (13.77%)
   - 2 transfers: 1,206 requests (11.14%)
   - Mean transfers per request: 0.361.
   - Total inter-team transfers: **3,902**.
3. **Worst Performing Queues:**
   - `Filters & Consumables`: **41.2% transferred** (40.2% final team disagreement). 315 requests misrouted here were transferred to `Repairs` (purifier breakdowns).
   - `Repairs`: **38.4% transferred** (36.3% disagreement).
   - `Billing`: **36.9% transferred** (35.3% disagreement). 192 transferred to `Repairs`, 146 to `Installs & Demo`, 125 to `Returns & Replacement`.
   - In contrast, `Installs & Demo` (5.8% transfer rate), `Returns & Replacement` (6.0%), `Warranty Claims` (6.2%), and `Product Advice` (6.6%) exhibited high routing fidelity.
4. **Financial Impact of Poor Routing:**
   - Handling cost of transfers (3,902 × ₹305): ₹11,90,110.
   - Extra customer contact cost (2,696 misrouted tickets × ₹260): ₹7,00,960.
   - Total 15-month operational waste: **₹18,91,070**.
   - **Annualized cost of bot misrouting: ₹15,12,856 per year (~₹1.26 lakh/month).**
   - The hidden cost of the bot's routing errors is **4.7× greater** than its annual ₹3.2 lakh license fee!

---

## 8. Data Quality & Preprocessing Caveats

1. **Text Encoding & Mojibake in `legacy_zoho`:**
   - 480 rows in `legacy_zoho` contain corrupted characters (e.g., `â€¦` for `...`, `â€“` for `–`, `urgént`, `paymént`, `sméll`).
   - `crm` and `test_unlabelled.csv` contain 0 corrupted characters.
   - *Mitigation:* Text cleaning pipeline must normalize UTF-8 Mojibake, strip non-ASCII artifacts, and lowercase text to avoid feature sparsity.
2. **Timestamp Inconsistency:**
   - 1,140 rows in `resolution_log.csv` have `resolved_at < created_at_ist`.
   - 100% of these 1,140 rows belong to `legacy_zoho`.
   - Adding 5 hours 30 minutes (UTC to IST offset) brings negative resolution times to exactly 0.
   - *Mitigation:* `resolved_at` is strictly prohibited from feature pipelines. Creation timestamps are verified as valid IST and will guide time-based validation splitting.
3. **Data Leakage Safeguards:**
   - No target features (`team_label`, `first_team`, `final_team`, `transfers`, `resolved_at`) may enter prediction pipelines.
   - Only intake features (`channel`, `product_family`, `warranty_status`, `request_text`) will be utilized.
