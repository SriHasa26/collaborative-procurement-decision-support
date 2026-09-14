# 📂 RESEARCH AUDIT FILE — PHASE 1B
### Quantitative Economic Feasibility & Data Audit
**Subject:** An AI-Assisted Freshness- and Logistics-Aware Collaborative Procurement Decision Framework for India's Informal Street Vendors
**Question this phase answers:** Can collaborative bulk procurement actually save street vendors money after transportation, logistics, and handling costs are included?

**Data labeling used throughout:**
🟢 REAL OBSERVED DATA · 🔵 PRIMARY SURVEY DATA (not yet collected) · 🟡 EXPERIMENTAL ASSUMPTION · 🟠 SYNTHETIC/SIMULATED DATA (not used in this phase)

---

## 1. Executive Summary

**Verdict: 🟡 MODIFY — the economics work, but only under specific, narrower conditions than the original problem statement assumed.**

Using real wholesale and retail price data for Hyderabad (Telangana) and real local transport rental rates, collaborative procurement does produce a positive price spread large enough, in principle, to cover local transport costs — but only once a single group order reaches roughly **35–70 kg**, because local transport in Indian cities is priced as a near-fixed per-trip charge (₹800–2,500 for a 0–10 km trip), not a small linear per-km rate. That threshold translates to needing roughly **8–15 vendors** clustered together per commodity per day, under a demand assumption that has not yet been verified with real vendors.

The bigger finding is that **the three candidate commodities behave very differently once freshness is factored in**. Onion and potato have long ambient shelf life, so there is no meaningful tension between "buy enough to justify the transport cost" and "sell it before it spoils" — for these two, the model looks workable. Tomato (and by extension leafy greens) is a harder case: its short shelf life means the order size needed to amortize a fixed transport cost can exceed what a small vendor cluster can safely consume before spoilage, especially without cold storage. Cooking oil doesn't fit this model at all — it is a packaged manufactured good with no mandi/wholesale price spread mechanism comparable to fresh produce, and needs either a different economic model (bulk-pack-size discounting) or should be dropped from the initial commodity set.

A second, methodologically important finding: two different secondary price-aggregator websites, both claiming to source Hyderabad mandi data within days of each other, produced wholesale figures that disagreed by 2–3×. This is a data-quality warning, not just a footnote — it means none of the numbers in this report should be treated as final, and the actual paper must pull matched, same-day, unit-verified data directly from the primary data.gov.in Agmarknet API rather than any scraped aggregator site.

**This is not a pivot.** The core mechanism survives contact with real numbers for at least two of three tested commodities. But the commodity scope, the transport-cost model, and the group-size assumption in the original problem statement all need to be narrowed and made explicit before moving to system design.

---

## 2. Economic Model

**Scenario 1 — Individual procurement**

$$C_{individual} = Q \times P_{retail/local}$$

Explicit monetary transport cost is **excluded** from the V1 individual-procurement model. Phase 1A found that a substantial share of vendors source goods via existing routine trips, on-foot proximity, or wholesaler-advance/credit arrangements rather than a dedicated paid trip — meaning individual transport cost is real but largely an *embedded opportunity/time cost*, not a comparable cash outflow. Forcing a monetary value onto it without primary data would mean inventing a number, which this audit was explicitly told not to do. **Recommendation: treat individual travel cost as a stated limitation, not a modeled variable, until primary survey data can characterize it.**

**Scenario 2 — Collaborative procurement**

$$C_{group} = Q \times P_{wholesale} + C_{transport} + C_{handling} + C_{wastage}$$

Component-by-component decision for V1:

| Component | Data available? | Include in V1? | Treatment |
|---|---|---|---|
| Commodity cost at wholesale price | 🟢 Yes (Agmarknet-derived) | Yes | Core variable |
| Transport (inbound, wholesaler→collection point) | 🟢 Yes (real rental rate ranges) | Yes | Modeled as a near-fixed per-trip charge, not pure per-km (see Section 6) |
| Distribution (collection point→vendors) | 🔴 No real data found | Deferred | Assume single collection point = vendor cluster centroid for V1; multi-stop distribution costing is future work |
| Handling | 🔴 No real data found for this population | 🟡 Experimental only | Not included in the base-case break-even calculation; shown only in a sensitivity variant, explicitly labeled assumption |
| Expected wastage/spoilage cost | 🟢 Partially — derivable from shelf-life vs. consumption-time analysis (Section 12) | Yes, as a feasibility *filter*, not a cost line | Modeled as a binary/graded risk flag rather than a rupee cost, since no real spoilage-rate data for this context was found |
| Payment/coordination cost | 🔴 No data | Deferred | Treated as a design/trust question (Section 13), not a monetary cost in V1 |

