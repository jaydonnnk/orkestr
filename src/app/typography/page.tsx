import {
  ComponentLabel,
  MobileFrame,
  Screen,
  ScreenContent,
  ScreenHeader,
} from "@/components/layout";
import { Amount } from "@/components/orkestr/Amount";
import { Card } from "@/components/orkestr/Card";

export default function TypographyPage() {
  return (
    <MobileFrame>
      <Screen>
        <ScreenHeader
          title="Typography"
          subtitle="Display, body & amount scales"
          backHref="/"
        />
        <ScreenContent>
          <div className="variant-block">
            <ComponentLabel>Display — Plus Jakarta Sans</ComponentLabel>
            <Card>
              <div className="stack-md">
                <p className="text-display-lg">$156.00 split</p>
                <p className="text-display-md">Dinner at Trattoria</p>
                <p className="text-display-sm">Your share this week</p>
              </div>
            </Card>
          </div>

          <div className="variant-block">
            <ComponentLabel>Body — Inter</ComponentLabel>
            <Card variant="surface">
              <div className="stack-sm">
                <p className="text-body-lg">Alice paid the full bill upfront.</p>
                <p className="text-body-md">Everyone owes an equal share of the total.</p>
                <p className="text-body-md-strong">Bob still needs to pay</p>
                <p className="text-body-sm">Last reminder sent 2 days ago</p>
                <p className="text-body-sm-strong">Status: collecting</p>
                <p className="text-caption">Refunds processed within 3–5 business days</p>
                <p className="text-eyebrow">Payment breakdown</p>
              </div>
            </Card>
          </div>

          <div className="variant-block">
            <ComponentLabel>Amounts — tabular nums, amber for financial</ComponentLabel>
            <Card>
              <div className="stack-lg">
                <div>
                  <p className="text-body-sm">Hero amount</p>
                  <Amount value={156.0} size="lg" />
                </div>
                <div>
                  <p className="text-body-sm">Card amount</p>
                  <Amount value={31.2} size="md" />
                </div>
                <div>
                  <p className="text-body-sm">Inline / row amount</p>
                  <Amount value={13.7} size="sm" />
                </div>
                <div>
                  <p className="text-body-sm">Negative (you owe)</p>
                  <Amount value={-24.5} size="sm" negative />
                </div>
              </div>
            </Card>
          </div>

          <div className="variant-block">
            <ComponentLabel>Alignment demo — columns stay fixed</ComponentLabel>
            <Card variant="surface">
              <div className="split-row">
                <span className="text-body-md">Alice</span>
                <Amount value={31.2} size="sm" />
              </div>
              <div className="split-row">
                <span className="text-body-md">Bob</span>
                <Amount value={999.99} size="sm" />
              </div>
              <div className="split-row">
                <span className="text-body-md">Carol</span>
                <Amount value={8.0} size="sm" />
              </div>
            </Card>
          </div>
        </ScreenContent>
      </Screen>
    </MobileFrame>
  );
}
