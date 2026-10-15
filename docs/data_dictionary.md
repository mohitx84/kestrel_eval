# Data Dictionary — Kestrel Home Service-Request Routing

## 1. Overview

This document defines the schema, data types, allowed values, semantic definitions, and data leakage classifications for all features and identifiers across `train.csv`, `test_unlabelled.csv`, `resolution_log.csv`, `teams.csv`, and `sample_submission.csv`.

---

## 2. Table Schemas

### 2.1 `train.csv` (Historical Intake Requests)
Primary training dataset containing requests routed by the legacy vendor bot.

| Column Name | Storage Type | Logical Type | Null Count | Allowed / Observed Values | Description | Leakage Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `request_id` | `object` | Identifier | 0 (0.0%) | Pattern `^SR\d{6}$` (e.g., `SR500001` - `SR510822`) | Unique identifier for each customer service request ticket. | **Excluded from features** (Identifier only). |
| `created_at_ist` | `object` | Timestamp | 0 (0.0%) | `2025-04-01 00:31` to `2026-06-30 23:33` | Ticket creation timestamp in Indian Standard Time (IST, UTC+5:30). | **Validation splitting only** (Not a direct routing feature). |
| `channel` | `object` | Categorical | 0 (0.0%) | `chat` (3,337), `whatsapp` (3,230), `ivr` (3,141), `email` (1,114) | Intake channel through which the customer contacted Kestrel. | **Allowed Feature** (Available at intake). |
| `product_family`| `object` | Categorical | 0 (0.0%) | `Water Purifier` (2,190), `Air Fryer` (1,927), `Mixer Grinder` (1,611), `Induction Cooktop` (1,470), `Room Heater` (1,294), `Ceiling Fan` (1,290), `Robot Vacuum` (1,040) | Product category the customer ticket pertains to. | **Allowed Feature** (Available at intake). |
| `warranty_status`| `object` | Categorical | 0 (0.0%) | `in_warranty` (5,887), `out_of_warranty` (2,728), `shield` (2,207) | Warranty coverage status on record at ticket creation (`shield` refers to Kestrel Shield AMC). | **Allowed Feature** (Available at intake). |
| `request_text` | `object` | Text | 0 (0.0%) | Free-form text (customer message or IVR transcript) | Opening message or transcribed voice transcript submitted by the customer. | **Allowed Feature** (Core predictive text signal). |
| `source` | `object` | Categorical | 0 (0.0%) | `crm` (6,502), `legacy_zoho` (4,320) | Platform origin of the ticket. Note: Test set is 100% `crm`. | **Conditional Feature / Segmenter** (Not predictive of intent; can be dropped or kept as constant indicator). |
| `team_label` | `object` | Categorical (Target) | 0 (0.0%) | 9 distinct values (`Repairs`, `Billing`, `Product Advice`, `Returns & Replacement`, `Warranty Claims`, `Consumables`, `Installations`, `Filters & Consumables`, `Installs & Demo`) | Target queue assigned by the vendor bot at ticket creation. Canonicalized to 7 classes. | **TARGET ONLY** (Strictly forbidden as input). |

---

### 2.2 `test_unlabelled.csv` (Out-of-Time Production Evaluation)
Target requests requiring predictions.

| Column Name | Storage Type | Logical Type | Null Count | Allowed / Observed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `request_id` | `object` | Identifier | 0 (0.0%) | `SR510823` to `SR513000` (2,178 rows) | Primary key for matching to submission. |
| `created_at_ist` | `object` | Timestamp | 0 (0.0%) | `2026-07-01 00:31` to `2026-09-30 23:00` | Chronologically out-of-time (July - Sept 2026). |
| `channel` | `object` | Categorical | 0 (0.0%) | `whatsapp` (661), `ivr` (659), `chat` (633), `email` (225) | Intake channel. |
| `product_family`| `object` | Categorical | 0 (0.0%) | Same 7 categories as train. | Product family. |
| `warranty_status`| `object` | Categorical | 0 (0.0%) | `in_warranty` (1,192), `out_of_warranty` (555), `shield` (431) | Warranty status. |
| `request_text` | `object` | Text | 0 (0.0%) | Clean UTF-8 text. | Inbound customer text. |
| `source` | `object` | Categorical | 0 (0.0%) | `crm` (2,178 - 100.0%) | Modern CRM platform. |