**Net savings and break-even:**

$$NetSavings = C_{individual} - C_{group}$$

$$SavingsPerUnit = P_{retail/local} - P_{wholesale}$$

$$BreakEvenQuantity = \frac{C_{transport}}{SavingsPerUnit}$$

This assumes handling and wastage costs are zero at the break-even point (a simplification, stated as such) and that the wholesale price used is the raw mandi average rather than a trader-marked-up "effective access price" — see the caution in Section 10.

---

## 3. Data Source Verification

| Variable | Required For | Possible Source | Real Data Available? | Free? | Frequency | Geographic Coverage | Suitable for V1? |
|---|---|---|---|---|---|---|---|
| Wholesale/mandi price | Commodity cost (group) | Agmarknet via data.gov.in API | 🟢 Yes — confirmed free registration + REST API in Phase 1A audit; not independently re-verified this phase beyond catalog-page confirmation | Yes | Daily | 3,000+ mandis nationally, incl. Hyderabad-area markets (Bowenpally, Gaddiannaram) | Yes, via the official API — **not** via scraped secondary sites (see Section 3a) |
| Retail/alternative price | Comparison baseline | Dept. of Consumer Affairs Price Monitoring System (fcainfoweb.nic.in) | 🟢 Confirmed to exist (Phase 1A), covers 38 essential commodities | Yes | Daily | Hundreds of centres nationally | Yes, but access is via generated web reports, not a clean API — requires scripting effort |
| Vendor procurement price (what a vendor *actually* pays) | True individual-cost baseline | None found | 🔴 No public dataset — PMS tracks *consumer* retail price, which is not proven equivalent to street-vendor procurement price | — | — | — | 🔵 Primary survey required — this is the single most important data gap in the whole project |
| Transport cost | Group logistics cost | Commercial rental-rate listings (thetransporter.in, logisticmart, bookmytempo, etc.) | 🟢 Yes, real published rate bands for Hyderabad specifically | Free to view | Static listings, not daily | City-level | Yes, as a bounded range; primary quotes from 2–3 actual local operators would strengthen this |
| MOQ (wholesaler/trader minimum order) | Feasibility constraint | None public found | 🔴 No — mandi trading is auction/lot-based (commonly by the quintal), not published as a fixed retail-style MOQ | — | — | — | 🔵 Primary survey/trader interview required; do not invent a number |
| Shelf life / perishability | Freshness constraint | FAO postharvest handling manuals; USDA ARS storage handbook | 🟢 Yes, but only for **refrigerated/controlled storage**, not ambient | Yes | Static reference data | International, not India-specific | Partially — ambient-condition figures are a REASONABLE ASSUMPTION extrapolated downward from refrigerated figures, not directly verified (see Section 12) |
| Vendor demand quantity | Group sizing, break-even translation to vendor count | None found | 🔴 No public dataset (confirmed in Phase 1A) | — | — | — | 🔵 Primary survey required — used here only as a labeled 🟡 experimental assumption (5 kg/vendor/day) |
| Geographic vendor density / clustering distance | Group formation radius | No dedicated dataset found this phase | 🔴 Not found | — | — | — | 🔵 Primary field observation required; reasoned estimate given in Section 7 |

### 3a. Data-quality finding (important)

Two different price-aggregator websites were checked for Hyderabad/Bowenpally mandi prices within a 4-day window (8 and 12 September 2026):

- 🟢 napanta.com (Bowenpally, 8 Sep 2026): tomato avg **₹1,000/quintal** (≈₹10/kg), onion avg **₹4,000/quintal** (≈₹40/kg), potato avg **₹1,200/quintal** (≈₹12/kg).
- 🟢 market.todaypricerates.com (Hyderabad, 12 Sep 2026): tomato "wholesale" **₹26/kg**, onion (big) **₹52/kg**, potato **₹29/kg**, alongside retail bands ₹29–82/kg depending on commodity.

