"use client";

import { useState } from "react";
import {
  ComponentLabel,
  MobileFrame,
  Screen,
  ScreenContent,
  ScreenHeader,
} from "@/components/layout";
import { NavTabs } from "@/components/orkestr/NavTabs";
import { Card } from "@/components/orkestr/Card";
import { Amount } from "@/components/orkestr/Amount";
import { Badge } from "@/components/orkestr/Badge";
import { SPLITS } from "@/lib/mock-data";

const TABS = [
  { id: "active", label: "Active" },
  { id: "owed", label: "You owe" },
  { id: "settled", label: "Settled" },
];

export default function NavigationPage() {
  const [activeTab, setActiveTab] = useState("active");

  const filtered = SPLITS.filter((split) => {
    if (activeTab === "active") return split.status === "active" || split.status === "pending";
    if (activeTab === "owed") return split.status === "active";
    return split.status === "settled";
  });

  return (
    <MobileFrame>
      <Screen>
        <ScreenHeader title="Your splits" subtitle="Navigation tabs component" backHref="/" />
        <NavTabs tabs={TABS} activeId={activeTab} onChange={setActiveTab} />
        <ScreenContent soft>
          <div style={{ paddingTop: "var(--space-lg)" }}>
            <ComponentLabel>
              {TABS.find((t) => t.id === activeTab)?.label} splits
            </ComponentLabel>
          </div>
          <div className="stack-sm" style={{ marginTop: "var(--space-md)" }}>
            {filtered.map((split) => (
              <Card key={split.id}>
                <div className="row-between">
                  <div>
                    <p className="text-body-md-strong">{split.title}</p>
                    <p className="text-caption">{split.date}</p>
                  </div>
                  <Amount value={split.yourShare} size="sm" />
                </div>
                <div style={{ marginTop: "var(--space-md)" }}>
                  <Badge
                    variant="status"
                    statusDot={
                      split.status === "settled"
                        ? "complete"
                        : split.status === "active"
                          ? "active"
                          : "pending"
                    }
                  >
                    {split.status === "settled"
                      ? "Settled"
                      : split.status === "active"
                        ? "Collecting"
                        : "Pending"}
                  </Badge>
                </div>
              </Card>
            ))}
            {filtered.length === 0 ? (
              <Card variant="surface">
                <p className="text-body-sm">No splits in this tab.</p>
              </Card>
            ) : null}
          </div>
        </ScreenContent>
      </Screen>
    </MobileFrame>
  );
}
