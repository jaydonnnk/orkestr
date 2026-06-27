import Link from "next/link";
import {
  BottomBar,
  MobileFrame,
  Screen,
  ScreenContent,
  ScreenHeader,
} from "@/components/layout";
import { Button } from "@/components/orkestr/Button";
import { Card } from "@/components/orkestr/Card";
import { Badge, AvatarGroup } from "@/components/orkestr/Badge";
import { FRIENDS } from "@/lib/mock-data";

export default function SettledPage() {
  return (
    <MobileFrame>
      <Screen soft>
        <ScreenHeader
          title="Settled"
          subtitle="Dark passport card — final state"
          backHref="/"
        />
        <ScreenContent soft>
          <Card variant="dark">
            <div className="row-between">
              <span className="badge-ref" style={{ background: "var(--color-positive-light)", color: "var(--color-settled-seal)" }}>
                FULLY SETTLED
              </span>
              <div className="settled-seal">✓</div>
            </div>

            <p
              className="text-eyebrow"
              style={{ color: "var(--color-mute)", marginTop: "var(--space-2xl)" }}
            >
              SPL-2799
            </p>
            <h2
              className="text-display-md"
              style={{ color: "var(--color-settled-text)", marginTop: "var(--space-sm)" }}
            >
              Seoul Garden
            </h2>
            <p className="text-body-sm" style={{ color: "var(--color-mute)", marginTop: "var(--space-sm)" }}>
              Mon 3 Jun · All 5 friends paid
            </p>

            <p
              className="text-amount-lg"
              style={{ color: "var(--color-text-primary)", marginTop: "var(--space-3xl)" }}
            >
              $68.50
            </p>
            <p className="text-caption" style={{ color: "var(--color-mute)", marginTop: "var(--space-sm)" }}>
              Total split amount
            </p>

            <div style={{ marginTop: "var(--space-2xl)" }}>
              <AvatarGroup
                personas={FRIENDS.map((f) => ({ persona: f.id, initials: f.initials }))}
              />
            </div>
          </Card>

          <div style={{ marginTop: "var(--space-3xl)" }}>
            <Card>
              <p className="text-body-md-strong">Settlement summary</p>
              <p className="text-body-sm" style={{ marginTop: "var(--space-sm)" }}>
                Carol fronted the grocery bill. Everyone paid their $13.70 share within 48 hours.
              </p>
              <div style={{ marginTop: "var(--space-lg)" }}>
                <Badge variant="status" statusDot="complete">
                  Closed · no outstanding balance
                </Badge>
              </div>
            </Card>
          </div>
        </ScreenContent>
        <BottomBar>
          <Link href="/" style={{ display: "block" }}>
            <Button variant="secondary">Back to all splits</Button>
          </Link>
        </BottomBar>
      </Screen>
    </MobileFrame>
  );
}
