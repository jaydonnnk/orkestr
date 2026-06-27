import {
  ComponentLabel,
  MobileFrame,
  Screen,
  ScreenContent,
  ScreenHeader,
} from "@/components/layout";
import { Badge, TagChip } from "@/components/orkestr/Badge";
import { Card } from "@/components/orkestr/Card";

export default function BadgesPage() {
  return (
    <MobileFrame>
      <Screen>
        <ScreenHeader
          title="Badges & pills"
          subtitle="Split status, refs & labels"
          backHref="/"
        />
        <ScreenContent>
          <div className="variant-block">
            <ComponentLabel>Amber — confirmed / financial positive</ComponentLabel>
            <div className="row" style={{ flexWrap: "wrap", gap: "var(--space-sm)" }}>
              <Badge variant="amber">Payment received</Badge>
              <Badge variant="amber">Split confirmed</Badge>
            </div>
          </div>

          <div className="variant-block">
            <ComponentLabel>Negative — overdue or declined</ComponentLabel>
            <div className="row" style={{ flexWrap: "wrap", gap: "var(--space-sm)" }}>
              <Badge variant="negative">Overdue 3 days</Badge>
              <Badge variant="negative">Payment declined</Badge>
            </div>
          </div>

          <div className="variant-block">
            <ComponentLabel>Reference pill — tabular nums</ComponentLabel>
            <div className="row" style={{ flexWrap: "wrap", gap: "var(--space-sm)" }}>
              <Badge variant="ref">SPL-2847</Badge>
              <Badge variant="ref">SPL-2812</Badge>
              <Badge variant="ref">SPL-2799</Badge>
            </div>
          </div>

          <div className="variant-block">
            <ComponentLabel>Status dots</ComponentLabel>
            <Card>
              <div className="stack-md">
                <Badge variant="status" statusDot="active">
                  Collecting payments
                </Badge>
                <Badge variant="status" statusDot="complete">
                  Fully settled
                </Badge>
                <Badge variant="status" statusDot="pending">
                  Waiting on Dave
                </Badge>
              </div>
            </Card>
          </div>

          <div className="variant-block">
            <ComponentLabel>Tag chips — dietary / metadata</ComponentLabel>
            <div className="row" style={{ flexWrap: "wrap", gap: "var(--space-sm)" }}>
              <TagChip positive>Vegetarian</TagChip>
              <TagChip>Split equally</TagChip>
              <TagChip>Tip included</TagChip>
            </div>
          </div>
        </ScreenContent>
      </Screen>
    </MobileFrame>
  );
}
