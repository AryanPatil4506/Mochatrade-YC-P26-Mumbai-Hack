import { useEffect, useRef, useState } from "react";

// Animates a number from its previous value to `target` over `duration`ms.
// Used by RiskGauge for its ~600ms count-up animation.
export function useCountUp(target: number, duration = 600): number {
  const [value, setValue] = useState(target);
  const fromRef = useRef(target);

  useEffect(() => {
    const from = fromRef.current;
    if (from === target) return;
    const start = performance.now();
    let frame: number;

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(from + (target - from) * eased));
      if (t < 1) {
        frame = requestAnimationFrame(tick);
      } else {
        fromRef.current = target;
      }
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);

  return value;
}
