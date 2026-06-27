"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import personas from "../../../../data/personas.json";
import {
  MobileFrame,
  Screen,
  ScreenContent,
  BottomBar,
} from "@/components/layout";
import { Button } from "@/components/orkestr/Button";

const ACCENT = "var(--color-accent)";
const EVENT_NAME = "Dinner at Seoul Garden";

const bob = personas.find((p) => p.id === "P-002")!;

const DIETARY_OPTIONS: { label: string; key: string }[] = [
  { label: "No raw fish", key: "no_raw_fish" },
  { label: "Vegetarian", key: "vegetarian" },
  { label: "Halal", key: "halal" },
  { label: "Vegan", key: "vegan" },
  { label: "Gluten-free", key: "gluten_free" },
  { label: "No pork", key: "no_pork" },
];

const BUDGET_OPTIONS = [15, 30, 50, 100];
const TRAVEL_OPTIONS = [15, 30, 45, 60];

export default function PreferencesPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [dietary, setDietary] = useState<string[]>(bob.constraints.dietary);
  const [budget, setBudget] = useState(
    BUDGET_OPTIONS.reduce((prev, curr) =>
      Math.abs(curr - bob.constraints.budget_max) < Math.abs(prev - bob.constraints.budget_max)
        ? curr
        : prev
    )
  );
  const [travel, setTravel] = useState(bob.constraints.max_travel_min);

  function toggleDietary(key: string) {
    setDietary((prev) =>
      prev.includes(key) ? prev.filter((d) => d !== key) : [...prev, key]
    );
  }

  function handleSubmit() {
    console.log("Preferences submitted:", { dietary, budget, travel });
    router.push(`/negotiation/${id}`);
  }

  return (
    <MobileFrame>
      <Screen>
        <ScreenContent>
          {/* Heading */}
          <div style={{ paddingTop: "var(--space-lg)", marginBottom: "var(--space-3xl)" }}>
            <h1 className="text-display-lg">Set your constraints</h1>
            <p className="text-body-sm" style={{ marginTop: "var(--space-sm)" }}>
              {bob.name} · joining &ldquo;{EVENT_NAME}&rdquo;
            </p>
          </div>

          {/* DIETARY */}
          <section style={{ marginBottom: "var(--space-3xl)" }}>
            <p className="text-eyebrow" style={{ marginBottom: "var(--space-md)" }}>
              Dietary
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-sm)" }}>
              {DIETARY_OPTIONS.map((opt) => {
                const selected = dietary.includes(opt.key);
                return (
                  <button
                    key={opt.key}
                    type="button"
                    onClick={() => toggleDietary(opt.key)}
                    className={`tag-chip${selected ? " tag-positive" : ""}`}
                    style={{
                      minHeight: 48,
                      cursor: "pointer",
                      border: "none",
                      transition: "background 120ms ease, color 120ms ease",
                      WebkitTapHighlightColor: "transparent",
                    }}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </section>

          {/* BUDGET */}
          <section style={{ marginBottom: "var(--space-3xl)" }}>
            <p className="text-eyebrow" style={{ marginBottom: "var(--space-md)" }}>
              Budget per person
            </p>
            <div
              style={{
                display: "flex",
                border: "1px solid var(--color-border-strong)",
                borderRadius: "var(--radius-md)",
                overflow: "hidden",
              }}
            >
              {BUDGET_OPTIONS.map((amount, i) => {
                const selected = budget === amount;
                return (
                  <button
                    key={amount}
                    type="button"
                    onClick={() => setBudget(amount)}
                    style={{
                      flex: 1,
                      minHeight: 48,
                      background: selected ? ACCENT : "#fff",
                      color: selected ? "#fff" : "var(--color-mute)",
                      fontFamily: "var(--font-body)",
                      fontSize: 14,
                      fontWeight: selected ? 600 : 400,
                      fontVariantNumeric: "tabular-nums",
                      border: "none",
                      borderLeft:
                        i > 0 ? "1px solid var(--color-border-strong)" : "none",
                      cursor: "pointer",
                      transition: "background 120ms ease, color 120ms ease",
                      WebkitTapHighlightColor: "transparent",
                    }}
                  >
                    ${amount}
                  </button>
                );
              })}
            </div>
          </section>

          {/* MAX TRAVEL */}
          <section>
            <p className="text-eyebrow" style={{ marginBottom: "var(--space-md)" }}>
              Max travel (minutes)
            </p>
            <div
              style={{
                display: "flex",
                border: "1px solid var(--color-border-strong)",
                borderRadius: "var(--radius-md)",
                overflow: "hidden",
              }}
            >
              {TRAVEL_OPTIONS.map((mins, i) => {
                const selected = travel === mins;
                return (
                  <button
                    key={mins}
                    type="button"
                    onClick={() => setTravel(mins)}
                    style={{
                      flex: 1,
                      minHeight: 48,
                      background: selected ? ACCENT : "#fff",
                      color: selected ? "#fff" : "var(--color-mute)",
                      fontFamily: "var(--font-body)",
                      fontSize: 14,
                      fontWeight: selected ? 600 : 400,
                      border: "none",
                      borderLeft:
                        i > 0 ? "1px solid var(--color-border-strong)" : "none",
                      cursor: "pointer",
                      transition: "background 120ms ease, color 120ms ease",
                      WebkitTapHighlightColor: "transparent",
                    }}
                  >
                    {mins}
                  </button>
                );
              })}
            </div>
          </section>
        </ScreenContent>

        <BottomBar>
          <Button variant="primary" onClick={handleSubmit}>
            Find our plan
          </Button>
        </BottomBar>
      </Screen>
    </MobileFrame>
  );
}
