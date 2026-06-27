"use client";

import {
  BottomBar,
  ComponentLabel,
  MobileFrame,
  Screen,
  ScreenContent,
  ScreenHeader,
} from "@/components/layout";
import { Button } from "@/components/orkestr/Button";
import { Input } from "@/components/orkestr/Input";
import { Card } from "@/components/orkestr/Card";

export default function InputsPage() {
  return (
    <MobileFrame>
      <Screen>
        <ScreenHeader
          title="New split"
          subtitle="Text inputs — 16px prevents iOS zoom"
          backHref="/"
        />
        <ScreenContent>
          <div className="variant-block">
            <ComponentLabel>Split details</ComponentLabel>
            <div className="stack-lg">
              <Input label="Split name" placeholder="e.g. Dinner at Trattoria" defaultValue="Weekend brunch" />
              <Input label="Total amount" placeholder="0.00" type="number" inputMode="decimal" defaultValue="84.00" />
              <Input label="Number of people" type="number" defaultValue="4" />
            </div>
          </div>

          <div className="variant-block">
            <ComponentLabel>Disabled input</ComponentLabel>
            <Input label="Split reference" value="SPL-2847" disabled readOnly />
          </div>

          <div className="variant-block">
            <ComponentLabel>Input on surface card</ComponentLabel>
            <label className="input-label" htmlFor="note">Add a note for friends</label>
            <textarea id="note" className="input" placeholder="Add a note for friends" style={{ border: "none", background: "var(--color-canvas-soft)", resize: "none" }} />
          </div>
        </ScreenContent>
        <BottomBar>
          <Button>Create split</Button>
        </BottomBar>
      </Screen>
    </MobileFrame>
  );
}
