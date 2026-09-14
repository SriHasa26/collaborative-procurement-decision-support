# Problem Statement G (Refined): AI-Driven Collaborative Procurement Decision System for Street Vendors

## Problem Statement

Individual street food and goods vendors (protected under the Street Vendors Act, 2014, and financially supported by the PM SVANidhi scheme) buy raw materials — vegetables, oil, spices, milk, packaging — in small daily quantities at retail or semi-wholesale rates because they have no mechanism to pool demand with nearby vendors. This forces them to pay significantly more per unit than they would at true wholesale/mandi rates, directly compressing their already-thin margins. PM SVANidhi has improved vendors' access to working capital, but does nothing to address what vendors pay once they deploy that capital.

However, naive demand-pooling ("just cluster nearby vendors and buy together") does not reliably solve this, because bulk buying is not always beneficial. Five real-world constraints determine whether a given bulk order actually helps a given group of vendors on a given day:

1. **Price volatility** — the wholesale-retail price gap fluctuates daily and can shrink or invert; yesterday's favorable spread may not hold today.
2. **Logistics cost** — transporting goods from a mandi/wholesaler to vendor locations has a real cost that can exceed the savings a group achieves, especially for small orders or dispersed vendors.
3. **Perishability** — most street-vendor raw materials (vegetables, milk, leafy greens) spoil quickly; a bulk quantity large enough to hit wholesale pricing may exceed what a small vendor cluster can consume before it degrades, converting "savings" into waste.
4. **Minimum order quantities** — wholesalers/traders often require a minimum volume to offer wholesale pricing, but a volume large enough to satisfy that minimum can simultaneously be too large to consume safely (constraint 3), creating a genuine conflict the system must resolve.
5. **Market access** — Indian mandis (APMC markets) restrict auction participation to registered traders/wholesalers/retailers; individual street vendors (or an informal collective of them) cannot walk onto the mandi floor and buy at auction price directly. Wholesale access in practice requires routing through a registered trader or commission agent (arhatiya).

No existing platform — government or private — evaluates all five of these together to answer the actual operational question: **"Should this specific group of vendors buy raw materials together today, and if so, how much?"**

## Novelty

A structured search found no platform performing demand-aggregation / group bulk-buying coordination specifically for Indian street vendors. The closest analogues were checked directly and ruled out:

- **PM SVANidhi** — purely a micro-credit and digital-cashback scheme; no bulk-purchasing or wholesale-matching functionality.
- **Ninjacart** — a real B2B fresh-produce marketplace, but explicitly serves kirana stores, retailers, and restaurants, not itinerant street vendors.
- **Otipy** — India's largest community/social group-buying platform for fresh produce, but B2C (households/resellers), scheduled-order based, with no price/logistics/freshness viability-decision engine and no vendor-specific framing.

At the same time, the *general* decision problem — joint procurement of perishable goods under quantity-discount and shelf-life constraints — is an established area in operations research (e.g., joint procurement/pricing models for fresh produce under quantity-discount contracts, and economic-order-quantity models for perishables). The project's genuine contribution is therefore **not** claiming to invent this decision problem, but **adapting and applying it to the underserved Indian street-vendor context**: real government mandi and retail price data, informal-sector logistics constraints, trader-mediated market access, and low-capital, mobile, itinerant buyers — a combination no existing system addresses.

## Feasibility (Data Strategy)

A hybrid framework combining verified real data, primary field data, platform-generated data, and calibrated synthetic data:

**Real government data**
- *Agmarknet* (via the data.gov.in API) — daily wholesale max/min/modal prices across 3,000+ mandis and 200+ commodities. Access is a standard free registration (data.gov.in account → API key → REST calls), well documented and widely used; Hyderabad/Telangana-area mandis (e.g., Madannapet) are covered. Do not rely on unofficial "keyless" wrapper APIs — they only cover five states and exclude Telangana.
- *Department of Consumer Affairs Price Monitoring System* (fcainfoweb.nic.in) — daily retail **and** wholesale prices for 38 essential commodities across hundreds of monitored centres nationwide. This lets the project cross-validate vendor-reported retail prices against an independent government source rather than relying on self-report alone.

**Primary vendor data**
- A small field study of 10–20 vendors, tracked daily for 7–14 days (not a one-shot survey), capturing category, commodities, quantities, purchase frequency, actual price paid, and purchase source. Includes a brief informed-consent statement, since this is human-subject data collection even at small scale.

**Platform-generated data**
- From day one, every vendor interaction is logged (onboarding profile, actual purchases), so the system accumulates real historical demand data for production use over time, even though this isn't required for the initial research evaluation.

**Calibrated synthetic data**
- Used only to scale up algorithm evaluation (batching/optimization stress-testing), generated by sampling from distributions whose parameters are fit to the real survey data — never presented as real, always reported transparently as a calibrated simulation.

**Explicit operating assumption:** because direct mandi-floor access requires trader registration, the platform is designed to route aggregated orders through a partner registered trader or commission agent rather than assuming vendors bid at auction directly. Minimum order quantities and effective wholesale prices are therefore treated as parameters obtained from trader interviews or secondary sources, not invented constants — and this also simplifies the logistics model, since a partner trader typically already has transport arrangements in place.

