# 📂 RESEARCH AUDIT FILE — PHASE 1C
### Primary Data Collection & Dataset Feasibility Audit
**Subject:** An AI-Assisted, Freshness- and Logistics-Aware Collaborative Procurement Decision Platform for Street Vendors
**Question this phase answers:** Can enough reliable data realistically be obtained, within a mini-project timeframe, to build and evaluate this system on a scientifically defensible foundation?

**Data labeling used throughout:** 🟢 REAL PUBLIC DATA · 🔵 PRIMARY DATA TO BE COLLECTED · 🟡 EXPERIMENTAL ASSUMPTION · 🟠 SYNTHETIC/SIMULATED DATA

---

## 1. Executive Summary

**Verdict: 🟡 DATA FEASIBLE WITH LIMITATIONS.**

There is a realistic, scientifically defensible data foundation for this project — but it does not support what the earlier design drafts implied. The most important finding of this phase is about the AI/ML component specifically: **traditional supervised ML (Random Forest/LightGBM-style per-vendor demand forecasting, as proposed in earlier drafts) is not well justified on a 10–20 vendor, 7–14 day dataset.** At that scale you get roughly 70–280 vendor-day observations spread across several commodities and vendor categories — too sparse, especially per commodity per vendor, to train and validate a generalizable supervised model without serious overfitting risk.

This is not a reason to abandon intelligence in the system — it is a reason to be precise about where the intelligence actually lives, across three distinct layers, rather than labeling a simple average "our AI model" and hoping it holds up under questioning. **Layer 1 (Demand Estimation)** for cold-start vendors is similarity-based/case-based reasoning — finding a handful of comparable vendors and estimating from their behavior. This is a legitimate, citable technique family, but it should be presented for what it is (a lightweight case-based reasoning method), not oversold as the project's headline "AI." A judge who asks "where is the AI?" after hearing "our AI model uses category averages" has a fair point. **Layer 2 (Predictive Learning)** — a properly trained ML forecasting model — is architecturally supported and explicitly planned for, but deferred to future work once the platform accumulates real transaction history; V1 must not claim this layer is trained or validated on the small field dataset. **Layer 3 (Optimization Intelligence)** — the constrained decision engine that weighs demand, price, transport, and freshness together to decide whether, with whom, and how much to procure — is the project's real intelligence and its strongest, most defensible research contribution, and it does not depend on Layer 2 existing yet.

The second important finding is encouraging and reinforces the point above: **the optimization/batching engine (Layer 3) is not data-starved the way an ML model would be.** Constrained optimization works on parameter ranges (price, cost, quantity, shelf-life), not on hundreds of labeled training examples, so it can be meaningfully evaluated using the hybrid real + primary + calibrated-synthetic data this project already plans to assemble, independent of the ML sample-size problem above — and it should be positioned as the centerpiece of the project, not the demand estimator.

Public data for market prices, transport cost benchmarks, and (partially) shelf life is real and accessible, consistent with Phase 1A/1B findings — though Agmarknet wholesale price and actual vendor procurement price (primary data) should be prioritized over Price Monitoring System retail data, which is optional secondary context (see Section 3, C2). Vendor-specific demand, procurement price, and payment behavior remain primary-data-only, as already established. Geographic distance calculation has a free, adequate, zero-dependency option for this scale (the Haversine formula on approximate, anonymized vendor coordinates — not locality names alone, see Section 3, C4) — there is no need for a paid mapping API. Weather data is technically available but should be excluded from V1 on scientific grounds (overfitting risk at this sample size), not because it doesn't exist.

**Bottom line: yes, there is a realistic path — provided the project's claims are scoped to match a small, non-random field sample (exploratory case study / prototype-evaluation framing, not statistical generalization), and provided the AI/ML narrative is presented as the three-layer architecture above, with the optimization engine — not category-average estimation — carried as the project's actual intelligence claim.**

---

## 2. Complete Data Requirements Matrix

### A1. Vendor Profile Data

| Variable | Why Needed | Used For | Public Data? | Primary Data Required? | Can Be Estimated? | Reliability | V1 Priority |
|---|---|---|---|---|---|---|---|
| Anonymous vendor ID | Link records across tables without identifying individuals | All linked analysis | No | 🔵 Yes (assigned by researcher) | N/A | High | 🟢 Must have |
| Vendor category (tea stall, chaat, fruit cart, etc.) | Cold-start category grouping | Cold-start estimation, clustering | No | 🔵 Yes | No | High | 🟢 Must have |
| Approximate operating area/locality | Geographic clustering | Grouping, distance calc | No | 🔵 Yes | No | Medium (self-reported) | 🟢 Must have |
| Operating days (daily/weekdays/etc.) | Determines valid demand-observation days | Demand modeling | No | 🔵 Yes | No | High | 🟡 Should have |
| Type of products sold (beyond category) | Refines commodity relevance | Commodity selection per vendor | No | 🔵 Yes | Partially, from category | Medium | 🟡 Should have |
| Exact operating hours | Fine-grained scheduling | Not needed for V1 decision logic | No | 🔵 Yes | N/A | Low value for V1 | 🔵 Nice to have |

### A2. Procurement Behaviour

