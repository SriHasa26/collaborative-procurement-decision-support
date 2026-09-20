// Landing polish -- a small, focused IntersectionObserver hook: reports
// whether an element has entered the viewport, ONCE (the observer
// disconnects itself the first time it fires, so it never toggles back
// to false on scroll-away and never re-triggers on scroll-back -- exactly
// this task's own "play once, settle into a final state, never replay"
// requirement). No polling, no setInterval, no continuous work after the
// one observation. Falls back to "already in view" immediately if
// IntersectionObserver is unavailable, so content is never stuck hidden.
//
// This is a presentation-only utility -- it carries no business/
// procurement logic and computes nothing about the actual data. Takes no
// options (every call site here wants the same 25%-visible threshold) --
// kept deliberately parameter-free so the setup effect has nothing
// reactive to depend on and can run exactly once, cleanly.

import { useEffect, useRef, useState } from "react";

export function useInViewOnce() {
  const ref = useRef(null);
  const [isInView, setIsInView] = useState(typeof IntersectionObserver === "undefined");

  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return undefined;
    const node = ref.current;
    if (!node) return undefined;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { threshold: 0.25 }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return [ref, isInView];
}
