import Link from "next/link";
import {
  BottomBar,
  MobileFrame,
  Screen,
  ScreenContent,
  ScreenHeader,
} from "@/components/layout";
import { Button } from "@/components/orkestr/Button";
import { Amount } from "@/components/orkestr/Amount";
import { Badge } from "@/components/orkestr/Badge";
import { AvatarGroup } from "@/components/orkestr/Badge";
import { SHOWCASE_SCREENS, SPLITS, FRIENDS } from "@/lib/mock-data";

export default function HomePage() {
  const activeSplit = SPLITS[0];

  return (
    <MobileFrame>
      <Screen>
        <ScreenHeader
          title="Split"
          subtitle="Orkestr design system — payment splitting mock"
        />
        <ScreenContent soft>
          <section className="section">
            <p className="text-eyebrow section-title">Your balance</p>
            <div className="card">
              <p className="text-body-sm">You owe the group</p>
              <div style={{ marginTop: "var(--space-sm)" }}>
                <Amount value={activeSplit.yourShare} size="lg" />
              </div>
              <div style={{ marginTop: "var(--space-md)" }}>
                <Badge variant="status" statusDot="active">
                  {activeSplit.title}
                </Badge>
              </div>
            </div>
          </section>

          <section className="section">
            <p className="text-eyebrow section-title">Recent split</p>
            <div className="card">
              <div className="row-between">
                <div>
                  <p className="text-display-sm">{activeSplit.title}</p>
                  <p className="text-body-sm">{activeSplit.date}</p>
                </div>
                <Amount value={activeSplit.total} size="md" />
              </div>
              <div style={{ marginTop: "var(--space-lg)" }}>
                <AvatarGroup
                  personas={FRIENDS.slice(0, 4).map((f) => ({
                    persona: f.id,
                    initials: f.initials,
                  }))}
                />
              </div>
            </div>
          </section>

          <section className="section">
            <p className="text-eyebrow section-title">Component screens</p>
            <div className="hub-grid">
              {SHOWCASE_SCREENS.map((screen) => (
                <Link key={screen.href} href={screen.href} className="hub-link">
                  <div>
                    <p className="text-body-md-strong">{screen.title}</p>
                    <p className="text-caption">{screen.description}</p>
                  </div>
                  <span className="hub-link-arrow" aria-hidden="true">
                    →
                  </span>
                </Link>
              ))}
            </div>
          </section>
        </ScreenContent>
        <BottomBar>
          <Button>Start new split</Button>
        </BottomBar>
      </Screen>
    </MobileFrame>
  );
}
