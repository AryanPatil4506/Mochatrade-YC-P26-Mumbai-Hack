import type { ReactNode } from "react";
import { badgeStyle } from "../lib/palette";

interface Props {
  color: string;
  children: ReactNode;
}

// Small pill badge used for decision/status labels throughout the
// dashboard — purely a visual treatment of the same verdict values.
export function Badge({ color, children }: Props) {
  return (
    <span className="sentinel-badge" style={badgeStyle(color)}>
      <span className="sentinel-dot" style={{ background: color }} />
      {children}
    </span>
  );
}
