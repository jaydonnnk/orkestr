import Link from "next/link";
import { MobileFrame, Screen, ScreenContent } from "@/components/layout";
import { FRIENDS, SPLITS } from "@/lib/mock-data";

const SUBMITTED_IDS = new Set(["alice", "carol"]);

const event = SPLITS[0];

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function EventPage({ params }: PageProps) {
  const { id } = await params;

  const members = FRIENDS.map((f) => ({
    ...f,
    submitted: SUBMITTED_IDS.has(f.id),
  }));

  return (
    <MobileFrame>
      <Screen>
        <ScreenContent>
          {/* Event details */}
          <div style={{ paddingTop: "var(--space-lg)", marginBottom: "var(--space-3xl)" }}>
            <h1 className="text-display-lg">{event.title}</h1>
            <p
              className="text-body-md"
              style={{ marginTop: "var(--space-sm)", color: "var(--color-body)" }}
            >
              {event.date}
            </p>
          </div>

          {/* Members */}
          <div>
            <p className="text-eyebrow" style={{ marginBottom: "var(--space-md)" }}>
              Members
            </p>
            <div className="stack-md">
              {members.map((member) => (
                <div key={member.id} className="row-between">
                  {/* Left: avatar + name */}
                  <div className="row">
                    <span
                      style={{
                        width: 32,
                        height: 32,
                        borderRadius: "var(--radius-full)",
                        background: "#FAECE7",
                        color: "#993C1D",
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontFamily: "var(--font-display)",
                        fontSize: 12,
                        fontWeight: 700,
                        flexShrink: 0,
                      }}
                      aria-hidden="true"
                    >
                      {member.initials}
                    </span>
                    <span className="text-body-md-strong">{member.name}</span>
                  </div>

                  {/* Right: status */}
                  {member.submitted ? (
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        background: "var(--color-accent)",
                        color: "#fff",
                        fontFamily: "var(--font-body)",
                        fontSize: 12,
                        fontWeight: 500,
                        borderRadius: "var(--radius-pill)",
                        padding: "var(--space-xs) var(--space-md)",
                        whiteSpace: "nowrap",
                      }}
                    >
                      Done
                    </span>
                  ) : (
                    <Link
                      href={`/preferences/${id}`}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        minHeight: 36,
                        padding: "0 var(--space-md)",
                        border: "1px solid #D85A30",
                        borderRadius: "var(--radius-pill)",
                        color: "#D85A30",
                        background: "transparent",
                        fontFamily: "var(--font-body)",
                        fontSize: 12,
                        fontWeight: 500,
                        whiteSpace: "nowrap",
                        textDecoration: "none",
                      }}
                    >
                      Submit
                    </Link>
                  )}
                </div>
              ))}
            </div>
          </div>
        </ScreenContent>
      </Screen>
    </MobileFrame>
  );
}
