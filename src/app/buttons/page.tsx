import {
  BottomBar,
  ComponentLabel,
  MobileFrame,
  Screen,
  ScreenContent,
  ScreenHeader,
} from "@/components/layout";
import { Button, IconButton } from "@/components/orkestr/Button";

export default function ButtonsPage() {
  return (
    <MobileFrame>
      <Screen>
        <ScreenHeader
          title="Buttons"
          subtitle="Split actions — request payment, remind, cancel"
          backHref="/"
        />
        <ScreenContent>
          <div className="variant-block">
            <ComponentLabel>Primary — one per screen</ComponentLabel>
            <p className="text-body-sm text-muted" style={{ marginBottom: "var(--space-md)" }}>
              Used for the main action: send a payment request to friends.
            </p>
            <Button>Request $31.20 from Bob</Button>
          </div>

          <div className="variant-block">
            <ComponentLabel>Secondary</ComponentLabel>
            <p className="text-body-sm text-muted" style={{ marginBottom: "var(--space-md)" }}>
              Secondary actions like adding another expense.
            </p>
            <Button variant="secondary">Add another expense</Button>
          </div>

          <div className="variant-block">
            <ComponentLabel>Tertiary</ComponentLabel>
            <p className="text-body-sm text-muted" style={{ marginBottom: "var(--space-md)" }}>
              Outline style for optional actions.
            </p>
            <Button variant="tertiary">Share split link</Button>
          </div>

          <div className="variant-block">
            <ComponentLabel>Destructive</ComponentLabel>
            <p className="text-body-sm text-muted" style={{ marginBottom: "var(--space-md)" }}>
              Remove a friend from the split or delete the group.
            </p>
            <Button variant="destructive">Remove from split</Button>
          </div>

          <div className="variant-block">
            <ComponentLabel>Disabled states</ComponentLabel>
            <div className="stack-sm">
              <Button disabled>Waiting for everyone</Button>
              <Button variant="secondary" disabled>
                No pending invites
              </Button>
            </div>
          </div>

          <div className="variant-block">
            <ComponentLabel>Icon button</ComponentLabel>
            <p className="text-body-sm text-muted" style={{ marginBottom: "var(--space-md)" }}>
              Quick actions on a split row.
            </p>
            <div className="row">
              <IconButton aria-label="Edit split">✎</IconButton>
              <IconButton aria-label="More options">⋯</IconButton>
              <IconButton aria-label="Send reminder">↗</IconButton>
            </div>
          </div>
        </ScreenContent>
        <BottomBar>
          <Button>Send reminders</Button>
        </BottomBar>
      </Screen>
    </MobileFrame>
  );
}