| Variable | Why Needed | Used For | Public Data? | Primary Data Required? | Can Be Estimated? | Reliability | V1 Priority |
|---|---|---|---|---|---|---|---|
| Commodity purchased | Core unit of analysis | Everything | No | 🔵 Yes | No | High | 🟢 Must have |
| Quantity purchased | Demand magnitude | Break-even, forecasting | No | 🔵 Yes | No | Medium (recall bias risk) | 🟢 Must have |
| Unit of measurement | Normalization | All quantitative analysis | No | 🔵 Yes | No | Low unless normalized (see K2) | 🟢 Must have |
| Purchase frequency | Demand cadence | Forecasting, diary design | No | 🔵 Yes | No | Medium | 🟢 Must have |
| Purchase date | Time-series structure | Diary analysis | No | 🔵 Yes (diary) | No | High if diary, low if recalled | 🟢 Must have |
| Approximate price paid | THE key variable — vendor's real procurement price, distinct from consumer retail price (per Phase 1B) | Core cost-comparison baseline | No | 🔵 Yes | No — this is exactly what must NOT be estimated from PMS consumer data | High priority, moderate reliability (recall bias) | 🟢 Must have |
| Procurement source (wholesaler/agent/retailer/mandi) | Distinguishes cash-retail vs. credit/advance buyers (per Phase 1A's 48% finding) | Segmenting the price baseline | No | 🔵 Yes | No | Medium | 🟢 Must have |
| Supplier type | Related to above | Same | No | 🔵 Yes | Partially overlaps with source | Medium | 🟡 Should have |
| Distance to source | Logistics baseline | Transport-cost sanity check | No | 🔵 Yes (approximate) | Roughly, via Haversine if source location known | Low-medium | 🟡 Should have |
| Delivery availability from current supplier | Baseline comparison for the proposed platform | Context for payment/logistics design | No | 🔵 Yes | No | Medium | 🔵 Nice to have |

### A3. Demand Information

| Variable | Why Needed | Used For | Public Data? | Primary Data Required? | Can Be Estimated? | Reliability | V1 Priority |
|---|---|---|---|---|---|---|---|
| Typical daily consumption (per commodity) | Core demand baseline | Break-even translation, forecasting | No | 🔵 Yes | No | Medium (many vendors won't know exactly — ask in ranges, see Section 6) | 🟢 Must have |
| Quantity per transaction | Purchase-batching behavior | Understanding current behavior | No | 🔵 Yes | Partially derivable from consumption + frequency | Medium | 🟡 Should have |
| Demand variability (day to day) | Justifies uncertainty-aware ordering | Newsvendor-style logic | No | 🔵 Yes (only if diary run) | No — a one-time survey cannot capture this | Low from survey, Medium from diary | 🟡 Should have (diary-dependent) |
| Busy days / weekly pattern | Day-of-week feature | Forecasting feature | No | 🔵 Yes | No | Medium | 🔵 Nice to have |
| Seasonal changes | Longer-term pattern | Future work | No | 🔵 Yes (requires months, out of scope) | No | N/A for mini-project | 🔵 Nice to have (out of V1 scope) |
| Event-related demand spikes | Edge-case handling | Future work | No | 🔵 Yes | No | N/A for mini-project | 🔵 Nice to have (out of V1 scope) |

### A4. Logistics Information

| Variable | Why Needed | Used For | Public Data? | Primary Data Required? | Can Be Estimated? | Reliability | V1 Priority |
|---|---|---|---|---|---|---|---|
| Approximate vendor location | Clustering, distance calc | Grouping engine | No | 🔵 Yes — approximate stall coordinates (lat/long), not just a locality name (see Section 3, C4) | No | Medium | 🟢 Must have |
| Procurement source location | Same | Transport-cost sanity check | Partially (mandi locations are public) | 🔵 For informal suppliers | Partially | Medium | 🟡 Should have |
| Transport method currently used | Context | Payment/logistics design | No | 🔵 Yes | No | Medium | 🟡 Should have |
| Transport cost currently paid (if any) | Baseline | Individual-cost model refinement | No | 🔵 Yes | Partially, from Phase 1B benchmarks | Low-medium | 🟡 Should have |
| Delivery availability (current) | Context | Same | No | 🔵 Yes | No | Medium | 🔵 Nice to have |
| Pickup feasibility for a hypothetical group order | Design validation | Payment/logistics design | No | 🔵 Yes | No | Medium | 🟡 Should have |

### A5. Payment Behaviour

| Variable | Why Needed | Used For | Public Data? | Primary Data Required? | Can Be Estimated? | Reliability | V1 Priority |
|---|---|---|---|---|---|---|---|
| Cash vs. UPI vs. credit/supplier-advance | Directly tests Phase 1A's payment/trust finding | Payment-model selection (Phase 1B Section 13) | No | 🔵 Yes | Partially from WIEGO/Bhowmik (🟢 general finding, not vendor-specific) | Medium | 🟢 Must have |
| Typical payment timing (immediate vs. after sale) | Same | Same | No | 🔵 Yes | Same | Medium | 🟢 Must have |
| Exact amounts owed/credit limits | Not needed and sensitive | — | No | Not required | — | — | ❌ Do not collect |

### A6. Collaborative Procurement Behaviour

| Variable | Why Needed | Used For | Public Data? | Primary Data Required? | Can Be Estimated? | Reliability | V1 Priority |
|---|---|---|---|---|---|---|---|
| Willingness to coordinate purchases (neutral framing) | Adoption feasibility signal | Discussion/limitations section | No | 🔵 Yes | No | Low-medium (social desirability risk, see K6) | 🟡 Should have |
| Preferred ordering frequency | Design input | Payment/logistics design | No | 🔵 Yes | No | Medium | 🔵 Nice to have |
| Preferred pickup/delivery method | Design input | Same | No | 🔵 Yes | No | Medium | 🔵 Nice to have |
| Trust concerns (open-ended) | Qualitative risk signal | Discussion section | No | 🔵 Yes | No | Qualitative, high value despite small N | 🟡 Should have |
| Timing constraints | Design input | Scheduling design | No | 🔵 Yes | No | Medium | 🔵 Nice to have |
| Quantity flexibility | Design input | Batching engine parameter range | No | 🔵 Yes | No | Medium | 🔵 Nice to have |

### A7. Market Data

| Variable | Why Needed | Used For | Public Data? | Primary Data Required? | Can Be Estimated? | Reliability | V1 Priority |
|---|---|---|---|---|---|---|---|
| Commodity, date, market, min/max/modal price | Core wholesale baseline | Every economic calculation | 🟢 Yes — Agmarknet via data.gov.in (confirmed Phase 1A/1B) | No | No | Medium-high (verify units, per Phase 1B's aggregator-discrepancy finding) | 🟢 Must have |
| Retail/consumer price | Comparator baseline | Price-spread calc | 🟢 Yes — Price Monitoring System, 38 commodities (confirmed Phase 1A) | No | No | Medium | 🟢 Must have, but never substitute for vendor procurement price |

### A8. Commodity Data

| Variable | Why Needed | Used For | Public Data? | Primary Data Required? | Can Be Estimated? | Reliability | V1 Priority |
|---|---|---|---|---|---|---|---|
| Commodity name, unit | Basic identifiers | All tables | 🟢 Yes | No | No | High | 🟢 Must have |
| Perishability category (broad: high/medium/low) | Freshness filter | Optimization constraint | 🟢 Partially — FAO/USDA ARS give refrigerated storage-life tables (confirmed Phase 1B) | No | Yes, as a coarse 3-tier category | Medium | 🟢 Must have |
| Storage condition assumed | Context for freshness window | Same | 🟢 Yes (refrigerated benchmarks only) | No | No | Low for ambient conditions specifically | 🟡 Should have |
| Freshness window (days, ambient) | Direct input to spoilage constraint | Optimization constraint | 🟡 No India-specific ambient dataset found (confirmed again this phase — see Section 3) | 🔵 Ideally confirmed via trader interview (Part 7) | Yes, as a conservative downward adjustment from refrigerated figures, clearly labeled | Low-medium until verified | 🟢 Must have, but treat current values as assumptions |

---

## 3. Public Data Availability Audit

**C1. Wholesale prices — 🟢 Confirmed feasible.** Agmarknet via data.gov.in: free API registration, daily modal/min/max prices, historical data accessible, Hyderabad/Telangana mandis covered (Bowenpally, Gaddiannaram). Re-confirmed finding from Phase 1B: secondary aggregator sites (napanta.com, todaypricerates.com) gave inconsistent figures for the same city/week — **use the official API directly, do not scrape aggregators for the final dataset.**

**C2. Retail/alternative prices — 🟢 Confirmed feasible, but re-prioritized down this phase.** The Department of Consumer Affairs Price Monitoring System tracks *consumer* retail prices for 38 essential commodities across many centres, and it is a real, usable comparator. However, since Phase 1B and this phase both establish that **consumer retail price ≠ street-vendor procurement price**, PMS data should not be collected or treated as a co-equal priority alongside the two figures that actually matter: **Priority 1 — Agmarknet wholesale price** (the economic baseline the whole savings calculation rests on), and **Priority 2 — actual vendor procurement price**, collected directly through the survey/diary (Section 6, D3), which is the project's real baseline for "what a vendor currently pays." PMS retail data is optional secondary context — useful for a sanity-check comparison or a discussion-section aside, but not worth spending collection time on beyond a light, ad hoc pull unless a specific research question in a later phase calls for it.

**C3. Weather data — 🟢 Technically available, ❌ Not recommended for V1.** IMD publishes rainfall and related data through data.gov.in and its own portals (district-level rainfall statistics, historical time series). Availability is not the issue. The issue is sample size: at 10–20 vendors over 7–14 days, adding weather as a model feature invites overfitting to noise rather than finding real signal — a concern already raised in earlier phases and reconfirmed here. **Recommendation: exclude weather from V1 entirely; note it explicitly as future work once a larger, longer-running dataset exists.**

**C4. Geographic and distance data —**

| Option | Cost | Accessibility | Accuracy | Suitability for 10–20 vendors |
|---|---|---|---|---|
| Haversine formula on manually recorded lat/long | 🟢 Free, no API, no dependency | Trivial — a formula, not a service | Good for straight-line distance; doesn't account for actual road routes | ✅ Recommended for V1 — sufficient at this scale and removes all API-dependency risk |
| OpenStreetMap Nominatim/OSRM public servers | Free | Rate-limited (roughly 1 request/second on the public Nominatim instance) and governed by a formal usage policy that prohibits heavy/bulk or commercial use | Better — real road-network distance | Acceptable for 10–20 one-off lookups, but adds a dependency and a usage-policy compliance burden not justified at this scale |
| Google Maps Distance Matrix API | Paid per call beyond a monthly credit; requires a billing account | Requires API key + billing setup | Best — real-time road distance/duration | Overkill for 10–20 vendors; the setup friction (billing account) is not worth it for V1 |

**Important correction to reconcile with Section 14's privacy guidance:** Haversine requires actual coordinates (latitude/longitude) — a locality name alone (e.g., "Ameerpet") cannot be fed into it, so "record locality-level location" and "use Haversine" are not, as originally drafted, fully compatible. Two options were considered:

- **Option A — Approximate stall coordinates, tied only to the anonymous vendor ID (recommended).** Read off an approximate latitude/longitude once per vendor during the survey (e.g., from a map app, without needing the vendor's name, phone number, or exact home address attached to it). This preserves anonymity — the coordinate identifies a stall location, not a person — while giving Haversine the input it actually needs for meaningful clustering.
- **Option B — Area/locality centroid (fallback only).** If even approximate individual coordinates feel too sensitive to collect, use the centroid of the named locality (e.g., a single fixed point for "Ameerpet") instead of a per-vendor coordinate. This is more private but meaningfully less accurate, since every vendor in the same locality collapses to one point and the whole clustering exercise loses resolution.

**Recommendation: use Option A — approximate stall coordinates (rounded if extra caution is wanted) recorded against the anonymous vendor ID only, never against a name, phone number, or exact home address.** This is what Section 4's Minimum Viable Dataset and Section 15's schema now assume, and it is free, has no rate limits or usage-policy risk, and is entirely adequate for a sample this size.

**C5. Freshness/shelf-life data — 🟢 Partially available, with an honest gap, and two data types that must not be blended into one.** FAO's postharvest handling manual and general international storage-life references (e.g., extension-service storage guides) give refrigerated/controlled-storage figures — for example, red tomato at 8–10°C: 8–10 days (confirmed in Phase 1B). **No India-specific (ICAR or otherwise) dataset giving ambient/room-temperature shelf life for tomato, onion, or potato was found in this or the prior phase's searches.** This must be stated plainly rather than papered over: ambient shelf-life figures used in this project are, at present, a 🟡 reasoned downward extrapolation from refrigerated data, not a verified fact.

**Important distinction:** a trader interview (Part 7) cannot *verify* this scientifically, and should not be described as doing so. Keep the two data types explicitly separate:
- 🟢 **Scientific freshness information** — from FAO, USDA ARS, ICAR, agricultural university research, or peer-reviewed literature. This is the only category that can be described as "verified" shelf-life data.
- 🔵 **Practical market information** — from trader/commission-agent interviews: what they consider acceptable to still sell, how long a commodity typically stays sellable in their own experience, and their storage practices. This is genuinely useful **triangulating context** that can sanity-check whether the 🟡 ambient assumption is in a reasonable ballpark — but it is a practitioner's practical judgment, not scientific verification, and must be labeled and cited as such wherever it's used, never merged into the 🟢 category.

---

## 4. Minimum Viable Dataset (MVD)

| Variable | Priority | Reason | Source |
|---|---|---|---|
| Vendor ID, category, approximate area | 🟢 Must Have | Core identifiers for every other table | 🔵 Primary |
| Commodity, quantity, unit, frequency, approximate price paid, procurement source | 🟢 Must Have — **Priority 2 economic baseline** (the real "what a vendor currently pays" figure, per Section 3, C2) | This is the actual research contribution — nothing else substitutes for it | 🔵 Primary |
| Payment method and timing (cash/credit, immediate/later) | 🟢 Must Have | Directly tests the Phase 1A payment/trust finding; determines which payment model (Phase 1B Section 13) is realistic | 🔵 Primary |
| Wholesale price (date, market, min/max/modal) | 🟢 Must Have — **Priority 1 economic baseline** | Core economic comparator | 🟢 Agmarknet |
| Approximate vendor coordinates (lat/long, tied to anonymous ID only — see Section 3, C4) | 🟢 Must Have | Enables the Haversine-based clustering the whole grouping logic depends on | 🔵 Primary |
| Commodity perishability category + freshness window | 🟢 Must Have | Required for the freshness constraint; keep the 🟢 scientific and 🔵 practical-trader components labeled separately (see Section 3, C5) | 🟢 FAO/USDA ARS (refrigerated, scientific) + 🟡 assumption (ambient) + 🔵 trader triangulation (practical, not scientific verification) |
| Retail/consumer price (PMS) | 🟡 Should Have (downgraded from Must Have — optional secondary context) | Not a substitute for vendor procurement price, and not worth prioritized collection time per Section 3, C2 | 🟢 PMS |
| Operating days | 🟡 Should Have | Refines which days count as valid observations | 🔵 Primary |
| Demand variability (requires diary, not survey) | 🟡 Should Have | Feeds uncertainty-aware ordering, but only if the diary component (Part 8) is run | 🔵 Primary (diary) |
| Trader-confirmed MOQ and effective wholesale-access price | 🟡 Should Have | Closes a real gap identified in Phase 1B (raw mandi price likely overstates real access price); note this is 🔵 practical trader input, not a scientific figure | 🔵 Primary (trader interview) |
| Trust/coordination concerns (qualitative) | 🟡 Should Have | Strengthens the discussion/limitations section | 🔵 Primary |
| Exact operating hours, seasonal patterns, event-driven spikes | 🔵 Nice to Have | Real but out of scope for a mini-project timeframe | 🔵 Primary (future work) |
| Weather | 🔵 Nice to Have (excluded from V1) | Available but not justified at this sample size | 🟢 IMD (not used in V1) |

**MVD summary: the project needs roughly 12–15 fields, not the 30+ variables listed in Part A. Everything outside the Must Have / Should Have tiers should be explicitly deferred, not quietly dropped — list them in the paper's "future work" section so the scoping decision is visible and deliberate.**

---

## 5. Vendor Primary Data Collection Plan

Given realistic access to 10–20 local vendors, the plan combines a short one-time survey (all 10–20 vendors) with a short purchase diary from a willing subset (see Part 8 for the feasibility comparison that leads to this recommendation). The survey below is designed to take 5–10 minutes, spoken conversationally rather than read as a form, since many vendors will not have time to sit with a written questionnaire mid-shift.

---

## 6. Vendor Survey Questionnaire

**Format note:** ask in the vendor's own units first (bags, crates, "₹200 worth"), and convert to kg afterward using standard conversion references — do not force the vendor to do the conversion themselves (see Section 13, K2).

**D1. Vendor Profile**
1. What type of stall do you run? (tea/chaat/fruit/vegetable/other — record as spoken)
2. Roughly which area do you usually operate in? (locality name, not exact address)
3. How many days a week do you usually operate?

**D2. Commodity Usage** *(ask only for the 2–3 focal commodities decided in Phase 1B — lead with onion and potato, include tomato as the harder case)*
4. Do you use [commodity] in your stall?
5. On a normal day, roughly how much [commodity] do you go through? (Accept any unit — kg, bags, baskets, "₹100 worth" — do not insist on kg)
6. How often do you buy [commodity] — every day, every few days, once a week?

*(Avoid: "Give your exact daily consumption over the past 30 days" — no vendor will have this. The goal is a usable approximation, not false precision.)*

**D3. Procurement**
7. Where do you usually get [commodity] from? (a nearby shop, a wholesaler, an agent who delivers, the mandi directly, etc.)
8. Roughly what do you pay per [unit] the last time you bought it? (accept an approximate figure — do not press for exact recall)
9. Does anyone deliver it to you, or do you go and get it yourself?

**D4. Logistics**
10. How do you (or your supplier) usually transport it? (on foot, cycle, auto, someone else's vehicle)
11. Roughly how far is that from here? (in minutes of travel is fine if km is unknown)

**D5. Payment**
12. When you buy [commodity], do you usually pay right away, or settle up later?
13. Do you mostly pay cash, or something else (UPI, etc.)?

*(Do not ask for exact amounts owed, credit limits, or income — not needed, and not appropriate to ask.)*

**D6. Collaborative Procurement (neutral framing)**
14. Do you know other nearby vendors who buy similar things to you?
15. If a few nearby vendors could combine an order to get a better price, what would worry you most about that — the price, trusting the arrangement, the timing, or something else?
16. Would you rather collect the order yourself, or have it delivered to one common spot?

*(Avoid: "Would you use my amazing collaborative procurement platform?" — this invites a polite yes rather than real signal. Question 15 is deliberately open and slightly negative-leaning to counteract social-desirability bias, per Section 13, K6.)*

---

## 7. Trader/Wholesaler Interview Plan

**Recommendation: yes, interview 2–5 local traders/commission agents.** This is not a statistical sample — it is a **validation check on the assumptions used in the prototype**, and the distinction should be stated explicitly in the paper: this is a small-N qualitative/expert-consultation component, not a survey intended to generalize across all traders.

**5-minute semi-structured interview guide:**
1. For [commodity], is there a minimum quantity you'd sell at a wholesale rate to someone who isn't a regular registered buyer?
2. Does the price change noticeably if someone buys, say, 50 kg vs. 10 kg?
3. Would you deliver to a nearby collection point, and if so, roughly what would that cost?
4. How do most small buyers pay you — cash on the spot, or do some settle later?
5. In practice, how many days does [commodity] usually stay sellable once it leaves here, without refrigeration?

This directly targets the three biggest unresolved gaps from Phase 1B: real MOQ figures, the effective wholesale-access price (vs. the raw mandi average), and ambient shelf life — all three are currently 🟡 assumptions. **A clarification on Question 5 specifically:** the trader's answer here is 🔵 practical market information — a practitioner's real-world experience of what stays sellable — not a scientific verification of shelf life, and it must be reported as such (see Section 3, C5). Even 2–5 informal expert conversations would meaningfully *triangulate* whether the current 🟡 assumptions are in a reasonable ballpark; they do not *upgrade* those assumptions to verified fact.

---

## 8. Purchase Diary Feasibility

| Option | Strengths | Weaknesses | What it supports | What it cannot support |
|---|---|---|---|---|
| **A — One-time survey (10–20 vendors)** | Fast, low burden, covers more vendors | Single snapshot — no variability, high recall-bias risk for "typical" quantities | Cross-sectional description, MVD baseline, qualitative signal | Any time-series analysis, demand variability, newsvendor-style uncertainty modeling |
| **B — 7-day diary (10 vendors)** | Captures real day-to-day variation; still a manageable ask | Attrition risk over even a week; vendors may forget days | Basic variability estimation, a short real time series for calibrating synthetic data | Weekly/seasonal patterns, robust statistical inference |
| **C — 14-day diary** | More data points, better variability estimate | Meaningfully higher burden and attrition risk for informal, time-poor vendors; realistic completion rate likely lower than 7-day | Marginally better calibration than 7-day | Same limits as B, just less severely |
| **D — Hybrid: survey of 15–20 vendors + 7–14 day diary from 5–10 willing vendors** | Combines broad (if shallow) coverage with a smaller but real time-series subset; realistic given informal-sector time constraints | More coordination effort than a single instrument | MVD baseline from the full group, plus real variability data from the diary subset for calibrating the synthetic expansion (Phase 1B's Part J requirement) | Still not a statistically representative or generalizable dataset — must not be framed as one |

**Recommendation: Option D (hybrid), with a 7-day rather than 14-day diary window.** A 7-day diary is the more realistic ask for this population given documented time constraints (Phase 1A), and still supplies exactly what's needed to calibrate the synthetic-data distributions honestly, without the higher attrition risk of a 14-day ask.

---

## 9. Sample Size Analysis

| Research Activity | Suitable? | Explanation |
|---|---|---|
| Exploratory case study | ✅ Yes | 10–20 vendors with a 7-day diary subset is a legitimate small-N exploratory/embedded case-study design, a well-established approach when studying informal-sector economic behavior under real access constraints |
| Prototype validation | ✅ Yes | Enough to sanity-check whether the decision engine behaves sensibly against real inputs |
| Economic simulation (real-calibrated synthetic scale-up) | ✅ Yes, with caveats | Calibration parameters (mean, spread) drawn from N=10–20 will have wide uncertainty — report confidence ranges, don't hide them |
| Statistical generalization to "Indian street vendors" as a population | ❌ No | Sample is small, convenience-based, and single-city — cannot support a representativeness claim |
| Traditional ML training (supervised, held-out test set, per-vendor models) | ❌ Not realistically | ~70–280 vendor-day observations spread across several commodities is too sparse for a generalizable trained model; high overfitting risk |
| Optimization experiments (the batching/constrained-clustering engine) | ✅ Yes | Optimization operates on parameter ranges, not labeled training examples — not constrained by the same sample-size limits as ML |
| User feedback (qualitative) | ✅ Yes | 10–20 respondents is a normal, often sufficient sample for qualitative thematic signal in a fairly homogeneous population |

**Defensible framing for the paper:** *"a prototype decision framework developed and evaluated through an exploratory field study (10–20 vendors, including a 7-day purchase diary with a subset), combined with real government market-price data and a calibrated simulation for scaled evaluation of the optimization component."* **Do not claim** "a representative study of Indian street vendors" or "a validated demand-forecasting model" — neither is supportable at this scale.

---

## 10. AI/ML Data Feasibility

| Scenario | Observations (approx.) | Data Diversity | ML Feasibility | Scientific Risk |
|---|---|---|---|---|
| 1 — 10 vendors × one survey | ~10–30 single data points (per commodity) | Very low — one snapshot per vendor | ❌ None for supervised ML | Any model "trained" on this would essentially memorize noise |
| 2 — 10 vendors × 7 days | ~70 vendor-day records, fewer per specific commodity | Low-moderate | ❌ Not enough for a trained supervised model; ✅ enough for descriptive statistics (mean, variance) per vendor/category | Overfitting near-certain if a supervised model is forced |
| 3 — 20 vendors × 14 days | ~280 vendor-day records | Moderate | ⚠️ Borderline — still thin per commodity-vendor cell; simple models (e.g., a single global or per-category regression with very few features) might be defensible, a per-vendor model is not | Still real overfitting risk if complexity isn't kept minimal |
| 4 — Pooled category-level observations (grouping similar vendors together rather than modeling each individually) | Effectively multiplies usable observations per estimate by pooling across vendors in the same category | Improves diversity within a category | ✅ This is the right unit of analysis for lightweight estimation | Requires assuming within-category vendors are reasonably comparable — a reasonable, statable assumption |
| 5 — Real observations + calibrated synthetic simulation | Real data sets the parameters; synthetic data provides scale for testing the optimization engine | High (for the optimization test-bed) | ✅ Fully appropriate for evaluating optimization behavior; ❌ still not a basis for claiming a validated ML forecasting model, since the synthetic data is generated from the same limited real parameters, not independent evidence | Must never be described as validating real-world forecasting accuracy |

**Recommendation:** do not use Random Forest/LightGBM or any trained supervised model as the headline forecasting method for V1 — the data doesn't support it, and using it anyway would be presenting an unvalidated model as more rigorous than it is. More importantly, **do not present category-level averaging or similarity matching as "our AI model" either** — a simple average is not automatically ML, and a project presentation that says "our AI model uses category averages" invites a reasonable and hard-to-answer "where is the AI?" from a judge. The corrected framing is three explicit intelligence layers, with the honesty about what's real and what's future work built into the naming itself:

- **Layer 1 — Demand Estimation (similarity-based case reasoning).** For cold-start / low-history vendors: find the 2–3 most comparable vendors by category and reported typical quantity, and estimate from their behavior (Scenario 4's category-level mean/spread is the simplest version of this). This is a real, citable technique family — case-based reasoning / memory-based estimation — and should be named exactly that in the paper, not inflated into a headline "AI model." It is a supporting layer, not the project's intelligence claim.
- **Layer 2 — Predictive Learning (deferred).** A properly trained ML forecasting model, architecturally supported by the system design once enough transaction history accumulates through real platform usage. V1 must state plainly that this layer is **not** trained or validated on the small field dataset — it is future work, not a current capability.
- **Layer 3 — Optimization Intelligence (the core contribution).** The constrained decision engine that weighs vendor demand, current price, geographic distance, transport cost, and freshness together to decide whether to procure collaboratively, with whom, and how much. This is where the project's actual research intelligence lives, it is not limited by the small-sample problem that constrains Layers 1 and 2 (per this section's earlier finding), and it should be positioned in both the system design and the paper's abstract as the headline contribution — with Layer 1 correctly described as a supporting cold-start estimator feeding it, not as the AI/ML claim itself.

---

## 11. Cold-Start Data Feasibility — Similarity-Based Case Reasoning (Layer 1)

Onboarding data realistically collectible from the survey (vendor category, which commodities are used, typical quantity in whatever unit the vendor reports, purchase frequency, operating days) is exactly the input a **similarity-based case-reasoning estimator** needs: it does not require historical transaction data, only a same-category peer group to compare against. With 10–20 vendors spread across a handful of categories (tea stall, chaat, fruit cart, etc.), each category will likely have only a few peers — enough for a simple average-of-similar-vendors estimate, not enough for anything more statistically elaborate.

**This is a feasibility confirmation, not a full algorithm design** (per this phase's scope restriction), and it is worth restating precisely what is and isn't being claimed: yes, the onboarding data supports a similarity-based initial estimate as **Layer 1** of the three-layer architecture (Section 10); no, it does not support a more sophisticated cold-start ML method (e.g., meta-learning approaches from the Phase 1A literature review) at this sample size — those remain a valid citation for *why* the general technique family is credible, not a method this project's data can actually run. And to be explicit about the point raised in Section 10: this layer should be described in the paper as "similarity-based case reasoning for cold-start demand estimation" feeding the optimization engine — not as the project's AI/ML contribution in its own right. That contribution is Layer 3.

---

## 12. Real + Synthetic Data Strategy

| Category | Rule |
|---|---|
| **MUST BE REAL** | Government market prices (Agmarknet, PMS) with correct units and dates; commodity characteristics from FAO/USDA ARS; actual survey/diary/interview responses, verbatim or accurately summarized |
| **CAN BE PRIMARY DATA** | Vendor procurement behavior, payment behavior, self-reported demand and frequency, trader-reported MOQ/shelf-life estimates |
| **CAN BE SIMULATED** | Additional demand scenarios beyond the surveyed vendors (to stress-test the optimization engine at a scale of, say, 100+ simulated vendors); additional group-participation/willingness scenarios; price-path simulations for sensitivity analysis |

**Strict rules for any simulated data used in this project (all required, none optional):**
1. Every synthetic record must be labeled as such in the dataset itself (a `data_source` field: real / survey / diary / synthetic), not just described as such in prose.
2. Generation must be reproducible — fixed random seeds, documented generation script.
3. Every distributional assumption used to generate synthetic data must be written down explicitly (e.g., "tomato daily demand ~ Normal(mean, sd) with mean and sd taken from the 7-day diary subset, n=X vendors").
4. Synthetic data must never be described in results/figures as if it were observed vendor behavior — figures and tables must distinguish real-observation counts from simulated-scenario counts.
5. Wherever possible, synthetic parameters should be anchored to a real observed range (Phase 1B's price and transport-cost figures, this phase's diary-derived demand variability) rather than invented from scratch.

**Critical evaluation:** given Section 10's finding, synthetic data in this project should be used almost exclusively to stress-test the **optimization engine** (which tolerates and even benefits from larger simulated scenario sets) — not to manufacture the appearance of a larger ML training set, which would not fix the fundamental sparsity problem and would risk exactly the kind of "presenting synthetic data as real capability" that Phase 1A and 1B both explicitly warned against.

---

## 13. Data Quality Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| **K1. Recall bias** | Vendors misremember exact prices/quantities, especially for "typical" values | Ask for ranges/approximate figures rather than exact numbers; prioritize diary data (recorded same-day) over recalled survey answers wherever the two conflict |
| **K2. Unit inconsistency** | Vendors report in bags, baskets, "₹X worth," not kg | Record the vendor's own unit verbatim at collection time; build a simple, documented conversion table afterward (e.g., via a follow-up question or a standard reference) rather than forcing vendors to self-convert |
| **K3. Missing data** | Vendors skip diary days, or a survey question is left blank | Design the diary to be as low-friction as possible (a single line per day); accept partial responses rather than discarding whole records; report the missingness rate transparently |
| **K4. Irregular purchasing** | Not every commodity is bought daily, complicating "daily demand" framing | Ask purchase frequency explicitly (D2, Q6) and derive an implied daily-equivalent rather than assuming daily purchase for every commodity |
| **K5. Small sample bias** | 10–20 vendors, single city/locality, convenience-sampled | State this plainly as a limitation (Section 9); do not generalize beyond the sampled population in any claim |
| **K6. Social desirability bias** | Vendors may tell the researcher what they think is wanted, especially on Q15 (collaborative procurement) | Use neutral/slightly negative-leaning question framing (as drafted in Section 6); avoid naming or pitching "the platform" during data collection |
| **K7. Location privacy** | Exact home addresses are sensitive and unnecessary; but a locality name alone is not precise enough for the Haversine distance calculation the grouping logic depends on (see Section 3, C4) | Record an approximate stall coordinate (not exact home address) tied only to the anonymous vendor ID — never to a name, phone number, or identifiable address (see Part 14) |

---

## 14. Ethical Data Collection Guidelines

- Participation is voluntary; a vendor can decline or stop at any point without needing to give a reason.
- Consent is given verbally at the start of the conversation — no signature or written form is required or expected for a mini-project field study of this kind, but the verbal consent should be explicit, not assumed.
- Collect only what is listed in the Minimum Viable Dataset (Section 4) — no addresses, ID numbers, exact income, or financial account details.
- Assign an anonymous vendor ID at the point of collection; never store the vendor's name against their data.
- Record an approximate stall coordinate (latitude/longitude), not an exact home address, and tie it only to the anonymous vendor ID — never to a name, phone number, or other identifying detail (per Section 3, C4, this level of precision is needed for the Haversine distance calculation; a locality name alone is not sufficient for that purpose, so this is the deliberate privacy/utility balance point, not a relaxation of privacy).
- No individual vendor's responses are shared outside the research team; only aggregated or anonymized findings appear in the paper.
- The trader/wholesaler interviews (Section 7) follow the same consent and anonymity principles.

**Suggested spoken consent script (to be read/paraphrased naturally, not handed over as a document):**

> *"Hi, I'm a student working on a college project about how vendors like you buy supplies like [onion/potato/tomato]. I'd like to ask a few quick questions — it'll take about 5 minutes. I won't take your name, just general answers, and you can skip anything you don't want to answer or stop anytime. Is that okay?"*

---

## 15. Recommended Dataset Schema

The schema proposed in the prompt is close to correct and is confirmed sufficient for V1, with small additions (a `data_source` field per Section 12's synthetic-labeling rule, and a `vendor_category` link made explicit on the Commodity-usage relationship). No new tables are needed — resist the urge to add more.

```text
Vendor
  vendor_id
  category
  approx_latitude        (approximate stall coordinate, tied only to vendor_id — not a name or address; see Section 3, C4)
  approx_longitude
  operating_days

Procurement_Observation
  vendor_id
  date
  commodity
  quantity
  unit
  purchase_price
  procurement_source
  payment_method        (added: cash / credit / UPI — supports Section 13's A5 requirement)
  data_source            (added: survey / diary / synthetic — supports Section 12's labeling rule)

Market_Price
  date
  market
  commodity
  min_price
  max_price
  modal_price
  source                 (added: agmarknet / pms — keeps the two comparators explicitly distinct, per the retail≠procurement-price rule)

Commodity
  commodity
  perishability_category
  storage_condition
  freshness_window_days
  freshness_window_source       (added: scientific / assumed / trader-practical — keeps the 🟢 FAO/ICAR figures, 🟡 ambient extrapolation, and 🔵 trader-interview triangulation explicitly distinct, per Section 3, C5 — never blend these into one "verified" figure)

Logistics
  vendor_id
  transport_method
  approx_transport_cost
  delivery_available
```

This is deliberately still five small tables — enough to run every calculation in Phase 1B and support the cold-start/similarity estimation in Section 11, without overengineering a schema for a dataset that will realistically hold a few hundred rows at most.

---

## 16. Data Collection Timeline

| Week | Activity | Output |
|---|---|---|
| 1 | Finalize commodities (onion, potato as primary; tomato as stress case, per Phase 1B); prepare survey and interview guides; identify candidate vendors and 2–5 traders | Finalized instruments, vendor/trader contact list |
| 2 | Conduct the vendor survey (10–20 vendors); conduct trader/wholesaler interviews (2–5) | Completed survey responses, interview notes |
| 3–4 | Run the 7-day purchase diary with 5–10 willing vendors from the survey pool | Raw diary records |
| 4 (parallel) | Pull Agmarknet wholesale data (Priority 1) for the same window, for the chosen commodities/market; only if time allows, a light supplementary PMS retail pull for optional secondary context (per Section 3, C2 — not a priority use of collection time) | Cleaned Market_Price table |
| 5 | Clean and normalize all collected data (unit conversion, missing-data handling, anonymized ID assignment) | Cleaned Procurement_Observation and Logistics tables |
| 5 (parallel) | Document synthetic-data generation rules and parameters based on diary-derived variability | Documented, reproducible synthetic-generation script |
| 6 | Consolidate all tables into the final schema; run the Section 9/10 sample-size and feasibility checks against the real collected data (not just the projected numbers in this report) | Final V1 dataset, ready for the next design phase |

This is a 5–6 week plan, realistic alongside coursework, and deliberately front-loads the survey/interview work so that any recruitment difficulties surface early rather than late.

---

## 17. Final Data Feasibility Verdict

**🟡 DATA FEASIBLE WITH LIMITATIONS.**

**1. Can enough real data be collected?** Yes — for the Minimum Viable Dataset defined in Section 4, using the hybrid survey + diary + trader-interview plan.

**2. What must come from primary data?** Vendor procurement price (the real Priority 2 economic baseline, per Section 3 C2), quantity, frequency, payment behavior, approximate stall coordinates, and trader-reported MOQ/effective-price/practical-shelf-life input — none of this exists publicly, confirmed again in this phase. Note that the trader input is 🔵 practical market information, not a scientific verification (Section 3, C5) — it triangulates the assumptions, it does not certify them.

**3. What reliable public data exists?** Wholesale prices (Agmarknet — the Priority 1 economic baseline), refrigerated-storage shelf-life benchmarks (FAO/USDA ARS, the 🟢 scientific freshness data), retail/consumer prices (Price Monitoring System — real, but optional secondary context, not a collection priority), and weather data (IMD) — the last of which should be collected-but-unused in V1 for scientific reasons, not availability reasons.

**4. Is a 10–20 vendor sample useful?** Yes, for an exploratory case study, prototype validation, and as the calibration source for a clearly-labeled synthetic expansion. No, for statistical generalization or for training a conventional supervised ML model.

**5. What research claims can we make?** "A prototype decision framework developed and evaluated through an exploratory field study, combined with real government market data and a calibrated simulation for testing the optimization component." Also defensible: specific, bounded findings like "for the vendors and commodities studied, collaborative procurement broke even at approximately X kg" (an illustrative, not universal, claim).

**6. What claims must we NOT make?** "A validated demand-forecasting model for street vendors." "A representative study of Indian street vendor economics." "An AI-powered system" in the deep-learning sense. Also specifically: do not present Layer 1's category-average/similarity estimation as if it were, on its own, the project's AI/ML contribution — a simple average is not automatically ML, and claiming otherwise invites exactly the "where is the AI?" question a careful reviewer will ask. The honest description is a three-layer architecture (Section 10): lightweight case-based estimation for cold start, ML explicitly deferred to future work, and a genuinely non-trivial constrained optimization engine as the actual headline contribution.

**7. Is traditional ML realistically feasible?** No, not as originally scoped (Random Forest/LightGBM per-vendor forecasting). The sample size does not support it.

**8. Can AI/ML be justified in another scientifically honest way?** Yes — via the three-layer architecture established in Section 10: Layer 1 (similarity-based case reasoning for cold-start demand estimation, explicitly *not* labeled as the project's headline AI), Layer 2 (predictive ML, honestly deferred to future work once real usage data accumulates), and Layer 3 (the constrained optimization engine, which is the project's genuine intelligence contribution and is not limited by the small-sample constraints affecting Layers 1–2).

**9. Is synthetic data appropriate?** Yes, strictly for stress-testing the optimization engine (Layer 3) at scale, generated under the labeling and reproducibility rules in Section 12 — not as a substitute for real forecasting validation.

**10. What must change before the next research phase?** The AI/ML component of the system design must be re-scoped now, before any architecture or algorithm design begins, into the explicit three-layer framing (Section 10): similarity-based case reasoning (Layer 1) feeding a constrained optimization engine (Layer 3) for V1, trained ML (Layer 2) explicitly deferred to future work once real platform-usage data accumulates — and the optimization engine, not the demand estimator, should be carried forward as the project's headline intelligence claim in every subsequent phase and in the eventual paper. This is a scope and framing correction, not a project-ending problem.

**Direct answer to the phase's governing question: yes — there is a realistic and scientifically defensible path to the data this project needs, provided the AI/ML ambitions are right-sized to what a 10–20 vendor field study can actually support.**

---

## Sources

- [Nominatim Usage Policy — OpenStreetMap Foundation](https://operations.osmfoundation.org/policies/nominatim/)
- [Google Maps API Pricing 2026 — Woosmap](https://www.woosmap.com/blog/google-maps-api-pricing-breakdown)
- [Rainfall in India — data.gov.in](https://www.data.gov.in/catalog/rainfall-india)
- [All India District Rainfall Statistics — IMD](https://mausam.imd.gov.in/imd_latest/contents/rainfallinformation.php)
- [Storage Life of Vegetables — SDSU Extension](https://extension.sdstate.edu/storage-life-vegetables)
- [FAO, Manual for the preparation and sale of fruits and vegetables (storage-life table)](https://www.fao.org/4/y4893e/y4893e06.htm) *(carried forward from Phase 1B)*
- Agmarknet / data.gov.in, Price Monitoring System (fcainfoweb.nic.in), and WIEGO/Bhowmik field study — *(sources verified in Phase 1A/1B, re-applied here; not re-fetched this phase)*
