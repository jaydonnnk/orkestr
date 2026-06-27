import {
  ComponentLabel,
  MobileFrame,
  Screen,
  ScreenContent,
  ScreenHeader,
} from "@/components/layout";
import { Avatar, AvatarGroup } from "@/components/orkestr/Badge";
import { Card } from "@/components/orkestr/Card";
import { FRIENDS } from "@/lib/mock-data";

export default function AvatarsPage() {
  return (
    <MobileFrame>
      <Screen>
        <ScreenHeader
          title="Avatars"
          subtitle="Friend personas — consistent colours"
          backHref="/"
        />
        <ScreenContent>
          <div className="variant-block">
            <ComponentLabel>Medium — 32px</ComponentLabel>
            <div className="row" style={{ flexWrap: "wrap", gap: "var(--space-lg)" }}>
              {FRIENDS.map((friend) => (
                <div key={friend.id} className="row" style={{ gap: "var(--space-sm)" }}>
                  <Avatar persona={friend.id} size="md" initials={friend.initials} />
                  <span className="text-body-sm">{friend.name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="variant-block">
            <ComponentLabel>Large — 40px</ComponentLabel>
            <div className="row" style={{ flexWrap: "wrap", gap: "var(--space-lg)" }}>
              {FRIENDS.map((friend) => (
                <Avatar key={friend.id} persona={friend.id} size="lg" initials={friend.initials} />
              ))}
            </div>
          </div>

          <div className="variant-block">
            <ComponentLabel>Avatar group — split participants</ComponentLabel>
            <Card>
              <p className="text-body-md-strong">Dinner at Trattoria</p>
              <p className="text-body-sm" style={{ marginTop: "var(--space-xs)" }}>
                5 friends on this split
              </p>
              <div style={{ marginTop: "var(--space-lg)" }}>
                <AvatarGroup
                  personas={FRIENDS.map((f) => ({
                    persona: f.id,
                    initials: f.initials,
                  }))}
                />
              </div>
            </Card>
          </div>

          <div className="variant-block">
            <ComponentLabel>Persona colour key</ComponentLabel>
            <Card variant="surface">
              <div className="stack-md">
                {FRIENDS.map((friend) => (
                  <div key={friend.id} className="row-between">
                    <div className="row">
                      <Avatar persona={friend.id} initials={friend.initials} />
                      <span className="text-body-md-strong">{friend.name}</span>
                    </div>
                    <span className="text-caption">avatar--{friend.id}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </ScreenContent>
      </Screen>
    </MobileFrame>
  );
}