## Proposed Solution

An AI-powered collaborative procurement platform whose core intelligence is a **daily viability decision**, not an assumption that grouping vendors is automatically beneficial.

1. **Vendor onboarding** — location, category (chaat/fruit/tea stall/etc.), and typical commodities/quantities, forming a cold-start demand profile.

2. **Hybrid demand forecasting** — new vendors are predicted from category-level patterns (similar vendors' historical demand); as a vendor's own transaction history accumulates, the system shifts toward a personalized model (moving-average baseline, then Random Forest/LightGBM using previous demand, 7-day average, day-of-week, category, and commodity as features). This is explicitly a hierarchical/backoff forecasting approach, a recognized technique for sparse-data settings, not an invented heuristic.

3. **Uncertainty-aware order sizing** — forecasts carry a confidence range; order quantities are chosen conservatively for highly perishable goods and closer to the upper estimate for non-perishables. This is an application of the classical **newsvendor model** (ordering under demand uncertainty with asymmetric overage/underage cost), the standard OR framework for exactly this tradeoff.

4. **Daily economic viability check** — pulls the latest available Agmarknet wholesale price and PMS-cross-validated retail price to compute individual procurement cost vs. group procurement cost (commodity + transport + handling); proceeds only if net savings are positive.

5. **Logistics-aware feasibility** — a single-stage transport cost model for the initial build (base cost + distance × per-km rate, calibrated against real mini-truck rental rates of roughly ₹10–25/km) from the wholesaler/trader to a chosen micro-collection point; a group is only formed if transport cost is less than gross savings. A more elaborate two-stage hub-and-spoke model (mandi → collection hub → vendors, with facility-location optimization) is documented as a future extension rather than built in the initial version, to keep scope realistic.

6. **Freshness-aware quantity capping** — using shelf-life figures sourced from literature (USDA ARS *Commercial Storage of Fruits, Vegetables, and Florist and Nursery Stocks*, and India's National Centre for Cold-Chain Development) rather than invented numbers, the system computes `ConsumptionDays = BulkQuantity / PredictedDailyDemand` and caps the recommended order so `ConsumptionDays ≤ FreshnessWindow`, preventing spoilage-driven waste.

7. **MOQ handling** — aggregated demand is checked against the partner trader's minimum order threshold; if unmet, the system either waits, expands the vendor cluster, or falls back to recommending individual purchase.

8. **Batching/optimization engine** — clusters geographically proximate, demand-compatible vendors into groups that jointly satisfy all constraints (positive savings, transport cost below savings, MOQ met, freshness safe, distance within range), formulated as a constrained clustering / bin-packing-style optimization. Evaluation is based on net rupee savings and constraint-feasibility rate, not on an arbitrary weighted "viability score" — a composite score may exist as a cosmetic dashboard element, but is not used as the paper's core evaluation metric, since its weights would be unjustifiable without real preference data.

9. **Vendor dashboard** — shows each vendor the day's recommendation (buy today / don't buy today), estimated savings, and the reasoning behind it (price advantage, logistics cost, freshness safety), grounded in real Agmarknet/PMS price differentials as the baseline.

## Research Paper Angle

Using real Agmarknet and Price Monitoring System data together with the calibrated survey/synthetic demand dataset:

- Quantify what fraction of vendor-cluster-days a bulk purchase is actually economically, logistically, and freshness-viable, compared against a naive "always cluster" baseline.
- Run a sensitivity analysis identifying the transport-cost or distance threshold at which collaborative buying stops being beneficial.
- Compare batching strategies (geography-only clustering vs. demand-similarity clustering vs. the combined constrained optimization) on cost-savings-to-order-size and spoilage-risk tradeoffs.
- Compare newsvendor-style conservative ordering against naive mean-forecast ordering on realized savings vs. realized waste, separately for perishable and non-perishable commodity subsets.
- Position the work explicitly against the joint-procurement-under-perishability OR literature as related work, framing the contribution as a context-specific adaptation grounded in real Indian market data and informal-sector constraints.

## Government/Institutional Hook

"PM SVANidhi solved vendor access to capital. This solves the next problem — what happens to that capital once vendors spend it on raw materials — and does so responsibly, by verifying real economic, logistical, and freshness viability before recommending a bulk purchase, rather than assuming pooling demand is always beneficial."

## Scoping: V1 vs. Future Work

**Build for the mini-project (V1):**
Agmarknet + Price Monitoring System integration; cost/break-even model; single-stage transport cost model; freshness cap using literature-sourced shelf-life values; cold-start + personalized hybrid forecaster (moving average baseline, then Random Forest/LightGBM); newsvendor-style uncertainty-aware order sizing; constrained batching/optimization engine; vendor dashboard; primary survey (10–20 vendors × 7–14 days) plus calibrated synthetic expansion for scale testing.

**Document but do not build (future work):**
Two-stage hub-and-spoke logistics with facility-location optimization; computer-vision-based freshness detection; genuinely real-time pricing; a full payment-splitting/settlement system; weather-based demand features.
