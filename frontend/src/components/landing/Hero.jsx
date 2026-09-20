// UI-2 -- the primary landing hero. "Start an Analysis" routes to
// /analyze directly -- for a signed-out visitor, the existing
// ProtectedRoute (unchanged) redirects to /signin and returns them to
// /analyze afterward, reusing the already-tested flow rather than
// inventing a new one.

import Button from "../common/Button";
import FloatingLines from "./FloatingLines";
import HeroNetwork from "./HeroNetwork";

// Hero background line color refinement -- white -> sky blue -> blue -> navy
// (replacing the earlier pink/magenta palette), weighted toward the lighter
// end so the lines read as restrained "data flow" rather than neon glow.
// lineCount below is 8, so with exactly 8 stops each stop maps ~1:1 to one
// line per wave, giving direct control over the white/sky/blue/navy mix
// instead of a smooth blend that would wash the distribution out. The two
// darker stops reuse this project's own --color-primary and --color-midnight
// token values (variables.css) rather than inventing new brand colors; sky
// blue has no existing token, so a literal is used for just that one stop.
const HERO_LINE_GRADIENT = [
  "#ffffff", // bright white -- primary highlight
  "#ffffff",
  "#f0f8ff", // soft white
  "#f0f8ff",
  "#7dd3fc", // sky blue -- primary flowing energy
  "#7dd3fc",
  "#2f54eb", // medium/deep blue -- same value as --color-primary
  "#0b1220", // deep navy -- same value as --color-midnight
];

function Hero() {
  return (
    <section className="hero-section">
      <div className="hero-floating-lines" aria-hidden="true">
        <FloatingLines
          enabledWaves={["top", "middle", "bottom"]}
          lineCount={8}
          lineDistance={8}
          bendRadius={8}
          bendStrength={-2}
          interactive
          parallax
          animationSpeed={1}
          linesGradient={HERO_LINE_GRADIENT}
        />
      </div>
      <div className="hero-inner">
        <div className="hero-copy animate-in">
          <p className="eyebrow">Collaborative Procurement Intelligence</p>
          <h1 className="hero-headline">
            Turn fragmented demand into smarter procurement decisions.
          </h1>
          <p className="text-body">
            Discover compatible vendors, evaluate collaborative procurement opportunities, and
            quantify the savings behind every recommendation — through transparent, rule-based
            evaluation, not a black box.
          </p>
          <div className="hero-actions">
            <Button to="/analyze" variant="primary">
              Start an Analysis
            </Button>
            <Button href="#how-it-works" variant="outline">
              See How It Works
            </Button>
          </div>
        </div>

        <HeroNetwork />
      </div>
    </section>
  );
}

export default Hero;
