import {
  ComponentLabel,
  MobileFrame,
  Screen,
  ScreenContent,
  ScreenHeader,
} from "@/components/layout";
import { Card } from "@/components/orkestr/Card";
import { Amount } from "@/components/orkestr/Amount";
import { Badge, Avatar } from "@/components/orkestr/Badge";
import { FRIENDS } from "@/lib/mock-data";

export default function CardsPage() {
  return (
    <MobileFrame>
      <Screen soft>
        <ScreenHeader
          title="Cards"
          subtitle="Split summaries on elevated surfaces"
          backHref="/"
        />
        <ScreenContent soft>
          <div className="variant-block">
            <ComponentLabel>Default card — level 1</ComponentLabel>
            <Card>
              <div className="row-between">
                <div>
                  <p className="text-display-sm">Dinner at Seoul Garden</p>
                  <p className="text-body-sm">Paid by Alice · 5 people</p>
                </div>
                <Amount value={156.0} size="md" />
              </div>
              <div style={{ marginTop: "var(--space-lg)" }}>
                <Badge variant="ref">SPL-2847</Badge>
              </div>
            </Card>
          </div>

          <div className="variant-block">
            <ComponentLabel>Surface card — soft background</ComponentLabel>
            <Card variant="surface">
              <p className="text-eyebrow" style={{ marginBottom: "var(--space-sm)" }}>
                Your share breakdown
              </p>
              {FRIENDS.slice(0, 3).map((friend) => (
                <div key={friend.id} className="split-row">
                  <div className="row">
                    <Avatar persona={friend.id} initials={friend.initials} />
                    <span className="text-body-md-strong">{friend.name}</span>
                  </div>
                  <Amount value={31.2} size="sm" />
                </div>
              ))}
            </Card>
          </div>

          <div className="variant-block">
            <ComponentLabel>Featured card — strong border</ComponentLabel>
            <Card variant="featured">
              <p className="text-body-sm">Group total outstanding</p>
              <div style={{ marginTop: "var(--space-sm)" }}>
                <Amount value={124.8} size="lg" />
              </div>
              <p className="text-caption" style={{ marginTop: "var(--space-md)" }}>
                4 friends still need to pay their share
              </p>
            </Card>
          </div>

          <div className="variant-block">
            <ComponentLabel>Dark card — settled passport preview</ComponentLabel>
            <Card variant="dark">
              <div className="row-between">
                <div>
                  <p className="text-eyebrow" style={{ color: "var(--color-mute)" }}>
                    Settled
                  </p>
                  <p
                    className="text-display-sm"
                    style={{ color: "var(--color-settled-text)", marginTop: "var(--space-sm)" }}
                  >
                    Groceries run
                  </p>
                </div>
                <div className="settled-seal">✓</div>
              </div>
              <p
                className="text-amount-lg"
                style={{ color: "var(--color-settled-seal)", marginTop: "var(--space-sm)" }}
              >
                $68.50
              </p>
            </Card>
          </div>
        </ScreenContent>
      </Screen>
    </MobileFrame>
  );
}