---

### 2.3 `resolution_log.csv` (Historical Retrospective Outcomes)
Post-resolution ticket logs. **FORBIDDEN AS MODEL INPUTS.**

| Column Name | Storage Type | Logical Type | Null Count | Allowed / Observed Values | Description | Leakage Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `request_id` | `object` | Identifier | 0 (0.0%) | Matches `train.csv` (10,822 rows) | Ticket identifier. | Key only. |
| `first_team` | `object` | Categorical | 0 (0.0%) | 9 distinct teams (100% matches `team_label`) | Queue assigned at creation. | **LEAKAGE — Target equivalent**. |
| `final_team` | `object` | Categorical | 0 (0.0%) | 9 distinct teams (7 canonical) | Queue that actually closed the ticket. | **LEAKAGE — Future resolution data**. |
| `transfers` | `int64` | Integer | 0 (0.0%) | `0` (8,126), `1` (1,490), `2` (1,206) | Number of times ticket was moved between teams. | **LEAKAGE — Future operational event**. |
| `resolved_at` | `object` | Timestamp | 0 (0.0%) | `2025-03-31 22:41` to `2026-07-02 16:16` | Resolution event timestamp (UTC for Zoho, IST for CRM). | **LEAKAGE — Future event & corrupted timezone**. |

---

### 2.4 `teams.csv` (Organizational Hierarchy & Metadata)

| Column Name | Storage Type | Description |
| :--- | :--- | :--- |
| `team` | `object` | Historical team name (`Installations`, `Repairs`, `Consumables`, `Billing`, `Returns & Replacement`, `Warranty Claims`, `Product Advice`). |
| `renamed_to` | `object` | Updated name effective 15 Jan 2026 (`Installs & Demo`, `Filters & Consumables`, null for unchanged). |
| `handles` | `object` | Operational boundary and responsibility description. |

---

### 2.5 `sample_submission.csv` (Output Submission Contract)

| Column Name | Storage Type | Expected Values | Description |
| :--- | :--- | :--- | :--- |
| `request_id` | `object` | 2,178 IDs matching `test_unlabelled.csv` | Preserves exact test set ordering without gaps or duplications. |
| `team` | `object` | 1 of 7 Canonical Current Names: `Installs & Demo`, `Repairs`, `Filters & Consumables`, `Billing`, `Returns & Replacement`, `Warranty Claims`, `Product Advice` | Model predicted destination queue. |

---

## 3. Team Alias Canonicalization Map

| Raw Historical / Alias Name | Canonical Current Name | Effective Date | Notes |
| :--- | :--- | :--- | :--- |
| `Installations` | `Installs & Demo` | Pre-15 Jan 2026 | New-product installation, demo, wall-mounting. |
| `Installs & Demo` | `Installs & Demo` | Post-15 Jan 2026 | Current active team name. |
| `Consumables` | `Filters & Consumables` | Pre-15 Jan 2026 | Spares, filters, blades, membranes, AMC kits. |
| `Filters & Consumables`| `Filters & Consumables` | Post-15 Jan 2026 | Current active team name. |
| `Repairs` | `Repairs` | All | Unchanged. Breakdowns, leaks, faults. |
| `Billing` | `Billing` | All | Unchanged. Invoices, GST, refunds, EMI. |
| `Returns & Replacement`| `Returns & Replacement` | All | Unchanged. Wrong/damaged delivery, returns. |
| `Warranty Claims` | `Warranty Claims` | All | Unchanged. Warranty certificate, claim status. |
| `Product Advice` | `Product Advice` | All | Unchanged. Usage queries, pre/post purchase. |

---

## 4. Leakage Prevention Checklist

- [x] `team_label` isolated as training target $y$.
- [x] All columns from `resolution_log.csv` (`first_team`, `final_team`, `transfers`, `resolved_at`) excluded from training and inference data pipelines.
- [x] `request_id` used strictly as non-predictive entity key.
- [x] `created_at_ist` excluded from classifier feature space; used solely for temporal data splitting.
- [x] All vectorizer vocabularies, IDF matrices, and encoders fit strictly on training splits.
