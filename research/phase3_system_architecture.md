# 📂 PHASE 3 — System Architecture & AI/ML Integration Design
### Full-Stack Design for the Collaborative Procurement Decision Framework
**Subject:** An AI-Assisted, Freshness- and Logistics-Aware Collaborative Procurement Decision Framework for Street Vendors
**Question this phase answers:** What is the complete, buildable V1 system architecture, and exactly where — if anywhere — does genuine AI/ML belong in it?

**Data labeling used throughout:** 🟢 REAL PUBLIC DATA · 🔵 REAL PRIMARY DATA (per the Phase 1C timeline) · 🟡 EXPERIMENTAL ASSUMPTION · 🟠 SIMULATED DATA — unchanged from Phases 2A/2B.

**Component color key (per this phase's Strict Rule 5):** 🟦 AI/ML-adjacent · 🟩 Mathematical/Deterministic Model (Phase 2A) · 🟨 Optimization (Phase 2B) · 🟪 Full-Stack Application.

This document inherits Phase 2A's Stage 2 model and Phase 2B's Stage 1 algorithm **unmodified** — nothing here redesigns the mathematical decision model, the candidate-generation approach, the constraint evaluation, or the overlap-resolution logic. This phase's job is strictly the software architecture those models live inside, and the honest determination of whether any genuine AI/ML belongs in that architecture.

---

## 1. Executive Summary

**Verdict: 🟡 ARCHITECTURE APPROVED WITH REQUIRED CORRECTIONS (applied below) — the AI/ML question remains formally open pending a dedicated Phase 3A audit.**

The V1 system is a small, single-region web application with three real actors — the vendor, a researcher/administrator operating the pilot, and Phase 2A/2B's own deterministic engine — connected by a short, auditable pipeline: **Frontend → Backend/API → Vendor Database + Public Price Ingestion → (conditional) Cold-Start Demand Estimation → Optimization Engine (Phase 2B Stage 1 generation, Phase 2A Stage 2 evaluation, Phase 2B Stage 3 selection, all unmodified) → Recommendation & Explanation Engine → Dashboard**, with a feedback/logging loop back into the database for reproducibility.

**The central finding of this phase, and the one the "no fake AI" rule exists to force:** after auditing six realistic AI/ML uses — demand forecasting, similarity-based demand estimation, demand-pattern clustering, price prediction, recommendation learning, and anomaly detection (Section 6) — **no trained machine-learning model is scientifically justified for V1.** At 10–20 vendors, a short pilot window, and no historical outcome data, every candidate that depends on vendor-level history fails on data volume alone; the one candidate with genuinely sufficient data (Agmarknet's public price history) fails on a different, more important ground — it doesn't feed any parameter the deterministic model actually needs (Phase 2A's model consumes the *current* realized price, not a forecast), so building it would be ML included for the sake of the label, which is explicitly rejected in Section 8.

**The system's one AI-adjacent component is a deterministic case-matching lookup for cold-start demand estimation** — used only for a vendor with insufficient own purchase history, only to estimate the single parameter $r_{i,c}$, and never to make or influence the recommend/don't-recommend decision. This is Phase 1C's Layer 1 mechanism, reaffirmed here rather than re-invented, and it is labeled throughout as case-based reasoning, explicitly **not** machine learning. **Simplified in this revision** (Section 9): rather than a weighted multi-feature similarity score — which would require justifying arbitrary weights (why 40% category, 20% location?) with no data to support any particular split — the estimator now uses exact categorical matching only (same category, same commodity, same declared purchase-frequency bucket) and reports the **median** $r_{i,c}$ among matches, with an explicit, ordered fallback hierarchy for when no exact match exists. There is nothing left to weight and therefore nothing arbitrary to defend.

**Strict separation is maintained end-to-end:** 🟦 the case-matching estimator only ever produces one input number, tagged 🟡 estimated; 🟩 Phase 2A's deterministic cost/constraint model decides feasibility and savings from whatever $r_{i,c}$ it is given, estimated or observed; 🟨 Phase 2B's exact graph/set-packing pipeline decides which groups are actually recommended; 🟪 the full-stack application (frontend, backend, database) exists only to move data between these layers and present the result. No layer above the estimator is statistical, learned, or opaque.

**Technology stack (Section 18), revised in this round:** Python/FastAPI backend, SQLite database, a React frontend calling the API (or plain HTML/CSS/JavaScript if React's tooling overhead doesn't fit the timeline), NetworkX + itertools for the optimization engine, Haversine distance from vendor-supplied coordinates (browser geolocation or manual survey entry — no geocoding API), manually-tracked config files for reproducibility. **Streamlit was reconsidered and dropped as the default recommendation**: a Streamlit app reading the database directly would also have quietly bypassed this document's own Frontend → Backend/API → Database layering (Section 5), and — separately from that — would read as a Python research dashboard rather than the full-stack web application this project is meant to demonstrate. Nothing here needs GPUs, microservices, or a trained model registry, because nothing in the approved design requires one.

**Recommendations carry explicit timestamps, not "today."** Because price ingestion and the recommendation run are batch, periodic events rather than continuous ones, every recommendation now states its commodity, the price date it used, and the analysis-run timestamp explicitly (Sections 15, 16) — "today's recommendation" is dropped as a phrase that overstates how real-time the system actually is.

---

## 2. Final V1 System Definition

**1. Who are the users?**
- **Vendor (primary user).** A street vendor procuring one or more of the study's commodities. Registers, enters demand and (if known) confirmed MOQ, views recommendations, accepts/declines, optionally reports outcomes.
- **Researcher/administrator (pilot operator).** Manages the vendor roster, ingests and verifies Agmarknet price data, sets and version-controls experimental parameters ($D_{max}$, $F_c$, margin $m$, MOQ assumptions), monitors data quality, and runs the batch recommendation job.
- **No trader/supplier user role.** Per Phase 1B, vendors typically access the market through a single partner trader; the trader is an external counterparty modeled only as a source of price and MOQ data, never a system user.

**2. What information does a vendor provide?** Registration (name/ID, category, commodities traded, location — GPS coordinates recorded at registration, not tracked continuously); demand entries ($r_{i,c}$, per commodity, updated periodically); current individual price paid ($p^{ind}_{i,c}$); confirmed MOQ if and only if their trader has stated one; optional post-recommendation feedback (accepted/declined, and — if they proceeded — the actual outcome).

**3. What information does the system collect automatically?** Public wholesale price data (🟢 Agmarknet); Haversine distances computed from stored coordinates; the derived effective price $p^{eff}_{c,t}$ (from $p^{wh}_{c,t}$ and margin $m$); every candidate group generated; every cost/savings computation; every recommendation issued; timestamps and run logs for reproducibility (Section 22).

**4. What calculations happen automatically?** Demand aggregation and order-horizon enumeration; individual vs. collaborative cost; transport-tier lookup; $NetSavings_{g,c}(k)$ across feasible $k$; all four Phase 2A hard-constraint checks; Phase 2B's candidate generation (commodity filter → geographic graph → connected components → subset enumeration); Phase 2A's Stage 2 evaluation of every candidate; Phase 2B's overlap resolution/selection; explanation-text assembly.

**5. What recommendations does the system generate?** Per (commodity, price date, analysis-run timestamp — Sections 15–16, never presented as bare "today"): either a specific recommended group — members, order horizon $k^*$, aggregate quantity, the group's representative collection point, per-vendor cost allocation, $NetSavings$, and a plain-language explanation — or an explicit **"do not recommend collaboration"** with the specific disqualifying reason, for every commodity-relevant vendor not covered by a selected group.

**6. What decisions remain with the vendor?** Whether to actually join a recommended group; whether to accept the suggested order horizon and quantity; whether to transact with their trader on the implied terms; whether to trust or override an estimated (vs. observed) demand figure; whether to report an outcome. The system is decision support only (Phase 2A, Part 4) — it never forces or automates participation.

**7. What does the system explicitly NOT do?** No automatic ordering or payment processing; no autonomous negotiation with traders; no vehicle routing, dispatch, or real-time GPS tracking; no forced participation; no trained demand forecasting or deep learning in V1; no chat/negotiation platform; no credit or lending features; no dynamic real-time price-setting.

| Component | Responsibility | Input | Output |
|---|---|---|---|
| Frontend | Collect vendor/admin input, display recommendations and explanations | User actions, recommendation payloads | Rendered screens, submitted forms |
| Backend/API | Validate requests, orchestrate the pipeline, persist state | HTTP requests | HTTP responses, DB writes |
| Vendor Database | Store vendor, demand, group, and recommendation records | Validated records | Query results |
| Public Price Ingestion | Pull and store commodity price data | Agmarknet API responses | Stored 🟢 price records |
| Cold-Start Demand Estimator (CBR) | Estimate $r_{i,c}$ only for vendors lacking sufficient own history | Comparable-vendor records | 🟡 estimated $r_{i,c}$ |
| Optimization Engine | Run Phase 2B Stage 1 generation + Phase 2A Stage 2 evaluation + Phase 2B Stage 3 selection, unmodified | Vendor/price/param data | Selected groups, "do not recommend" list |
| Recommendation & Explanation Engine | Format optimization output into vendor-facing recommendations with reasons | Optimization output | Recommendation payload |
| Feedback/Logging | Capture outcomes and run metadata | Vendor feedback, run parameters | Logged records for reproducibility |

---

## 3. User & System Roles

| Role | Can View | Can Edit | Cannot Do |
|---|---|---|---|
| Vendor | Own profile, own demand history, recommendations addressed to them, group details they belong to | Own registration data, own demand entries, feedback on their own recommendations | View other vendors' raw data, override the optimization result, trigger a system-wide re-run |
| Researcher/Admin | All vendor and system data (for the pilot), price ingestion status, run logs | Experimental parameters ($D_{max}$, $F_c$, $m$, MOQ assumptions), vendor roster corrections, trigger a recommendation run | Fabricate or alter a computed recommendation directly (all edits must go through re-running the deterministic pipeline, to preserve auditability) |

This two-role model is deliberately minimal: a mini-project pilot with 10–20 vendors does not need role-based access control beyond "the person whose data it is" and "the person running the study."

---

## 4. System Modules

| Module | Required for V1? | Purpose | Input | Output |
|---|---|---|---|---|
| 1. Vendor Registration/Profile | Yes | Onboard a vendor, store static attributes | Name, category, commodities, coordinates | Vendor record |
| 2. Commodity & Demand Management | Yes | Record and update per-commodity demand | $r_{i,c}$ entries, updates | Demand records |
| 3. Location Management | Yes | Store and validate vendor coordinates | GPS input or manual entry | Validated $L_i$ |
| 4. Price Data Module | Yes | Ingest, store, and serve $p^{wh}_{c,t}$ | Agmarknet pulls | Price records |
| 5. Cold-Start Demand Estimation (renamed from "AI/ML Module") | Yes, but conditional — invoked only for vendors with insufficient own history (Section 9) | Deterministic case-matching estimate of $r_{i,c}$ (exact category/commodity/frequency-bucket match → median, with fallback hierarchy) | Comparable-vendor records | 🟡 Estimated $r_{i,c}$, tagged with fallback tier |
| 6. Candidate Group Generation | Yes | Phase 2B Steps 0–3 (commodity filter, compatibility graph, components, subsets) | $V_c$, coordinates | Candidate groups |
| 7 & 8. Constraint & Savings Evaluation Engine (merged) | Yes | Phase 2A Stage 2, called via Phase 2B Step 4 — evaluates feasibility and $NetSavings$ together, since Phase 2A computes them in one pass, not as separable steps | Candidate group, params | Feasibility flag, $k^*$, $NetSavings$ |
| 9. Overlap Resolution | Yes | Phase 2B Steps 5–6 — exact selection among feasible candidates | Feasible candidate pool | Selected disjoint groups |
| 10. Recommendation Engine | Yes | Assemble vendor-facing output + explanation | Selected/unselected candidates | Recommendation payload |
| 11. Vendor Dashboard | Yes | Present recommendations, savings, group details | Recommendation payload | Rendered UI |
| 12. Data Logging/Feedback Module | Yes | Capture outcomes, log every run for reproducibility | Vendor feedback, run metadata | Feedback + audit records |

**Consolidation applied:** the prompt's Modules 7 ("Constraint Evaluation Engine") and 8 ("Cost & Savings Engine") are merged into one module, because Phase 2A's Stage 2 model computes feasibility and $NetSavings$ in the same pass (its Part 23 decision rule) — implementing them as two separate services would introduce an artificial boundary the mathematics doesn't have. No module from the candidate list is dropped entirely; all twelve map to something V1 needs, once 7/8 are merged and Module 5 is renamed and scoped honestly.

---

## 5. Complete Architecture

The prompt's proposed skeleton (Frontend → Backend/API → Database → AI/ML Module → Optimization Engine → Recommendation Engine) is **modified in three ways**, per the audit in Section 6: (a) "Database" is split into the vendor database and the public price-ingestion path, since they have different sources, refresh cadences, and trust levels (🔵/🟡 vendor-entered vs. 🟢 public); (b) the "AI/ML Module" is renamed and made **conditional** — it is invoked only for cold-start vendors, not as an obligatory stage every request passes through; (c) a feedback/logging path is added back from the Recommendation layer into the database, since reproducibility (Section 22) requires every run to be recorded.

**Corrected layer order:**
```
Frontend
   ↓ (requests)
Backend/API
   ↓                              ↘
Vendor Database              Public Price Ingestion (Agmarknet)
   ↓                              ↙
Cold-Start Demand Estimation (conditional, CBR — Section 9)
   ↓
Optimization Engine (Phase 2B Stage 1 → Phase 2A Stage 2 → Phase 2B Stage 3, unmodified)
   ↓
Recommendation & Explanation Engine
   ↓
Frontend / Dashboard
   ↺ (feedback + run logs back to Database)
```

| Layer | Purpose | Responsibilities | Inputs | Outputs | Dependencies |
|---|---|---|---|---|---|
| Frontend | Vendor/admin interaction | Forms, dashboards, explanation display | User actions | API calls | Backend/API |
| Backend/API | Orchestration | Validation, routing, calling the pipeline in order | HTTP requests | HTTP responses | Database, Optimization Engine |
| Vendor Database | Persistence of vendor-side data | Store/query vendor, demand, group, recommendation, feedback records | Validated records | Query results | None (leaf layer) |
| Public Price Ingestion | Persistence of external data | Pull, store, timestamp Agmarknet prices | API responses | Price records | External Agmarknet API |
| Cold-Start Demand Estimation | Fill missing $r_{i,c}$ only when needed | Exact category/commodity/frequency-bucket matching, median, ordered fallback hierarchy (Section 9) | Comparable vendor records | 🟡 estimated $r_{i,c}$, tagged with fallback tier | Vendor Database |
| Optimization Engine | The decision core | Run Phase 2B's 7-step pipeline exactly as specified | Vendor/price/param data | Selected groups, non-selections with reasons | Vendor Database, Public Price Ingestion, (conditionally) Cold-Start Estimation |
| Recommendation & Explanation Engine | Vendor-facing packaging | Template-based explanation generation (Section 16), payload assembly | Optimization output | Recommendation payload | Optimization Engine |
| Feedback/Logging | Reproducibility and improvement signal | Store outcomes, store every run's parameters and inputs | Vendor feedback, run config | Audit trail | Vendor Database |

No layer is chosen for its own sake — every one maps to a module in Section 4, and none introduces a responsibility the mathematics or the "no fake AI" rule doesn't require.

---

## 6. AI/ML Opportunity Audit

### A. Demand Forecasting
Time-series forecasting of a vendor's future demand (per commodity) typically needs enough historical observations per series to detect a real pattern — weeks to months of regular records, ideally with enough history to separate signal from noise, per series, per vendor. Phase 1C's own data-collection timeline is only beginning; at 10–20 vendors with a short pilot window, most vendors will have at most a handful of demand entries per commodity when V1 is built. **Not justified for V1** — there is no way to validate a forecasting model (train/test split, cross-validation) with that little history without the test set being essentially the whole dataset. Minimum data that *would* justify it: several months of regular per-vendor, per-commodity demand records, ideally across a full seasonal cycle, so a genuine train/test split is possible. **🔴 REJECT for V1, 🟡 future work** once diary data accumulates over a longer operating period.

### B. Similarity-Based Demand Estimation
For a new or low-history vendor, comparing them to vendors who share the same category, commodity, and purchase-frequency bucket, and estimating $r_{i,c}$ from the matches, is a real and useful technique. **Is it ML?** Only in the loosest textbook sense (k-nearest-neighbors is sometimes classified as "instance-based learning"), but that classification presumes a validated similarity metric and enough held-out cases to check it generalizes — and at $n=10$–$20$, "validation" would mean leave-one-out testing on a sample too small to say anything statistically meaningful. **Correct classification: case-based reasoning (CBR), not machine learning.** This is exactly Phase 1C's original Layer 1 designation, reaffirmed here rather than revisited. **A revision made after review is worth flagging here:** an earlier draft of this component used a *weighted* multi-feature similarity score (category, commodity mix, quantity, operating days, location). That was retracted (Section 9) because the weights themselves would be an unjustified free parameter — nothing in the available data says category should count for more or less than location — and replaced with exact categorical matching (no weights needed, because there is nothing left to weight) plus a plain median. See Section 9–10 for the full, simplified specification.

### C. Demand Pattern Clustering
Unsupervised clustering of vendors' demand vectors to find "archetypes" (e.g., high-frequency small-batch vs. low-frequency bulk buyers) is statistically fragile at $n=10$–$20$: clusters over a dozen or two points are not robust to small data changes, and Phase 2B (Part 8) already established that generic clustering objectives have no awareness of the constraints or economics this system actually needs respected. There is also no established downstream use for such clusters in the decision pipeline — Phase 2A/2B's grouping logic is already exact and constraint-driven, not cluster-driven. **🔴 REJECT as a V1 production component.** It could appear as a purely descriptive, exploratory analysis in the eventual research write-up (e.g., "vendors appear to fall into N loose demand patterns") if the collected data supports it, but it would be a research aside, never part of the deployed decision system.

### D. Price Prediction
Agmarknet provides a genuinely large volume of historical daily/periodic price records across markets and commodities — data volume is **not** the limiting factor here, unlike A/C/E. But Phase 2A's model consumes the *current*, realized wholesale price $p^{wh}_{c,t}$ for a same/near-term collaboration decision — it does not have an open parameter for a *forecast* price, because the order-horizon decision $k$ is about how many days of demand to bundle *now*, not about whether to wait for a better price later. Building a price-forecasting model would therefore not feed anything the deterministic model actually uses. **🔴 REJECT for V1** — not for lack of data, but for lack of a role in the current decision problem. **🟡 FUTURE WORK**, specifically if the decision problem is later extended to include order-timing ("should the group wait two days for an expected price dip"), which is a genuinely different, larger research question than V1's scope.

### E. Recommendation Learning
Learning from historical accept/reject outcomes to improve future recommendations presumes (a) a decision that isn't already exactly computable, and (b) enough historical decisions to learn from. Phase 2B (Part 9) already established the recommend/don't-recommend decision is an exact deterministic function of known inputs — there is no unknown mapping to learn. Whether a vendor *chooses to act* on a recommendation is a different, behavioral question (already handled via Phase 1D's H6 participation-rate scenario stress-testing, not via ML), and a pilot with 10–20 vendors over a short window would produce at most a few dozen accept/decline events — far too few to train or validate any predictive model of adoption. **🔴 REJECT for V1, 🟡 far future work** only if the system runs for years across many more vendors and regions and accumulates real, large-sample acceptance-outcome data.

### F. Anomaly Detection
Flagging clearly wrong demand entries (e.g., a 50× jump with no explanation) or implausible price pulls (a data-ingestion glitch) is genuinely useful for data quality, and does **not** require a trained model — simple statistical bounds-checking (e.g., flag a value more than a few standard deviations from a vendor's own rolling average, or a price outside the recent historical range for that commodity/market) is enough, is easy to validate, and needs no training data beyond what is already being collected. **Decision: include a lightweight, explicitly non-ML, rule-based/statistical data-validation check in V1** (Section 20, failure handling) — it should never be labeled "AI/ML." A genuinely learned anomaly-detection model (e.g., isolation forest) is **🔴 REJECT for V1** on data-volume grounds, **🟡 future work** once enough volume exists to validate one.

---

## 7. AI/ML Feasibility Matrix

| AI/ML Idea | Data Required | Data Available? | Scientific Justification | V1 Feasibility | Decision |
|---|---|---|---|---|---|
| A. Demand forecasting (per-vendor time series) | Months of regular per-vendor, per-commodity history | 🔴 No — pilot just beginning (Phase 1C) | None at current data volume — cannot validate | Not feasible | 🔴 REJECT (🟡 future work) |
| B. Similarity-based demand estimation | A pool of comparable vendors' records (not per-vendor history) | 🟡 Partial — small pool, grows as pilot proceeds | Justified as **case-based reasoning**, not as ML | Feasible, at CBR scope only | 🟢 INCLUDE IN V1 (as CBR, not ML) |
| C. Demand pattern clustering | Enough vendors per cluster to be statistically robust | 🔴 No — $n=10$–$20$ too small | Not justified as a production component | Descriptive use only | 🔴 REJECT (production); optional exploratory research aside |
| D. Price prediction | Historical price series | 🟢 Yes — Agmarknet has ample history | Data-sufficient but **not needed** by the current decision model | Buildable but purposeless for V1 | 🔴 REJECT (🟡 future work if timing decisions are added) |
| E. Recommendation learning | Many historical accept/decline outcomes | 🔴 No — decision is already exact; outcomes will be a handful | Not justified — no unknown function to learn, no sample size | Not feasible | 🔴 REJECT (🟡 far future work) |
| F. Anomaly detection (statistical, not learned) | Ongoing demand/price entries (already collected) | 🟢 Yes, for simple bounds-checking | Justified as **rule-based/statistical validation**, not ML | Feasible at that scope | 🟢 INCLUDE IN V1 (as a data-quality check, not AI/ML) |

Two ideas are included in V1; neither is machine learning. This is the intended outcome of a strict audit, not a shortfall — it is the "no fake AI" rule doing its job.

---

## 8. Final AI/ML Decision

1. **Is ML genuinely possible in V1?** Not one that serves an actual, currently-open parameter in the deterministic model. A statistically valid model *could* be built (Section 6D, on Agmarknet's price history alone, decoupled from the small vendor count) — but "could be built" is not "is needed," and Strict Rule 1 forbids including it anyway.
2. **If yes, which exact problem does it solve?** N/A — no trained ML model is included in V1.
3–7. N/A for the same reason; see Section 10 for the honestly-labeled specification of the one component that *is* included (case-based reasoning), with each of these fields answered for that component instead, explicitly marked where "ML-shaped" fields don't apply to a non-trained method.
8. **Could additional data or a public dataset make one small ML component valid?** Investigated directly (Section 6D): yes, a defensible small ML model could be trained on Agmarknet's price history, since that data source has real volume independent of vendor count. It was not included, because it would not connect to any parameter Phase 2A's model leaves open — including it would be "ML for the project title's sake," which this phase's rules explicitly forbid. No training data has been or will be fabricated to manufacture a justification.

---

## 9. Selected AI/ML Component

**Name: Deterministic Case-Matching for Cold-Start Demand Estimation** (simplified in this revision from an earlier weighted-similarity design — see below). Used only when a vendor has insufficient own demand history for a commodity to compute $r_{i,c}$ directly.

**Matching rule — no weights, no tunable parameters:** find every other registered vendor who shares (a) the same vendor category, (b) the same commodity, and (c) the same declared purchase-frequency bucket (e.g., daily / a few times a week / weekly, captured once at registration — Section 12). Estimate $\hat{r}_{i,c}$ as the **median** $r_{i,c}$ among those exactly-matching vendors.

**Why the earlier weighted design was retracted:** the first draft matched vendors using a weighted combination of category, commodity mix, purchase quantity, operating days, and location. That requires answering "how much should each factor count?" — e.g., is category 40% and location 20%? — with no data or theory to justify any particular split. An unjustified weight is exactly the kind of free parameter this project's rules forbid inventing. Exact categorical matching removes the question entirely: there is nothing to weight, so there is nothing arbitrary to defend. **Location is deliberately excluded from the matching rule** — Phase 2A/2B's own geographic constraint already uses location for the thing it's suited to (which vendors can physically collaborate); reusing it here to estimate *how much* a vendor buys would be redundant and wouldn't improve the estimate. **Purchase quantity is also excluded as a matching feature** (an inconsistency in the earlier draft, caught and fixed here): using quantity to estimate quantity is circular for exactly the cold-start vendors this component exists to serve, since they are the ones who don't have a reliable quantity figure yet.

**Explicit, ordered fallback hierarchy** (so "no match" never means "no answer" or "an invented answer"): (1) match on category + commodity + frequency bucket, use the median; (2) if no vendor matches on all three, relax the frequency-bucket requirement and match on category + commodity only; (3) if still no match, use the median $r_{i,c}$ for that commodity across all vendors regardless of category, clearly labeled as a broad fallback; (4) if no vendor anywhere has recorded that commodity, exclude the vendor from grouping for that commodity and flag it for prioritized data collection rather than fabricate a figure. Every estimate is stored with which tier produced it (Section 13), so a researcher can see how reliable any given estimate actually is.

**Why this is not machine learning, stated plainly:** there is no training phase, no learned parameters — there is nothing left to learn once matching is exact and the estimate is a plain median — and no statistical claim of generalization to an unseen population. This matches Phase 1C's Layer 1 designation, and is more accurately described as **case-based reasoning**, a recognized (non-ML) technique from the broader AI literature — legitimate to cite as "AI-assisted," illegitimate to cite as "machine learning."

---

## 10. AI/ML Model Specification

Presented in the requested template, with fields marked **N/A** where they presume a trained model that this component, honestly, is not.

- **Problem Definition:** estimate $r_{i,c}$ for a vendor with insufficient own history, using data from vendors with adequate history.
- **Matching Features (categorical, exact-match only — no weights):** vendor category, commodity, declared purchase-frequency bucket. *(Two features from an earlier draft are deliberately dropped: "typical purchase quantity," because using quantity to estimate quantity is circular for exactly the cold-start vendors this serves; and "location," because Phase 2A/2B's geographic constraint already uses it for what it's suited to — which vendors can collaborate, not how much any one of them buys.)*
- **Target Variable:** N/A in the supervised-learning sense — there is no labeled "correct" $r_{i,c}$ to match against; the output is a case-matched median, not a prediction validated against ground truth.
- **Dataset:** the pool of other registered vendors' 🔵 real-primary demand records (grows as Phase 1C's data collection proceeds); no external or fabricated dataset is used.
- **Data Size:** whatever the current vendor pool provides — explicitly small (potentially single digits of exact-matching vendors per commodity at pilot start), which is precisely why Section 9's fallback hierarchy exists and why this is scoped as case-matching, not a validated statistical model.
- **Matching/Estimation Method:** exact categorical match on the three features above; if no vendor matches, Section 9's four-tier fallback hierarchy relaxes the criteria in a fixed, stated order. Output at whichever tier first finds a non-empty match set is the **median** $r_{i,c}$ among that tier's matches. **No weighting, no tunable similarity threshold, no training.**
- **Validation Strategy:** **Not a statistical validation** — no outcome-labeled dataset exists to validate against. The estimator is sanity-checked qualitatively (a researcher reviews which tier fired and whether the resulting matches look plausible for a sample of vendors) rather than scored against a held-out test set. This limitation is stated in the paper, not hidden.
- **Baseline Model:** folded into Section 9's fallback hierarchy itself (tiers 3–4 are the conservative fallback), rather than being a separate concept — there is no case where the estimator both fails to match and fails to fall back to something explicit.
- **Evaluation Metrics:** N/A in the ML sense; downstream sensitivity is instead handled by Phase 2A's own low/base/high demand-scenario framework (its Part 12/25) — i.e., the system reports how sensitive a recommendation is to the estimate being wrong, rather than claiming the estimate itself is validated.
- **Model Output:** a single estimated value, $\hat{r}_{i,c}$, tagged 🟡, along with which fallback tier produced it.
- **How the Output Enters the Optimization Pipeline:** exactly like an observed $r_{i,c}$ — Phase 2A's cost model does not distinguish observed from estimated demand mathematically, only in its data-quality tag (Section 12) and in which demand scenario (low/base/high) is used to stress-test the resulting recommendation.

**Adapted architecture** (the prompt's suggested diagram is not assumed correct, per its own instruction, and is revised accordingly):
```
Vendor's own demand records
        ↓ (sufficient history?)
   ── Yes → use observed r_i,c directly (🔵), no estimation needed
   ── No  → Comparable-vendor pool (🔵 records from other vendors)
                ↓
        Exact categorical match: category + commodity + frequency bucket
        (Section 9's fallback hierarchy relaxes criteria if no match)
                ↓
        Median r_i,c among matches → Estimated r_i,c (🟡), tagged with tier
                ↓
        Phase 2A/2B Optimization Engine (unmodified)
                ↓
        Final Recommendation
```

---

## 11. AI/ML–Optimization Interface

**Selected role: the estimator estimates one input parameter; it never makes or influences the recommend/don't-recommend decision.** This is Section 8, Part 8's first listed option, chosen deliberately over any alternative that would let an estimate bypass Phase 2A's constraint checks.

**Explicit safeguard against "ML making procurement decisions without constraint checking":** even though this component is not ML, the same discipline is enforced as if it were. An estimated $\hat{r}_{i,c}$ flows into Phase 2A's model exactly like an observed one — every hard constraint (procurement quantity, geographic, freshness/horizon, economic) is still checked in full by the deterministic Stage 2 model before any recommendation is issued (Phase 2A, Part 21). A bad estimate can therefore only ever produce a *rejected or suboptimal-looking* candidate (caught by the hard constraints, exactly as designed), never a silently-approved bad decision that skips verification. No estimate is ever allowed to set $y_{g,c,t}=1$ directly.

**Data-flow diagram:**
```
🔵/🟡 Vendor Demand Data
        ↓
🟦 Cold-Start Estimation (conditional; CBR, not ML)
        ↓ (estimated or observed r_i,c, tagged)
🟩 Phase 2A Deterministic Model — computes NetSavings, checks all 4 hard constraints
        ↓ (feasible candidates only)
🟨 Phase 2B Optimization — generation, then exact selection
        ↓
🟪 Recommendation & Explanation Engine
        ↓
🟪 Vendor Dashboard
```

---

## 12. Data Architecture

**A. Primary Vendor Data (🔵 real-primary, once collected per Phase 1C; 🟡 where estimated):** vendor ID, category, location (coordinates), commodities traded, purchase quantity ($r_{i,c}$), purchase frequency, current individual price paid ($p^{ind}_{i,c}$), confirmed MOQ (where the trader has stated one), practical procurement horizon ($H_{i,c}$).

**B. Public Data (🟢 real-public):** historical and current commodity wholesale prices (Agmarknet), used to derive $p^{eff}_{c,t}$.

**C. System-Generated Data:** candidate groups (Phase 2B), cost/savings calculations, feasibility flags, final recommendations, vendor feedback records, run logs.

**D. ML/CBR-Adjacent Data:** the comparable-vendor pool used by the cold-start estimator is simply a query over Category A data (no separate "training set" is stored, since nothing is trained) — the estimator reads the same vendor database, filtered to vendors with adequate history.

| Data Field | Source | Required For | Real / Estimated / Simulated |
|---|---|---|---|
| Vendor ID, category, commodities | Vendor registration | All modules | 🔵 Real |
| Location $L_i$ | Vendor registration (browser geolocation or manual survey entry — Section 14; no address geocoding) | Geographic feasibility, transport | 🔵 Real |
| Purchase-frequency bucket | Vendor registration (declared category: daily / a few times a week / weekly) | Cold-start case-matching (Section 9) | 🔵 Real |
| Demand $r_{i,c}$ | Vendor entry, or cold-start case-matching | Demand aggregation, cost model | 🔵 Real or 🟡 Estimated (tagged with fallback tier) |
| Individual price $p^{ind}_{i,c}$ | Vendor entry | Cost comparison | 🔵 Real |
| Confirmed MOQ | Vendor entry (only if trader-stated) | Procurement quantity constraint | 🔵 Real, absent if unconfirmed (Phase 2A Part 18) |
| Practical horizon $H_{i,c}$ | Vendor entry (purchase frequency / declared max interval) | Freshness/horizon constraint | 🔵 Real or 🟡 Assumption pending collection |
| Wholesale price $p^{wh}_{c,t}$ | Agmarknet API | Effective price, NetSavings | 🟢 Real Public |
| Margin $m$ | Researcher-set experimental parameter | Effective price | 🟡 Assumption, sensitivity-tested |
| $D_{max}$, $F_c$, transport tiers | Phase 1B/1C established parameters | Geographic/freshness/transport constraints | 🟡 Assumption, sensitivity-tested |
| Candidate groups, recommendations | System-generated | Dashboard, feedback | System-generated |
| Vendor feedback | Vendor entry, post-recommendation | Reproducibility, future research | 🔵 Real |

No field in this table is fabricated or simulated for production use; 🟠 simulated data is used only in offline scalability stress-tests (Phase 2B, Part 14), never in a real recommendation run.

---

## 13. Database Design

**Entities (minimal, no unneeded enterprise tables):**

- **Vendor** — PK `vendor_id`; attributes: name, category, coordinates (`lat`, `lon` — from browser geolocation or manual survey entry, Section 14), purchase-frequency bucket, registration date. Relationships: 1-to-many with DemandRecord, GroupMembership, Feedback.
- **Commodity** — PK `commodity_id`; attributes: name, freshness window $F_c$. Relationships: 1-to-many with DemandRecord, PriceRecord.
- **DemandRecord** — PK `demand_id`; FKs `vendor_id`, `commodity_id`; attributes: $r_{i,c}$, is_estimated (boolean), fallback_tier (1–4, null if not estimated — Section 9), date recorded, source tag (🔵/🟡).
- **PriceRecord** — PK `price_id`; FK `commodity_id`; attributes: $p^{wh}_{c,t}$, market, **price_date**, source (🟢).
- **ProcurementGroup** — PK `group_id`; FKs `commodity_id`, date; attributes: $k^*$, aggregate quantity, **`collection_point_lat`, `collection_point_lon`** (the group's representative collection point — see the terminology note below), $NetSavings$, feasibility flag, method (Proposed/Baseline 1/2/3, for experiment logging).
- **GroupMembership** — PK (`group_id`, `vendor_id`) composite; attributes: allocated cost, allocated savings. Join table between Vendor and ProcurementGroup.
- **Recommendation** — PK `recommendation_id`; FKs `group_id` (nullable, for "do not recommend" cases), `vendor_id`, **`run_id`** (the RunLog entry that produced it); attributes: outcome (recommend/do-not-recommend), reason text, **`price_date`** (from the PriceRecord used), **`analysis_run_timestamp`** (denormalized from RunLog, so a recommendation always displays its own timing without a join — Section 15/16).
- **Feedback** — PK `feedback_id`; FKs `recommendation_id`, `vendor_id`; attributes: accepted (boolean), outcome notes, timestamp.
- **RunLog** — PK `run_id`; attributes: timestamp, parameter snapshot ($D_{max}$, $F_c$, $m$, etc.), method compared, for reproducibility (Section 22).

This is a small relational schema — nine tables, all directly traceable to a module in Section 4. No microservice-style data partitioning, no separate analytics warehouse, no user-permission tables beyond the two roles in Section 3.

**Terminology correction applied in this revision:** the group's meeting point is named `collection_point` in every database field and every piece of user-facing/software language in this document, not "centroid" — a mathematical centroid can land in the middle of a road or somewhere otherwise inaccessible, so the operational name should describe what it actually is: a representative point vendors can physically meet at. **This does not yet extend to Phase 2A/2B's own mathematical notation**, which still defines and uses the term "centroid" throughout their formulas (verified directly in both files while making this correction) — the rename requested was believed already made there, but it was not. Phase 3's software layer can consistently call the *same* computed point "the representative collection point" without changing Phase 2A/2B's math, but if full terminology consistency down to the formulas themselves is wanted, that requires a further, separate correction pass on those two documents — flagged for you to confirm before it's done, since it touches already-approved mathematical notation, not just naming.

---

## 14. Backend/API Responsibilities

| Operation | Input | Processing | Output |
|---|---|---|---|
| `POST /vendor` | Registration fields, including submitted latitude/longitude | Validate; store the submitted coordinates as-is (from the vendor's browser/device location permission, or entered manually during in-person survey onboarding) — **no automatic address-to-coordinate geocoding is performed** | Vendor record |
| `POST /demand` | Vendor ID, commodity, $r_{i,c}$ | Validate, run Section 6F's statistical bounds-check, store (or flag) | Confirmation / flag |
| `GET /prices` | Commodity, date range | Query stored Agmarknet records (or trigger ingestion if stale) | Price records |
| `POST /recommendations/generate` | Commodity, date, (optionally) method to run | Invoke cold-start estimation as needed → Optimization Engine (Phase 2B Steps 0–6) → Recommendation Engine | Recommendation set, persisted |
| `GET /recommendations` | Vendor ID or group ID | Query stored recommendations | Recommendation payload with explanation |
| `POST /feedback` | Recommendation ID, accepted flag, notes | Validate, store | Confirmation |
| `GET /runlog` (admin only) | Date range | Query RunLog for reproducibility/audit | Run metadata |

Framework syntax is intentionally left open (Section 18 recommends FastAPI); these are responsibilities, not a finalized route spec.

---

## 15. Frontend Design

| Screen | User Input | Data Displayed | Action Available |
|---|---|---|---|
| Vendor Registration | Name, category, commodities, purchase-frequency bucket, location (captured via browser geolocation permission, or entered manually if onboarding in person — no address geocoding) | Confirmation | Submit, edit before confirming |
| Vendor Profile | — | Registered details, demand history | Edit demand/location |
| Demand Entry | Commodity, quantity, (optional) MOQ/horizon | Recent entries | Submit, correct a prior entry |
| Recommendation Dashboard | — | Recommendation(s) shown with explicit **commodity, price date, and analysis-run timestamp** (never presented as bare "today"), or "no recommendation" with reason | View group details |
| Group Details | — | Members, $k^*$, aggregate quantity, representative collection point, allocation | Accept / decline |
| Savings Comparison | — | Individual vs. collaborative cost, Total Net Savings (primary metric, Section 18 of Phase 2B) — Feasibility Rate never surfaced to vendors, only used internally as a research diagnostic | — |
| Recommendation Explanation | — | Plain-language reason (Section 16) | — |

No admin panel beyond what Section 3's Researcher/Admin role needs (roster management, parameter configuration, run triggering) — this is deliberately not built as a general-purpose admin console. **A usability note flagged as 🟡, not yet validated:** street-vendor users may have variable smartphone literacy; V1 should favor simple numeric/visual layouts over dense text and keep language strings configurable (not hardcoded to one language), but no specific literacy assumption is asserted without field validation.

---

## 16. Recommendation & Explainability Design

**Chosen approach: template-based, not AI-generated.** Every number in a recommendation is already computed exactly by Phase 2A's deterministic model — there is nothing for a generative model to infer, and using one would introduce hallucination risk and non-reproducibility for zero benefit, directly conflicting with Section 22's reproducibility goal. A small set of rule-selected templates, filled with the exact computed values, is the simplest defensible approach and is fully auditable.

**Every explanation is prefixed with its commodity, the price date it used, and the analysis-run timestamp — never presented as a bare "today"**, since price ingestion and recommendation runs are periodic batch events, not continuous ones (Section 22's `RunLog`, Section 13's `analysis_run_timestamp`).

**Example templates:**
- Recommend: *"For {commodity} (price date: {price_date}; analysis run: {analysis_run_timestamp}) — collaboration is recommended: joining this group of {n} vendors and ordering a {k}-day supply together is estimated to save you ₹{savings} after transport costs, compared to procuring alone."*
- Not recommended — economic: *"For {commodity} (price date: {price_date}; analysis run: {analysis_run_timestamp}) — collaboration is not recommended: the transport cost for a feasible group exceeds the expected savings."*
- Not recommended — geographic: *"For {commodity} (price date: {price_date}; analysis run: {analysis_run_timestamp}) — no sufficiently nearby vendors were found within the collaboration distance."*
- Not recommended — freshness/horizon: *"For {commodity} (price date: {price_date}; analysis run: {analysis_run_timestamp}) — a collaborative order would need to be held longer than the commodity's practical freshness/storage limit allows."*
- Not recommended — quantity: *"For {commodity} (price date: {price_date}; analysis run: {analysis_run_timestamp}) — the nearby group's combined order does not meet your trader's minimum order quantity."*

Template selection follows Phase 2A's constraint-check trace directly (its Part 21 order: quantity → geographic → freshness/horizon → economic), so the explanation always names the actual first constraint that failed, not a generic refusal.

---

## 17. End-to-End Data Flow

```
Vendor Input (registration, demand, MOQ if known)         🔵/🟪
        ↓
Data Validation + Statistical Anomaly Check (Section 6F)   🟪
        ↓
Database                                                    🟪
        ↓
Cold-Start Estimation (only if history insufficient)        🟦 (CBR, not ML)
        ↓
Commodity Filtering                                          🟨
        ↓
Geographic Pre-filter (necessary condition only)             🟨
        ↓
Candidate Group Generation                                   🟨
        ↓
Constraint & Savings Evaluation (Phase 2A, unmodified)        🟩
        ↓
Overlap Resolution / Selection                                🟨
        ↓
Recommendation + Explanation                                  🟪
        ↓
Dashboard                                                      🟪
        ↓
Feedback / Data Logging → back to Database                    🟪
```

This matches the prompt's sketch with two corrections: the AI/ML step is explicitly marked conditional and non-ML, and a statistical validation step is added right after vendor input (Section 6F), since that is the cheapest point to catch a bad entry before it propagates through the whole pipeline.

---

## 18. Technology Stack

| Layer | Recommended Technology | Why | Alternative |
|---|---|---|---|
| Frontend | React, calling the FastAPI backend over HTTP | Presents as a genuine full-stack web application — matching the project's own stated "Full-Stack + AI/ML" goal — rather than a Python research dashboard; keeping it a separate client from the backend also preserves the Frontend → Backend/API → Database layering this document specifies (Section 5), which a dashboard reading the database directly would quietly bypass | Plain HTML/CSS/JavaScript with `fetch` calls to the same API, if React's tooling overhead doesn't fit the timeline — **not** Streamlit, which was reconsidered and dropped as a recommendation for exactly the reason above |
| Backend | FastAPI | Modern, well-documented, async-capable, easy for a student to pick up, plays well with Python's data/optimization libraries | Flask, if simplicity and ubiquity of tutorials matter more |
| Database | SQLite | Zero-config, file-based, perfectly sized for 10–20 vendors, trivially versioned/shared for reproducibility | PostgreSQL, if the pilot later needs concurrent multi-user writes |
| AI/ML (case-matching component) | Plain Python/Pandas — group by category, commodity, and frequency bucket, take the median | Deliberately the simplest possible implementation: exact categorical matching plus a median has no library dependency worth adding, and full transparency matters more than convenience here | None needed — there is no similarity metric or weighting left to implement with a library (Section 9) |
| Optimization | NetworkX (graph/connected components) + Python `itertools` (subset enumeration and brute-force selection) | Free, well-documented, exactly matches Phase 2B's specified algorithm with no solver dependency | PuLP or Google OR-Tools, documented as the exact ILP fallback if candidate-pool sizes ever grow (Phase 2B, Part 14) |
| Maps/Distance | Haversine formula computed directly in Python, over coordinates the vendor supplies at registration (browser geolocation permission, or manual entry during in-person survey onboarding, Section 14) | Phase 2A already establishes straight-line distance, not routed distance — no geocoding API is needed for V1 at all | OpenStreetMap Nominatim (free), only if address-based entry is ever needed instead of direct coordinates — not the V1 default |
| Deployment | Local demonstration + free-tier hosting (Render/Railway free tier for the FastAPI+SQLite backend, Vercel/Netlify or GitHub Pages free tier for the React or plain-HTML frontend) | Matches a mini-project's scale and budget; no infrastructure to maintain | None needed — Docker/Kubernetes/cloud infra would be solving a scaling problem this project does not have |

Every choice satisfies "student-friendly, free/low-cost, easy integration, suitable for V1, research-reproducible" — none is chosen for being fashionable.

---

## 19. System Security & Data Privacy

**What is stored:** vendor name/ID, category, coordinates (static, recorded at registration — not continuously tracked), commodities and quantities, contact information needed for pilot coordination, price data (public). **What is not collected:** no payment or banking details (the system never processes payments, Section 21), no continuous/real-time location tracking, no data beyond what a specific module in Section 4 actually consumes.

**Minimum privacy requirements:** informed consent from each participating vendor before data collection (standard for primary-data academic research, per Phase 1C); data minimization (store only fields listed in Section 12); no third-party sharing of vendor-identifying data; contact information visible only to the researcher/admin role, never to other vendors.

**Authentication:** a lightweight scheme appropriate to the pilot's scale — e.g., a phone number plus a simple PIN or one-time code — rather than enterprise SSO or complex password policies, which would be disproportionate for 10–20 known, personally-onboarded participants.

---

## 20. Failure Handling

| Failure | System Response |
|---|---|
| Missing vendor data (e.g., no location) | Vendor excluded from geographic pooling until corrected; flagged to admin, not silently guessed |
| Invalid location (outside plausible study area) | Rejected at input validation (Section 17); admin notified |
| Missing price data (Agmarknet pull fails/stale) | That commodity's recommendation run is skipped for the day, logged, and retried; never silently substituted with a guessed price |
| No feasible group exists | Every affected vendor receives an explicit "do not recommend" with reason (Phase 2B, Part 15 Step 7) — this is correct, expected behavior, not an error |
| Negative or zero net savings | Group is correctly evaluated as infeasible by Phase 2A's economic constraint; no recommendation issued |
| Insufficient data for cold-start estimation (no comparable vendors) | Fall back to the conservative default (Section 10's baseline) or exclude the vendor from grouping for that commodity, flagged for prioritized data collection |
| Optimization engine failure (e.g., malformed input) | Run aborted, logged with full input snapshot (Section 22), no partial/incorrect recommendation issued |
| Statistical anomaly flagged (Section 6F) | Entry held for admin review before entering the pipeline, vendor notified to confirm |

The consistent principle: every failure produces an explicit, logged non-result rather than a silently wrong or fabricated one.

---

## 21. V1 vs. Future System

**V1 (actually implemented):** vendor registration and demand entry; Agmarknet price ingestion; the cold-start CBR estimator (not ML); Phase 2B's exact candidate generation and selection pipeline; Phase 2A's exact Stage 2 evaluation; template-based explanations; a simple dashboard; feedback logging; the lightweight stack in Section 18; SQLite-scale data (10–20 vendors).

**Future Work (explicitly not built now):** trained demand forecasting once sufficient longitudinal data exists (Section 6A); real-time or predictive price modeling (Section 6D); a learned recommendation-adoption model (Section 6E); a trained anomaly detector (Section 6F); supplier/trader-side platform integration; dynamic vehicle routing; payment integration; large-scale optimization beyond ~20–50 vendors (Phase 2B, Part 14's documented ILP/spatial-indexing upgrade path); multi-region or multi-hub logistics (Phase 2A, Part 28).

No future item has been smuggled into the V1 scope above; every V1 item traces to a module in Section 4 that is buildable with the stack in Section 18 by a single student in a mini-project timeframe.

---

## 22. Research Reproducibility

**Fixed datasets:** the calibrated scenario grid already established in Phase 1C (its Section 12) is used for all reported experiments, alongside real vendor data as it becomes available (Phase 1C timeline) — results are never generated from ad hoc, unlogged inputs.

**Configuration parameters, versioned:** $D_{max}$, $F_c$, margin $m$, MOQ assumptions, and the CBR estimator's $k$ (number of neighbors) are stored in a single version-controlled config file per experiment run, not hardcoded inline, so a reported result can be traced back to the exact parameter set that produced it.

**Scenario assumptions:** every 🟡 experimental assumption (Section 12's table) is documented alongside the config file it lives in, with its source (e.g., "Phase 1B, Section 7").

**Random seeds:** the production pipeline is fully deterministic (Phase 2A/2B are exact, not stochastic) and needs no seed. A fixed seed **is** required for the one place randomness appears: synthetic vendor sets generated to stress-test scalability beyond the real pilot's size (Phase 2B, Part 14's $n=50/100/1000$ analysis).

**Versioned datasets and experiment logs:** every recommendation run is written to the `RunLog` table (Section 13) with a timestamp and full parameter snapshot; raw and derived datasets used for a reported result are saved as versioned files (e.g., `data/v1_2026-09-13.csv`) rather than overwritten in place.

**Minimum reproducibility setup for V1:** a config file, a `RunLog` table, and versioned data snapshots are sufficient at this scale — no experiment-tracking platform (e.g., MLflow) is needed for a system with no trained models to track.

---

## 23. Complete Architecture Diagram

```
┌──────────────────────────┐
│     VENDOR FRONTEND       │  🟪
└─────────────┬─────────────┘
              ↓
┌──────────────────────────┐
│       BACKEND/API         │  🟪
└─────────────┬─────────────┘
              ↓
       ┌──────┴──────┐
       ↓             ↓
┌─────────────┐ ┌───────────────────┐
│   VENDOR    │ │  PUBLIC PRICE DATA │   🟪 / 🟢
│  DATABASE   │ │   (Agmarknet)      │
└──────┬──────┘ └─────────┬──────────┘
       └──────┬───────────┘
              ↓
┌───────────────────────────────────┐
│ COLD-START DEMAND ESTIMATION       │  🟦
│ (Case-Based Reasoning — NOT ML;    │
│  invoked only when needed)         │
└─────────────┬───────────────────────┘
              ↓
┌───────────────────────────────────┐
│ OPTIMIZATION ENGINE                 │  🟩 + 🟨
│ Phase 2B Stage 1 (generation) →     │
│ Phase 2A Stage 2 (evaluation) →     │
│ Phase 2B Stage 3 (selection)        │
└─────────────┬───────────────────────┘
              ↓
┌───────────────────────────────────┐
│ RECOMMENDATION + EXPLANATION        │  🟪
│ (template-based)                    │
└─────────────┬───────────────────────┘
              ↓
┌──────────────────────────┐
│     VENDOR DASHBOARD      │  🟪
└─────────────┬──────────────┘
              ↺ feedback + run logs → VENDOR DATABASE
```

The only substantive change from the prompt's skeleton is labeling the AI/ML box honestly (case-based reasoning, conditional, not ML) and splitting "Database" into vendor vs. public sources — everything else follows the given shape.

---

## 24. Architecture Quality Audit

1. **Does every module have a purpose?** Yes — Section 4 maps all twelve prompted modules (after merging 7/8) to a concrete role; none is speculative.
2. **Is the AI/ML component scientifically justified?** Yes, as case-based reasoning for cold-start estimation — but note the honest answer is that *no ML component* is included, which is itself the scientifically justified outcome of Section 6's audit.
3. **Is ML actually implemented if claimed?** No ML is claimed. The one AI-adjacent component is explicitly and consistently labeled CBR, not ML, everywhere it appears (Sections 1, 6, 9, 10, 17, 23).
4. **Does ML have sufficient data?** N/A — no ML is included; the CBR component's data sufficiency is addressed on its own terms in Section 10 (small, growing, not statistically validated, and stated as such).
5. **Does the optimization engine remain deterministic and explainable?** Yes — Phase 2A/2B are used completely unmodified; nothing in this phase alters their logic.
6. **Consistent with Phase 2A?** Yes — Section 11's safeguard, Section 16's explanation logic, and Section 13's schema all trace directly to Phase 2A's Parts 4, 18, 21, 23.
7. **Consistent with Phase 2B?** Yes — Section 4/5/17 reproduce Phase 2B's 7-step pipeline and its "necessary condition, not feasibility guarantee" caveat for geographic pooling exactly as corrected in that phase's review.
8. **Is V1 realistically buildable?** Yes — Section 18's stack is free, well-documented, and matches a single student's skill/time budget; Section 13's schema is nine small tables.
9. **Are unnecessary technologies avoided?** Yes — no microservices, no GPU/ML infra, no enterprise auth, no paid maps API (Section 18/19/21 all state this explicitly).
10. **Can the system be demonstrated clearly?** Yes — a live React (or plain HTML/CSS/JS) frontend calling the FastAPI backend and showing a recommendation with its explanation and timestamps is a natural, understandable demo for 10–20 vendors, and reads as a genuine full-stack application rather than a Python-only dashboard.
11. **Can experiments be reproduced?** Yes — Section 22's config files, `RunLog` table, and versioned datasets are sufficient given there is no trained model to version.
12. **Is the AI/ML + full-stack positioning honest?** Yes — this is the section this whole phase exists to get right, and the answer is that the honest positioning is "AI-assisted via case-based reasoning, deterministic optimization otherwise," not "AI/ML-powered."

No issue found in this audit requires a structural redesign.

---

## 25. Exact V1 Implementation Scope

A student building this system implements, in order: (1) the vendor/commodity/price database schema (Section 13); (2) registration (with browser-geolocation or manual coordinate entry, no geocoding), demand-entry, and price-ingestion endpoints (Section 14); (3) the cold-start case-matching estimator as a small, transparent grouping-and-median function, not a trained model (Section 10); (4) Phase 2B's candidate-generation code (commodity filter, Haversine-threshold graph, connected components via NetworkX, subset enumeration via `itertools`); (5) Phase 2A's Stage 2 evaluation as a pure function called on each candidate; (6) brute-force selection among feasible candidates (Phase 2B, Part 15 Step 6); (7) template-based explanation generation with explicit price-date/run-timestamp fields (Section 16); (8) a React (or plain HTML/CSS/JS) frontend that calls the backend API for recommendations and explanations — never reading the database directly, preserving Section 5's layering; (9) feedback capture and run-logging for reproducibility. Nothing on this list requires infrastructure beyond a laptop and free-tier hosting.

---

## 26. Final Verdict

**🟡 ARCHITECTURE APPROVED WITH REQUIRED CORRECTIONS — corrections applied in this revision; one item (the AI/ML question) is deliberately left open for a dedicated follow-up audit rather than decided unilaterally here.**

**Five review items, resolved in this revision:**
1. **CBR similarity weights were arbitrary** — fixed by replacing the weighted multi-feature similarity score with exact categorical matching (category, commodity, frequency bucket) plus a median, and an explicit ordered fallback hierarchy (Sections 6B, 9, 10). Nothing is weighted anymore, so nothing needs justifying.
2. **"Centroid" terminology** — fixed throughout this document: database fields, output descriptions, and screen content all now say "representative collection point" / `collection_point`, never "centroid" (Section 13). **Important honest correction to the record:** Phase 2A and Phase 2B's own mathematical formulas still use "centroid," verified directly while making this fix — the rename had not actually been made there, contrary to what was believed. Extending it into their notation is a separate, larger edit and is flagged for your decision, not assumed.
3. **Streamlit vs. a genuine full-stack frontend** — fixed: the default recommendation is now React (or plain HTML/CSS/JS) calling the FastAPI backend over HTTP, not Streamlit reading the database directly, which would also have quietly broken this document's own layering (Section 18, Section 5).
4. **Geocoding underspecified** — fixed: `POST /vendor` now explicitly takes vendor-supplied coordinates (browser geolocation or manual survey entry) and performs no address-to-coordinate geocoding; Nominatim is listed only as a fallback, not the default (Sections 14, 18).
5. **"Today's recommendation" overstated real-time-ness** — fixed: every recommendation and explanation now carries an explicit commodity, price date, and analysis-run timestamp (Sections 13, 15, 16), and the database schema was extended (`price_date`, `analysis_run_timestamp`, `run_id`) to support it.

**One item deliberately not resolved here — the AI/ML question:** whether this project's evaluator requires a literal trained/validated ML model, or accepts a well-justified "AI-assisted" framing built on case-based reasoning and exact optimization, is a fact about your specific academic requirement that only you can supply — this document cannot resolve it by asserting an answer. What this phase *can* and does state honestly: the architecture above is internally consistent and complete either way, and a Phase 3A audit (proposed by you, not yet begun) can investigate whether one small, genuinely justified ML component — most promisingly built on Agmarknet's price history, since that is the one data source with real volume independent of vendor count — can be added without violating this project's own "no fake AI" rule. Section 6D's original finding (that a price-forecasting model doesn't feed a parameter Phase 2A currently uses) still stands as of this revision; Phase 3A's job would be to determine whether a different framing of the decision problem, or a different ML target on public data, changes that conclusion, not to override it by assumption.

**What Phase 4 inherits, once Phase 3A resolves:** a complete module list (Section 4), a corrected layer architecture (Section 5), a fully specified non-ML case-matching component (Sections 9–11) that stands on its own regardless of Phase 3A's outcome, a minimal database schema with the terminology and timestamp corrections applied (Section 13), an API surface (Section 14), a revised technology stack (Section 18), and an honest V1/future-work boundary (Section 21).

**What remains open, as scheduled dependencies, not design defects:** (a) real vendor data collection (Phase 1C's timeline) is still in progress — until enough vendors are onboarded, the system will be built and demonstrated against the calibrated scenario grid (Phase 1C, Section 12); (b) the AI/ML question above, pending Phase 3A and your confirmation of the actual academic requirement; (c) whether to extend the "representative collection point" rename into Phase 2A/2B's mathematical notation, pending your decision.
