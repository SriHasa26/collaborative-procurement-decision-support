// UI-2 -- premium landing page. Composes the sections below in the
// brief's own intended order (Hero -> Value -> How it works -> Decision
// intelligence -> Product preview -> Differentiators -> Final CTA);
// Navigation and Footer live in LandingLayout.jsx (the route wrapper for
// "/" only -- see routes/AppRoutes.jsx), not here.
//
// Superseded from Phase 7B: the old bare hero/workflow/"decision
// transparency grid of all four states"/dev-diagnostic layout. The
// "developer diagnostic" BackendStatusCheck card is intentionally removed
// (its own Phase 7A docstring anticipated exactly this: "A later phase
// ... will replace or remove this" -- a raw connectivity-check box has no
// place on a public, judge-facing landing page). No backend call is made
// anywhere on this page; every figure shown is either a capability
// statement or an explicitly-labeled "Example"/"Demo Scenario" -- see
// DecisionIntelligence.jsx/ProductPreview.jsx.

import DecisionIntelligence from "../components/landing/DecisionIntelligence";
import Differentiators from "../components/landing/Differentiators";
import Hero from "../components/landing/Hero";
import HowItWorks from "../components/landing/HowItWorks";
import LandingCTA from "../components/landing/LandingCTA";
import ProductPreview from "../components/landing/ProductPreview";
import ValueMetrics from "../components/landing/ValueMetrics";

function HomePage() {
  return (
    <>
      <Hero />
      <ValueMetrics />
      <HowItWorks />
      <DecisionIntelligence />
      <ProductPreview />
      <Differentiators />
      <LandingCTA />
    </>
  );
}

export default HomePage;