These disagree by roughly 2.5–3× on "wholesale" tomato and potato prices for essentially the same city and week. This could reflect different sub-markets, different varieties/grades, unit-labeling confusion (₹/quintal vs ₹/kg — one automated extraction of the napanta page even mislabeled the unit), or simple aggregator error. **This is a direct, evidence-based reason not to trust scraped aggregator sites for the research paper.** The figures used in this report's calculations (Section 9) use the napanta per-quintal-converted wholesale figures (more consistent with standard Agmarknet unit convention) paired with the todaypricerates retail figures, but this pairing itself is an approximation across two unverified sources and two nearby-but-different dates — **explicitly labeled 🟢/⚠️ real-but-unverified, not certified**. Before the actual paper is written, matched same-day wholesale (Agmarknet API) and retail (PMS) figures must be pulled directly from the primary sources.

---

## 4. Commodity Selection

| Commodity | Vendor Relevance | Price Data | Retail Data | Perishability Data | Recommended? | Reason |
|---|---|---|---|---|---|---|
| **Tomato** | High — used by chaat, curry, and most cooked-food stalls | 🟢 Available (Agmarknet) | 🟢 Available (PMS/aggregators) | 🟢 Refrigerated data available; ambient is a reasoned extrapolation, not verified | ✅ Yes, as the "hard case" | Highest price spread found, but also highest perishability risk — the commodity that will show whether the model survives its most demanding test |
| **Onion** | High — near-universal ingredient | 🟢 Available | 🟢 Available | 🟢 Long ambient shelf life is well-established general food-science knowledge | ✅ Yes, as the "easy case" | Long shelf life removes the freshness constraint almost entirely, letting the analysis isolate the pure economic/logistics question |
| **Potato** | High — near-universal | 🟢 Available | 🟢 Available | 🟢 Long ambient shelf life, similar to onion | ✅ Yes | Behaves similarly to onion; included to confirm the pattern holds across more than one long-shelf-life commodity |
| **Cooking oil** | High (per original PS) | ⚠️ Not a mandi/Agmarknet commodity in its refined (packaged) form — Agmarknet tracks raw oilseeds, not bottled cooking oil | 🟢 PMS tracks retail packaged-oil prices | 🟢 Effectively non-perishable | ❌ Not recommended for V1 | The wholesale-vs-retail "mandi arbitrage" mechanism this whole project is built on does not apply to a manufactured packaged good — savings there would come from bulk-pack-size discounting (15L tin vs. 1L pouch), a *different* economic model. Recommend dropping oil from the initial 2–4 commodities, or treating it as a separate, later, structurally-different case study |
| Leafy greens (mentioned in earlier drafts) | High | 🟢 Likely available on Agmarknet | 🟢 Likely available | Very short ambient shelf life — expected to be *more* extreme than tomato | Not tested numerically this phase | Would very likely fail the freshness test even more decisively than tomato; not worth spending V1 build effort on until the tomato case is proven out |

**Recommended V1 commodity set: Onion and Potato as the core proof-of-concept (long shelf life, model works cleanly); Tomato as a deliberately included stress-test case to demonstrate the freshness-vs-economics tradeoff the whole system is designed to catch. Drop cooking oil from the initial set.**

---

## 5. Price Spread Analysis

| Commodity | 🟢 Wholesale (mandi, Bowenpally/Hyderabad) | 🟢 Retail/alternative (Hyderabad) | Price Spread | % Spread (of retail) |
|---|---:|---:|---:|---:|
| Tomato | ₹10/kg | ₹31.5/kg (mid of ₹29–34) | ₹21.5/kg | 68.3% |
| Onion | ₹40/kg | ₹62.5/kg (mid of ₹57–68) | ₹22.5/kg | 36.0% |
| Potato | ₹12/kg | ₹35/kg (mid of ₹32–38) | ₹23/kg | 65.7% |

