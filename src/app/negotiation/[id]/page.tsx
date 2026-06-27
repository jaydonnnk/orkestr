"use client";

import { useState, useEffect } from "react";
import personasData from "../../../../data/personas.json";
import { MobileFrame, Screen, ScreenContent } from "@/components/layout";

/* ── Personas ─────────────────────────────────────────────────────────── */
const PERSONA_COLORS: Record<string, { bg: string; text: string }> = {
  "P-001": { bg: "#FBF0EC", text: "#B03A1A" },
  "P-002": { bg: "#FDF4E3", text: "#7A5500" },
  "P-003": { bg: "#F7F6F3", text: "#3D3A35" },
  "P-004": { bg: "#FBF0EF", text: "#8B2020" },
  "P-005": { bg: "#F0EEE9", text: "#4A4740" },
};

const PERSONAS = personasData.map((p) => ({
  id: p.id,
  initials: p.name[0],
  ...PERSONA_COLORS[p.id],
}));

/* ── Negotiation states ───────────────────────────────────────────────── */
const STEPS = [
  {
    label: "object",
    labelColor: "#D85A30",
    message: "Carol can't do Saturday",
    activeIdx: 2,
    counter: "3→2",
  },
  {
    label: "object",
    labelColor: "#D85A30",
    message: "$70/head > Bob's $40 cap",
    activeIdx: 1,
    counter: "3→2",
  },
  {
    label: "propose",
    labelColor: "#BA7517",
    message: "Seoul Garden — halal, veg, meat",
    activeIdx: 0,
    counter: "3→1",
  },
  {
    label: "accept",
    labelColor: "#00563B",
    message: "Everyone's in ✓",
    activeIdx: -1,
    counter: "1",
  },
] as const;

/* ── SVG geometry ─────────────────────────────────────────────────────── */
const CX = 140;
const CY = 132;
const RING_R = 88;
const NODE_R = 22;
const CIRC = parseFloat((2 * Math.PI * RING_R).toFixed(2));

function getNodePos(i: number) {
  const a = (-90 + i * 72) * (Math.PI / 180);
  return {
    x: parseFloat((CX + RING_R * Math.cos(a)).toFixed(2)),
    y: parseFloat((CY + RING_R * Math.sin(a)).toFixed(2)),
  };
}

const NODE_POS = PERSONAS.map((_, i) => getNodePos(i));

/* ── Component ────────────────────────────────────────────────────────── */
export default function NegotiationPage() {
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 2500);
    return () => clearInterval(id);
  }, []);

  const step = tick % STEPS.length;
  const gen = Math.floor(tick / STEPS.length);
  const current = STEPS[step];
  const visibleSteps = STEPS.slice(0, step + 1);

  return (
    <MobileFrame>
      <Screen soft>
        <style>{`
          @keyframes arcFlow {
            from { stroke-dashoffset: 0; }
            to   { stroke-dashoffset: -${CIRC}; }
          }
          @keyframes fadeInRow {
            from { opacity: 0; transform: translateY(5px); }
            to   { opacity: 1; transform: translateY(0); }
          }
        `}</style>

        <ScreenContent>
          {/* Heading */}
          <div style={{ paddingTop: "var(--space-lg)", marginBottom: "var(--space-2xl)" }}>
            <h1 className="text-display-lg">Finding your plan…</h1>
            <p className="text-body-sm" style={{ marginTop: "var(--space-sm)" }}>
              Five agents, one Friday night
            </p>
          </div>

          {/* Ring diagram */}
          <div style={{ marginBottom: "var(--space-3xl)" }}>
            <svg
              viewBox="0 0 280 264"
              style={{ width: "100%", display: "block" }}
              aria-hidden="true"
            >
              {/* Outer dashed ring — animates clockwise */}
              <circle
                cx={CX}
                cy={CY}
                r={RING_R}
                fill="none"
                stroke="var(--color-border-strong)"
                strokeWidth={1}
                strokeDasharray="7 5"
                style={{ animation: `arcFlow 6s linear infinite` }}
              />

              {/* Inner decorative ring */}
              <circle
                cx={CX}
                cy={CY}
                r={RING_R * 0.52}
                fill="none"
                stroke="var(--color-border)"
                strokeWidth={0.75}
                strokeDasharray="4 5"
              />

              {/* Agent nodes */}
              {PERSONAS.map((p, i) => {
                const { x, y } = NODE_POS[i];
                const isActive =
                  current.activeIdx === i || current.activeIdx === -1;
                return (
                  <g key={p.id}>
                    {/* Pulse ring — SVG-native animate for reliability */}
                    {isActive && (
                      <circle
                        cx={x}
                        cy={y}
                        r={NODE_R}
                        fill="none"
                        stroke="#D85A30"
                        strokeWidth={1.5}
                        opacity={0}
                      >
                        <animate
                          attributeName="r"
                          values={`${NODE_R};${NODE_R + 14}`}
                          dur="1.6s"
                          repeatCount="indefinite"
                        />
                        <animate
                          attributeName="opacity"
                          values="0.5;0"
                          dur="1.6s"
                          repeatCount="indefinite"
                        />
                      </circle>
                    )}

                    {/* Node background */}
                    <circle cx={x} cy={y} r={NODE_R} fill={p.bg} />

                    {/* Initials */}
                    <text
                      x={x}
                      y={y}
                      textAnchor="middle"
                      dominantBaseline="central"
                      fill={p.text}
                      fontSize={12}
                      fontWeight={700}
                      fontFamily="'Plus Jakarta Sans', sans-serif"
                    >
                      {p.initials}
                    </text>
                  </g>
                );
              })}

              {/* Centre counter */}
              <text
                x={CX}
                y={CY}
                textAnchor="middle"
                dominantBaseline="central"
                fill="#D85A30"
                fontSize={16}
                fontWeight={600}
                fontFamily="'Inter', sans-serif"
              >
                {current.counter}
              </text>
            </svg>
          </div>

          {/* Negotiation log */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-md)",
            }}
          >
            {visibleSteps.map((s, i) => (
              <div
                key={`${gen}-${i}`}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "var(--space-xl)",
                  animation:
                    i === step ? "fadeInRow 400ms ease both" : "none",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 11,
                    fontWeight: 500,
                    letterSpacing: "0.02em",
                    color: s.labelColor,
                    width: 48,
                    flexShrink: 0,
                    paddingTop: 2,
                  }}
                >
                  {s.label}
                </span>
                <span className="text-body-md" style={{ color: "var(--color-ink)" }}>
                  {s.message}
                </span>
              </div>
            ))}
          </div>
        </ScreenContent>
      </Screen>
    </MobileFrame>
  );
}
