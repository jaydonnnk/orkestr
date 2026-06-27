import {
  BottomBar,
  MobileFrame,
  Screen,
  ScreenContent,
  ScreenHeader,
} from "@/components/layout";
import { Button, IconButton } from "@/components/orkestr/Button";
import { Card } from "@/components/orkestr/Card";
import { Amount } from "@/components/orkestr/Amount";
import { Badge, Avatar, AvatarGroup } from "@/components/orkestr/Badge";
import { FRIENDS } from "@/lib/mock-data";

const SHARES = [
  { friend: FRIENDS[0], paid: true, amount: 31.2 },
  { friend: FRIENDS[1], paid: false, amount: 31.2 },
  { friend: FRIENDS[2], paid: true, amount: 31.2 },
  { friend: FRIENDS[3], paid: false, amount: 31.2 },
  { friend: FRIENDS[4], paid: true, amount: 31.2 },
];

export default function SplitDetailPage() {
  return (
    <MobileFrame>
      <Screen soft>
        <ScreenHeader
          title="Dinner at Trattoria"
          subtitle="Composite screen — all components together"
          backHref="/"
          action={<IconButton aria-label="Share">↗</IconButton>}
        />
        <ScreenContent soft>
          <section className="section">
            <div className="card card-featured">
              <div className="row-between">
                <div>
                  <Badge variant="amber">Split confirmed</Badge>
                  <p className="text-display-sm" style={{ marginTop: "var(--space-md)" }}>
                    Group total
                  </p>
                </div>
                <Badge variant="ref">SPL-2847</Badge>
              </div>
              <div style={{ marginTop: "var(--space-md)" }}>
                <Amount value={156.0} size="lg" />
              </div>
              <p className="text-caption" style={{ marginTop: "var(--space-md)" }}>
                Sat 14 Jun · Paid by Alice
              </p>
            </div>
          </section>

          <section className="section">
            <p className="text-eyebrow section-title">Participants</p>
            <AvatarGroup
              personas={FRIENDS.map((f) => ({ persona: f.id, initials: f.initials }))}
            />
          </section>

          <section className="section">
            <p className="text-eyebrow section-title">Who owes what</p>
            <Card>
              {SHARES.map(({ friend, paid, amount }) => (
                <div key={friend.id} className="split-row">
                  <div className="row">
                    <Avatar persona={friend.id} initials={friend.initials} />
                    <div>
                      <p className="text-body-md-strong">{friend.name}</p>
                      <Badge
                        variant="status"
                        statusDot={paid ? "complete" : "pending"}
                      >
                        {paid ? "Paid" : "Pending"}
                      </Badge>
                    </div>
                  </div>
                  <Amount value={amount} size="sm" negative={!paid && friend.id === "bob"} />
                </div>
              ))}
            </Card>
          </section>

          <section className="section">
            <p className="text-eyebrow section-title">Your share</p>
            <Card variant="surface">
              <div className="row-between">
                <p className="text-body-md">You (Carol)</p>
                <Amount value={31.2} size="md" />
              </div>
              <p className="text-body-sm" style={{ marginTop: "var(--space-sm)" }}>
                You&apos;ve already paid your share.
              </p>
            </Card>
          </section>
        </ScreenContent>
        <BottomBar>
          <Button variant="secondary">Remind unpaid friends</Button>
        </BottomBar>
      </Screen>
    </MobileFrame>
  );
}
