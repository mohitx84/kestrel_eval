# EXECUTIVE MEMORANDUM

**TO:** Ritu Deshpande, Head of D2C Operations, Kestrel Home Appliances  
**FROM:** Machine Learning & Technical Advisory Team  
**DATE:** 15 October 2026  
**SUBJECT:** Decision Recommendation & Evaluation: Replacing Vendor Service-Routing Bot  

---

### 1. Executive Recommendation

**Recommendation: Approve a 4-Week Phased Operational Pilot, Followed by Full Retirement of the Vendor Bot.**

We recommend transitioning Kestrel from the third-party routing bot to the internal, privacy-preserving machine learning routing service under a controlled **80/20 shadow-to-live pilot**. 

Our model achieves **95.04% holdout accuracy** against the vendor bot's historical decisions, comfortably exceeding your 90.0% agreement threshold. More importantly, our operational investigation revealed that the existing bot misroutes **22.83% of all inbound requests**, triggering **3,902 inter-team transfers** that cost Kestrel **₹15.13 lakh annually** in agent waste and repeat contacts—nearly **five times the bot's annual license fee**. The proposed solution directly addresses these defects with automated policy safeguards and zero variable API costs.

---

### 2. Empirical Model Performance & Evidence

The solution was evaluated against 10,822 historical service requests using a strict **time-aware holdout protocol** (training on tickets prior to April 2026, $N=8,687$; testing on subsequent tickets, $N=2,135$):

| Metric | Proposed Calibrated Linear Pipeline | Vendor Bot Target | Majority Baseline (`Repairs`) |
| :--- | :---: | :---: | :---: |
| **Accuracy (Target Agreement)** | **95.04%** | $\ge 90.00\%$ | 28.90% |
| **Macro F1-Score** | **0.9485** | — | 0.0641 |
| **Weighted F1-Score** | **0.9504** | — | 0.1300 |

*Per-Queue Precision / Recall Breakdown:*
- `Billing`: F1 **0.9644** (Precision 94.8%, Recall 98.2%)
- `Installs & Demo`: F1 **0.9593** (Precision 94.5%, Recall 97.4%)
- `Repairs`: F1 **0.9558** (Precision 98.5%, Recall 92.9%)
- `Product Advice`: F1 **0.9446** (Precision 92.6%, Recall 96.4%)
- `Returns & Replacement`: F1 **0.9421** (Precision 94.8%, Recall 93.7%)
- `Warranty Claims`: F1 **0.9377** (Precision 93.1%, Recall 94.5%)
- `Filters & Consumables`: F1 **0.9359** (Precision 92.5%, Recall 94.7%)

Performance remained balanced across channels (WhatsApp: 95.6%, IVR: 95.2%, Chat: 94.6%, Email: 94.3%).

---

### 3. Operational Routing Quality vs. Bot Agreement

High agreement with the historical bot is not equivalent to high operational routing quality. Merging `train.csv` with `resolution_log.csv` reveals critical operational realities:

1. **Vendor Bot Defect Rate:** The vendor bot initially placed tickets into the correct closing queue in only **77.17% of cases**. Approximately **1 in 4 requests (24.91%)** required one or more transfers.
2. **The "Disagreement" Paradox:** In our validation failure analysis, in **32.1% of instances where our model "disagreed" with the vendor bot, our model actually predicted the correct final resolution team** that ultimately resolved the ticket after desk agents had transferred it.
3. **Desk Pain Points Validated:**
   - **Billing:** Had a **36.9% transfer rate** (585 tickets transferred out). As Meenal Joshi highlighted, customers mentioning they "paid for an installation or repair" were blindly dumped into Billing by the bot.
   - **Filters & Consumables:** Suffered a **41.2% transfer rate**, with 315 water purifier breakdowns misrouted here instead of Repairs.

---

### 4. Financial Cost & Business Savings Analysis

To satisfy Finance Controller Farhan Sheikh’s requirement for fixed, predictable operating costs without open-ended AI API bills:

```
+----------------------------------------------------------------------------------+
| ANNUAL OPERATING COMPARISON                                                      |
+----------------------------------------------------------------------------------+
| Current Vendor Bot Annual License Fee:                 ₹3,20,000 / year          |
| Current Bot Operational Misroute Waste (Policy §4):   ₹15,12,856 / year          |
| Current Total Cost of Bot Operations:                 ₹18,32,856 / year          |
+----------------------------------------------------------------------------------+
| Proposed In-House Solution Running Cost:                                         |
|   - Per-Request AI Inference Tokens:                   ₹0 (100% Local CPU Model) |
|   - Internal Cloud Hosting (Small VM / Container):      ₹36,000 / year (₹3,000/mo)|
|   - Maintenance & Retraining Overhead (Estimated):     ₹24,000 / year (₹2,000/mo)|
| Proposed Total Software Cost:                          ₹60,000 / year            |
+----------------------------------------------------------------------------------+
| MEASURED GUARANTEED LICENSE SAVINGS:                  ₹2,60,000 / year (~81% cut)|
| POTENTIAL OPERATIONAL TRANSFER REDUCTION:             ₹4,50,000 - ₹7,50,000/year |
+----------------------------------------------------------------------------------+
```

*Note on Savings Distinction:* The **₹2.60 lakh annual license net savings** is measured and contractual upon retiring the vendor bot. Additional operational savings from reduced transfers (₹4.5L–₹7.5L) are **projected estimates** based on pilot validation and human-review triage.

---

### 5. Headcount & Queue Workload Insights

Addressing your headcount planning for the upcoming budget cycle:

| Destination Queue | Request Volume (% Intake) | Resolution Complexity | Transfer Burden | Headcount Recommendation |
| :--- | :---: | :---: | :---: | :--- |
| **Repairs** | **29.5%** | High (Visits, Diagnostics) | High (38% transfer rate) | **Priority 1 for Staffing.** Highest volume and largest resolution effort. |
| **Billing** | **15.4%** | Low to Moderate | High (Artificial Burden) | **Hold / Reassign.** 35%+ of volume is misrouted service queries. Fix routing before adding headcount. |
| **Filters & Consumables** | **13.2%** | Low (Transactional Sales) | High (Purifier leaks) | **Hold.** Volume will stabilize once purifier breakdowns are redirected to Repairs. |
| **Installs & Demo** | **11.1%** | Moderate (Field Dispatch) | Very Low (3.3% transfer) | **Stable.** Highly efficient routing; staffing should track sales volume. |
| **Returns & Replacement**| **11.1%** | Moderate (Logistics) | Very Low (3.6% transfer) | **Stable.** |
| **Product Advice** | **10.5%** | Low (First-contact resolution) | Very Low (3.8% transfer) | **Stable.** Ideal for agent deflection / self-service FAQs. |
| **Warranty Claims** | **9.3%** | Moderate (Document verification) | Very Low (3.7% transfer) | **Stable.** |

---

### 6. Known Risks & Production Mitigations

1. **Policy §3 Billing Boundary:** Customers frequently write "i paid for repair".  
   *Mitigation:* Built-in regex rule flagging payment + service co-occurrences, routing to service and marking ticket `review_recommended: true`.
2. **Ambiguous Short Inquiries:** Messages like *"please call me about purifier"* cannot be routed with certainty.  
   *Mitigation:* Automated ambiguity detector flags short, non-specific texts for supervisor triage rather than guessing.
3. **Legacy Migration Glitches:** Historic Zoho Desk tickets contained Mojibake encoding and UTC timestamps.  
   *Mitigation:* Text normalization pipeline cleans encoding artifacts; timestamp parsing isolates UTC artifacts from IST CRM records.

---

### 7. Implementation Roadmap & Next Steps

1. **Weeks 1–2 (Shadow Mode):** Deploy FastAPI service alongside the vendor bot. Compare predictions in real-time without taking automated actions.
2. **Weeks 3–4 (Live Assisted Pilot):** Route 20% of inbound chat/web requests with agent-visible confidence meters and explanation cards.
3. **Go/No-Go Decision Gate:** If agent transfer rates decrease by $\ge 15\%$ and ticket agreement exceeds 92%, terminate the vendor contract prior to renewal.