**Important labeling caveat, per the instructions for this phase:** these are called **potential price spreads**, not "street vendor savings." No data confirms that street vendors actually pay the PMS/aggregator retail price rather than a wholesaler-advance/credit price partway between wholesale and retail (Phase 1A's finding that ~48% of vendors buy on advance from agents applies directly here). The true vendor-specific baseline price remains a 🔵 primary-survey requirement, not yet available. Treat the spreads above as an **upper bound on the opportunity**, not a guaranteed savings figure.

---

## 6. Transportation Cost Analysis

🟢 Real listed rates for Hyderabad local (0–10 km) goods transport:

| Vehicle class | Local trip (0–10 km) | Notes |
|---|---|---|
| Chota Hathi / Tata Ace (small) | ₹800–1,500 | Hourly rate also listed (₹200–400/hr) for very short local moves |
| Mini truck (up to 750 kg) | ₹800–1,500 | Broadly overlaps with Chota Hathi band |
| Pickup / Bolero (up to 1.5 ton) | ₹1,200–2,500 | Larger capacity, higher base cost |

**Key structural finding:** for short intra-city distances, local goods transport in India is priced predominantly as a **near-fixed per-trip/per-hour charge**, not a small linear per-km rate. The commonly assumed "₹10–25/km" benchmark (validated in the Phase 1A audit) applies to longer-haul trips where the base charge is amortized over more distance; it understates the effective per-unit cost of a short 1–5 km local collection run, where the base fare dominates. **Recommended V1 transport model:**

$$TransportCost \approx \text{flat local-trip charge (₹800–1,500 for the smallest suitable vehicle class)}$$

rather than a base+per-km formula, until primary quotes from local operators or informal transport (auto goods-carriers, cycle-carts) are collected — no public rate data was found for the smallest, cheapest vehicle classes (shared auto-carrier, e-cart, cycle-rickshaw) that a short, low-volume vendor-cluster run would likely actually use, which is a real gap and a priority for the next round of primary data collection, since it could materially improve the break-even math shown in Section 9.

---

## 7. Geographic Feasibility

No dedicated dataset on street-vendor spatial density or realistic pickup distances was found this phase (🔴 gap). Reasoning from the transport-cost finding above: because local transport cost is dominated by a fixed trip charge rather than distance, the *practical* geographic constraint is less about maximum distance in km and more about whether a single trip can visit a genuinely small, walkable cluster (favoring foot/handcart/cycle-cart delivery, which is likely much cheaper than motorized transport, though not quantified here) versus needing a motorized vehicle (which only pays off once the order is large enough per Section 9).

**Recommendation for V1:** use a conservative, non-arbitrary starting radius of **1–2 km** (roughly a 15–20 minute walk/handcart distance in a dense Indian urban market area), explicitly labeled 🟡 experimental, to be validated or revised against real vendor location data collected in the primary survey. Do not adopt 5–10 km radii from the earlier draft without evidence — at that distance, motorized transport becomes necessary and the fixed-trip-charge economics of Section 6 apply in full, raising the break-even bar.

---

## 8. Group Size and Demand Scenarios

🔴 No public vendor-demand dataset exists (confirmed in Phase 1A and again here). The following are **🟡 experimental scenario assumptions only**, to be calibrated later against 🔵 primary survey data — they are not claimed as real vendor behavior.

| Scenario | Assumed demand per vendor per day | Vendors needed to reach 50 kg/day (≈break-even zone, see Section 9) |
|---|---|---|
| Low demand | 2 kg | 25 vendors |
| Medium demand (used in Section 9's base case) | 5 kg | 10 vendors |
| High demand | 8 kg | 7 vendors |

These figures should be treated purely as scenario boundaries for stress-testing the model, not as design targets, until the primary survey (already planned in the data-strategy phase) produces real per-vendor daily quantities.

---

## 9. Back-of-the-Envelope Economic Analysis

Base case: 10 vendors, 5 kg/vendor/day (🟡 experimental demand assumption) → 50 kg group order; transport cost band ₹800–1,500 (🟢 real, Section 6); wholesale/retail prices 🟢 real per Section 5; handling excluded from the base case (🔴 no data).

| Commodity | Group Size | Total Demand | Individual Cost (@ retail) | Group Commodity Cost (@ wholesale) | Transport Cost | Handling | Total Group Cost | Net Savings | Viable? |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Tomato | 10 | 50 kg | ₹1,575 | ₹500 | ₹800–1,500 | ₹0 (excluded) | ₹1,300–2,000 | **₹275 to −₹425** | 🟡 Marginal — viable only at the low end of the transport-cost range |
| Onion | 10 | 50 kg | ₹3,125 | ₹2,000 | ₹800–1,500 | ₹0 | ₹2,800–3,500 | **₹325 to −₹375** | 🟡 Marginal — same pattern |
| Potato | 10 | 50 kg | ₹1,750 | ₹600 | ₹800–1,500 | ₹0 | ₹1,400–2,100 | **₹350 to −₹350** | 🟡 Marginal — same pattern |

**Honest reading of this table:** at exactly this group size and demand assumption, the model sits right on the break-even line — it is not a clear win. It only becomes clearly profitable once the group is somewhat larger (Section 10) or the transport option is cheaper than a motorized mini-truck (an unquantified but plausible possibility for very short distances, per Section 6). This is not the "everything works great" result a favorable-numbers exercise would produce, and it is not the "nothing works" result a pivot would require — it is a genuine, narrow, testable middle case.

---

## 10. Break-Even Analysis

$$BreakEvenQuantity = \frac{TransportCost}{SavingsPerUnit}$$

| Commodity | Savings/kg | Break-even @ ₹800 transport | Break-even @ ₹1,500 transport |
|---|---:|---:|---:|
| Tomato | ₹21.5 | **37.2 kg** | **69.8 kg** |
| Onion | ₹22.5 | **35.6 kg** | **66.7 kg** |
| Potato | ₹23.0 | **34.8 kg** | **65.2 kg** |

Translated to vendor count at the 🟡 5 kg/vendor/day assumption: break-even requires roughly **7–8 vendors** at the cheapest realistic local transport cost, rising to **13–14 vendors** at the more expensive end of the realistic local transport range.

**Maximum transport cost that preserves viability for a 50 kg order:** Tomato ₹1,075, Onion ₹1,125, Potato ₹1,150. Since the real observed local transport band tops out at ₹1,500 (and can reach ₹2,500 for larger vehicles), a 50 kg order is viable only if the *cheapest* available local transport option is used — reinforcing that transport-mode choice (smallest suitable vehicle, or non-motorized options where feasible) is a first-order design decision, not a minor detail.

**Important caution on the wholesale price used:** these calculations use the raw mandi average price. Phase 1A established that individual vendors (and, most likely, a vendor collective) cannot buy directly at the mandi auction without trader registration — real access will likely be through a registered trader/commission agent charging a margin on top of the mandi price. If that margin is even 10–15%, the effective savings per kg shrink meaningfully and break-even quantities rise correspondingly. **The figures in this section should be read as a best-case / upper-bound estimate**, not a guaranteed outcome — a genuine limitation, not a favorable assumption.

---

## 11. Price Volatility Analysis

Tomato prices in India are well-documented as highly volatile — 🟢 real reporting shows tomato wholesale/retail prices swinging from crisis lows of ₹3–10/kg to spikes many multiples higher within the same year, driven by seasonal supply shocks. This is a well-established pattern in Indian agricultural markets, not specific to this audit's snapshot data. Onion is also seasonally volatile (well-documented recurring "onion price crisis" cycles in Indian news/policy discourse), though generally less extreme day-to-day than tomato. Potato tends to be comparatively more stable.

**Direct answer to the design question this phase was asked to resolve:** yes, a single day's wholesale price advantage is *not* reliably stable, especially for tomato — this is a strong, evidence-backed justification for the system's core design principle of re-evaluating viability **daily** against the latest available price, rather than assuming a fixed savings margin. This finding directly validates one of the most important architectural decisions already in your refined problem statement.

*(This audit did not pull a full multi-week time series to quantify day-to-day standard deviation numerically — that would need to be done with the primary Agmarknet API pull in Phase 1C/data-collection, not this feasibility pass. Flagged here as a next step, not fabricated.)*

---

## 12. Freshness and Spoilage Analysis

🟢 Real data found: FAO's postharvest handling reference gives **refrigerated** storage life of 8–10 days (red/ripe tomato, 8–10°C, 90–95% RH) or 14–21 days (mature-green tomato, 12.5–15°C). No ambient-temperature figure was found in the sources reviewed this phase.

⚠️ **REASONABLE ASSUMPTION, not verified this phase:** ambient shelf life for ripe tomatoes at typical Indian outdoor/market temperatures (often 25–35°C) is expected to be substantially shorter than the refrigerated figures above — commonly cited in general food-science literature as roughly 2–5 days at room temperature — but this specific ambient figure was not independently confirmed against a primary source in this audit and must be verified (or replaced with a primary observation) before being used in the actual system.

Onion and potato are, by well-established general knowledge, long-shelf-life commodities at ambient temperature (typically weeks to months under reasonable storage), so they do not face this tension in any realistic V1 scenario.

**Testing the tension for tomato**, using ConsumptionDays = OrderQuantity ÷ Group Daily Demand, group daily demand = 50 kg (10 vendors × 5 kg, 🟡 assumption):

| Scenario | Order size | Consumption Days | vs. assumed 2–5 day ambient window | Risk |
|---|---:|---:|---|---|
| 1 — Buy exactly one day's need | 50 kg | 1.0 day | Well within window | 🟢 Low risk |
| 2 — Buy for 3 days (fewer trips, spreads transport cost further) | 150 kg | 3.0 days | At or near the upper bound of the assumed window | 🟡 Moderate risk |
| 3 — Buy for 5 days (maximize transport-cost amortization) | 250 kg | 5.0 days | At or beyond the assumed window | 🔴 High risk |

This demonstrates the real tension the whole project is designed around: buying more to better amortize the fixed transport cost (Scenario 3 spreads the ₹800–1,500 trip cost over 5× more units than Scenario 1, meaningfully improving per-unit economics) directly increases spoilage risk for a short-shelf-life commodity. **For onion and potato, Scenario 3's equivalent creates no meaningful risk at all**, which is exactly why this audit recommends leading with those two commodities.

---

## 13. Payment and Cash-Flow Feasibility

Phase 1A found that a substantial share of vendors (🟢 ~48% in the WIEGO/Bhowmik multi-city study) already operate on wholesaler-advance/credit arrangements, settling daily after sale, rather than paying cash upfront.

| Payment Model | Trust Requirement | Cash-Flow Risk (for vendor) | Technical Complexity | Realism given field evidence | Suitable for V1? |
|---|---|---|---|---|---|
| 1. All vendors pre-pay | High (must trust platform/organizer with cash upfront) | High — mismatches existing credit-based habits for ~half the population | Low | Low | ❌ No |
| 2. Deposit + balance on delivery/sale | Medium | Medium | Medium | Medium | 🟡 Possible, worth piloting |
| 3. Pay-on-delivery | Low-Medium | Low | Medium | High — closest to existing wholesaler-advance norms | ✅ Best fit for V1 |
| 4. Trusted anchor/lead vendor collects and pays | Medium (concentrated trust in one person) | Medium (anchor bears risk) | Low (no new payment tech needed) | High — mirrors informal community trust patterns already documented (e.g., SEWA-style vendor coordination) | ✅ Strong, low-tech V1 candidate |
| 5. Partner wholesaler/aggregator extends credit to the group (as they already do individually) | Low for vendors, shifts risk to the trader | Low for vendors | Low — no new fintech needed | High — directly extends the existing 48%-advance-credit norm to a group context | ✅ Strongest fit, and consistent with the "partner trader" market-access assumption already in the refined problem statement |

**Recommendation:** do not design a new fintech/escrow solution for V1. Models 3, 4, and 5 all extend existing, evidenced informal-sector payment norms rather than requiring vendors to change behavior, and Model 5 in particular is consistent with the market-access assumption (routing through a partner trader/commission agent) already built into the refined problem statement — the two design pieces reinforce each other.

---

## 14. Data Gap Audit

| Variable | Data Type | Source | Accessibility | Reliability | V1 Strategy |
|---|---|---|---|---|---|
| Wholesale/mandi price | 🟢 Real public data | Agmarknet/data.gov.in | High (free API) | Medium — verify units and cross-check against a second date before trusting any single pull | Use official API, not aggregator sites |
| Retail/alternative price | 🟢 Real public data | Price Monitoring System (fcainfoweb.nic.in) | Medium (web-report generation, not clean API) | Medium | Script the report generation; cross-check against Agmarknet-adjacent commodities |
| True vendor procurement price | 🟡 Currently difficult to obtain | None public | Low | N/A | 🔵 Primary survey required — highest-priority data gap |
| Vendor demand quantity | 🟠 Scenario/synthetic required for now | None public | Low | N/A | 🔵 Primary survey required; use scenario bounds (Section 8) only for stress-testing until then |
| Vendor location/geographic density | 🔴 Currently difficult to obtain | None found | Low | N/A | 🔵 Primary field observation required |
| Transport cost (motorized) | 🟢 Real public data | Commercial rental listings | High | Medium (static listings, not live quotes) | Use as a bounded range; get 2–3 real local quotes to tighten it |
| Transport cost (non-motorized/informal, e.g. handcart) | 🔴 Currently difficult to obtain | None found | Low | N/A | 🔵 Primary data collection — high priority, could materially change the break-even result |
| MOQ | 🔴 Currently difficult to obtain | None public | Low | N/A | 🔵 Primary survey/trader interview required; do not invent |
| Shelf life (refrigerated) | 🟢 Real public data | FAO postharvest manuals | High | High | Use directly |
| Shelf life (ambient) | 🟡 Reasonable assumption only | Extrapolated, not directly sourced | Low | Low | 🔵 Primary observation or a dedicated ambient-storage literature search required before final use |
| Payment/settlement behavior | 🟢 Real public data (qualitative) | WIEGO/Bhowmik field study | Medium | Medium (multi-city study, not India-wide census) | Use to justify Models 3–5 in Section 13; primary survey should confirm locally |
| Vendor category | 🔵 Primary data required | None public at the needed granularity | Low | N/A | Primary survey |

---

## 15. Assumptions and Limitations

**VERIFIED FACTS**
- Real wholesale-retail price spreads of 36–68% exist for tomato, onion, and potato in Hyderabad on the sampled dates (with the data-quality caveat in Section 3a).
- Local intra-city motorized transport in Hyderabad is priced primarily as a near-fixed per-trip charge of ₹800–2,500, not a small linear per-km rate.
- FAO reference data confirms tomato's refrigerated shelf life is far shorter than onion's or potato's ambient shelf life, a directionally reliable finding even before ambient-specific figures are confirmed.
- A documented share of Indian street vendors already transact on credit/advance terms with suppliers, not cash-upfront.

**PRIMARY DATA REQUIRED (blocking, before final model calibration)**
- Actual vendor procurement prices (vs. consumer retail price).
- Actual per-vendor daily demand quantities, by commodity and vendor category.
- Real MOQ figures from local traders/commission agents.
- Vendor geographic density and realistic clustering distances.
- Cost of non-motorized/informal local transport options.

**EXPERIMENTAL ASSUMPTIONS (used only for stress-testing in this report, not claimed as real)**
- 5 kg/vendor/day demand.
- 10-vendor base-case group size.
- 1–2 km clustering radius.
- Ambient tomato shelf life of 2–5 days (extrapolated downward from refrigerated data, not independently confirmed).
- Handling cost excluded (treated as ₹0) in the base case.

**LIMITATIONS (explicitly out of scope for V1 as currently evidenced)**
- Cooking oil does not fit the mandi-price-spread model and should be dropped or separately modeled.
- Distribution costs beyond a single collection point (multi-stop last-mile delivery) are not modeled.
- The wholesale price used is the raw mandi average, not an adjusted "effective access price" including a likely trader margin — real savings are probably somewhat lower than calculated here.
- No quantified day-to-day price-volatility statistic was computed this phase (qualitative evidence only).

---

## 16. FINAL GO / MODIFY / PIVOT VERDICT

**🟡 MODIFY.**

**1. Can collaborative procurement realistically save money?** Yes, for at least two of the three commodities tested, but the margin is narrower than the original problem statement implied — it is a real but modest opportunity, not a dramatic one, once real transport costs are included.

**2. Under what conditions?** A group order needs to reach roughly 35–70 kg per commodity to break even against realistic local transport costs, and the cheapest available local transport option must be used — the model does not comfortably clear break-even at the more expensive end of the observed transport-cost range.

**3. For which commodities?** Onion and potato are the strongest V1 candidates — the price spread is real and there is no meaningful freshness tension at any economically-relevant order size. Tomato is economically similar but freshness-constrained: it is a valid and valuable "hard case" to demonstrate the system's core intelligence, but should not be the commodity used to prove the concept first. Cooking oil should be dropped from the initial commodity set.

**4. At what group size?** Roughly 7–8 vendors at the cheapest realistic transport cost, rising to 13–14 vendors at the more expensive end — under an unverified 5 kg/vendor/day demand assumption that must be replaced with real survey data.

**5. At what approximate demand quantity?** 35–70 kg per group order per commodity, per the break-even calculation in Section 10.

**6. How sensitive is the model to transportation cost?** Highly sensitive — the difference between the cheap end (₹800) and expensive end (₹1,500) of the realistic local transport range roughly doubles the required break-even quantity. This is the single most important lever in the whole model, more important than the price spread itself.

**7. Does perishability significantly restrict the model?** Yes, but selectively — it is a binding, real constraint for tomato and (by extension) leafy greens, and essentially irrelevant for onion and potato. This is exactly the kind of commodity-dependent nuance the proposed AI/optimization system is meant to capture, which is a point in favor of the project's core design, not against it.

**8. Is the project economically feasible?** Yes, conditionally — for a narrower commodity set (leading with onion/potato, tomato as a stress-test case, oil deferred) and at group sizes in the 8–15 vendor range, using the cheapest available local transport mode. It is not unconditionally feasible across "vegetables, milk, oil, spices, packaging" as the original problem statement listed.

**9. What MUST change before moving to the next phase?**
- Narrow the initial commodity set to onion and potato as the primary proof-of-concept, keep tomato as the deliberate hard case, and drop cooking oil.
- Replace the base+per-km transport formula with a near-fixed local-trip-charge model, and prioritize primary data collection on cheaper non-motorized transport options (handcart/cycle-cart), which could materially improve viability if real numbers support it.
- Run the actual primary vendor survey (already planned) with explicit questions on per-vendor daily quantity, current procurement price and payment arrangement (cash vs. credit/advance), and willingness to participate in a pay-on-delivery or anchor-vendor payment model.
- Pull matched, same-day, unit-verified wholesale (Agmarknet API) and retail (PMS) prices directly from primary sources before finalizing any numbers used in the paper — do not reuse this report's aggregator-derived figures as final.
- Treat the wholesale price used in all future calculations as a best-case figure and test sensitivity to a 10–15% trader-margin adjustment, given the confirmed mandi-registration/market-access constraint from Phase 1A.

---

## Sources

- [Bowenpally Wholesale Mandi Market prices, napanta.com](https://www.napanta.com/market-prices)
- [Today's Vegetable Price in Hyderabad, market.todaypricerates.com](https://market.todaypricerates.com/Hyderabad-vegetables-price-in-Telangana)
- [Variety-wise daily market prices data (commodity) — data.gov.in](https://www.data.gov.in/resource/variety-wise-daily-market-prices-data-commodity)
- [Daily/weekly Retail prices of Sunflower Oil (Packed) — data.gov.in](https://www.data.gov.in/catalog/dailyweekly-retail-prices-sunflower-oil-packed)
- [Daily/weekly Retail prices of Groundnut Oil (Packed) — data.gov.in](https://www.data.gov.in/catalog/dailyweekly-retail-prices-groundnut-oil-packed)
- [Mini Truck / Chota Hathi rental rates, Hyderabad — thetransporter.in](https://www.thetransporter.in/mini-truck-for-rent/chota-hathi-services-online-booking-in-hyderabad)
- [FAO, Manual for the preparation and sale of fruits and vegetables (storage-life table)](https://www.fao.org/4/y4893e/y4893e06.htm)
- [Tomato prices hit 3-year low at ₹3–10/kg — Deccan Chronicle / PressReader](https://www.pressreader.com/india/deccan-chronicle/20200523/281943135083932)
- [Tomato mandi price today — farmer.in](https://farmer.in/mandi-bhav/tomato/)
- [Bhowmik, *Hawkers and the Urban Informal Sector*, WIEGO](https://www.wiego.org/wp-content/uploads/2019/09/Bhowmik-Hawkers-URBAN-INFORMAL-SECTOR.pdf) *(carried forward from Phase 1A, re-used for payment-behavior evidence in Section 13)*
