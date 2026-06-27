"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MobileFrame, Screen, ScreenContent } from "@/components/layout";
import { Input } from "@/components/orkestr/Input";
import { Button } from "@/components/orkestr/Button";

interface CreateEventForm {
  eventName: string;
  date: string;
}

function generateInviteCode() {
  return Math.random().toString(36).slice(2, 7);
}

const INVITE_CODE = generateInviteCode();
const INVITE_URL = `orkestr.app/e/${INVITE_CODE}`;

export default function CreateEventPage() {
  const [form, setForm] = useState<CreateEventForm>({
    eventName: "",
    date: "",
  });
  const [copied, setCopied] = useState(false);
  const router = useRouter();

  function handleChange(field: keyof CreateEventForm) {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
    };
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    console.log("Create Event submitted:", { ...form, inviteUrl: INVITE_URL });
    router.push(`/event/${INVITE_CODE}`);
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(`https://${INVITE_URL}`);
    } catch {
      // fallback: silent
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <MobileFrame>
      <Screen>
        {/* App bar */}
        <div
          style={{
            background: "var(--color-accent)",
            padding: "var(--space-sm) var(--space-xl) var(--space-xl)",
          }}
        >
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: 11,
              color: "rgba(255,255,255,0.7)",
              marginBottom: "var(--space-sm)",
            }}
          >
            9:41
          </p>
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 24,
              fontWeight: 700,
              color: "#fff",
              letterSpacing: "-0.02em",
            }}
          >
            Orkestr
          </h1>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "contents" }}>
          <ScreenContent>
            {/* Page heading */}
            <div style={{ marginBottom: "var(--space-3xl)", paddingTop: "var(--space-lg)" }}>
              <h2 className="text-display-lg">New event</h2>
              <p className="text-body-md" style={{ marginTop: "var(--space-sm)", color: "var(--color-body)" }}>
                Fill in the details and we&apos;ll coordinate the rest.
              </p>
            </div>

            {/* Form fields */}
            <div className="stack-lg" style={{ marginBottom: "var(--space-2xl)" }}>
              <Input
                label="Event name"
                id="event-name"
                type="text"
                placeholder="What are we doing?"
                value={form.eventName}
                onChange={handleChange("eventName")}
                autoComplete="off"
              />
              <Input
                label="Date"
                id="event-date"
                type="date"
                value={form.date}
                onChange={handleChange("date")}
              />
            </div>

            {/* CTA */}
            <Button type="submit" variant="primary">
              Create event
            </Button>

            {/* Divider */}
            <div
              style={{
                borderTop: "0.5px solid var(--color-border)",
                margin: "var(--space-3xl) 0 var(--space-2xl)",
              }}
            />

            {/* Invite link section */}
            <div>
              <p
                className="text-body-md-strong"
                style={{ marginBottom: "var(--space-md)" }}
              >
                Your invite link
              </p>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-sm)",
                  background: "var(--color-accent-light)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-md) var(--space-lg)",
                  minHeight: 48,
                }}
              >
                <span
                  style={{
                    flex: 1,
                    fontFamily: "monospace",
                    fontSize: 14,
                    color: "var(--color-ink)",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {INVITE_URL}
                </span>
                <button
                  type="button"
                  onClick={handleCopy}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "var(--space-xs)",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    fontFamily: "var(--font-body)",
                    fontSize: 13,
                    fontWeight: 500,
                    color: "var(--color-accent)",
                    flexShrink: 0,
                    padding: "var(--space-xs) 0",
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
                    <rect x="4" y="4" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
                    <path d="M2 10V2h8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
              <p className="text-body-sm" style={{ marginTop: "var(--space-sm)" }}>
                Share this link with your group to join the event.
              </p>
            </div>
          </ScreenContent>
        </form>
      </Screen>
    </MobileFrame>
  );
}
