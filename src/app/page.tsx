"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import styles from "./page.module.css";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Dict = Record<string, unknown>;

type Conflict = {
  agent?: string;
  constraint_ref?: string | null;
  claim?: string;
};

type Venue = {
  id?: string;
  name?: string;
  address?: string;
  tags?: string[];
};

type Plan = {
  title?: string;
  day?: string;
  time?: string;
  venue?: Venue;
  total_cost?: number;
  per_person?: number;
  booking_ref?: string | null;
  satisfies?: string[];
  conflicts?: Conflict[];
};

type Message = {
  round?: number;
  agent?: string;
  stance?: string;
  claim?: string;
  constraint_ref?: string | null;
};

type Mandate = {
  status?: string;
  booking_ref?: string;
  merchant?: string;
  payment_mode?: string;
  vault_token?: string | Dict;
  order?: Dict;
};

type Handshake = {
  request?: Dict;
  response?: Dict;
  mandate?: Mandate;
  booking_ref?: string;
  status?: string;
  merchant?: string;
};

type Transfer = {
  from?: string;
  to?: string;
  amount?: number;
  rail?: string;
  status?: string;
  tx_hash?: string | null;
  latency_ms?: number;
};

type Settlement = {
  transfers?: Transfer[];
  net_after?: Record<string, number>;
};

type DemoState = {
  phase: string;
  plan: Plan;
  negotiation: Message[];
  handshake: Handshake;
  settlement: Settlement;
  checkedAt: string;
};

type Member = { id: string; name: string; avatar?: string | null };

type Constraints = {
  days: string[];
  budget: string;
  dietary: string[];
  freeform: string;
};

const DAY_OPTIONS = ["FRI", "SAT", "SUN"];
const DIET_OPTIONS: { id: string; label: string }[] = [
  { id: "halal", label: "halal" },
  { id: "vegetarian", label: "vegetarian" },
  { id: "no_raw_fish", label: "no raw fish" },
  { id: "vegan", label: "vegan" },
];

const PERSON_NAMES: Record<string, string> = {
  "P-001": "Alice",
  "P-002": "Bob",
  "P-003": "Carol",
  "P-004": "Dave",
  "P-005": "Eve",
};

const PERSON_INITIALS: Record<string, string> = {
  "P-001": "A",
  "P-002": "B",
  "P-003": "C",
  "P-004": "D",
  "P-005": "E",
};

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    cache: "no-store",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }

  return (await response.json()) as T;
}

async function readLiveState(sessionId: string): Promise<DemoState> {
  const [status, negotiation, plan, handshake, settlement] = await Promise.all([
    fetchJson<{ phase?: string }>(`/api/status/${sessionId}`),
    fetchJson<Message[]>(`/api/negotiation/${sessionId}`),
    fetchJson<Plan>(`/api/plan/${sessionId}`),
    fetchJson<Handshake>(`/api/handshake/${sessionId}`),
    fetchJson<Settlement>(`/api/settlement/${sessionId}`),
  ]);

  return {
    phase: status.phase ?? "unknown",
    plan,
    negotiation: Array.isArray(negotiation) ? negotiation : [],
    handshake,
    settlement,
    checkedAt: new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }),
  };
}

function isRecord(value: unknown): value is Dict {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

function dollars(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value)
    ? `$${value}`
    : "$--";
}

function personName(id?: string): string {
  return id ? PERSON_NAMES[id] ?? id : "Agent";
}

function personInitial(id?: string): string {
  return id ? PERSON_INITIALS[id] ?? id.slice(0, 1) : "?";
}

function paymentMode(mandate?: Mandate): string {
  const direct = asString(mandate?.payment_mode);
  if (direct) {
    return direct;
  }

  const token = mandate?.vault_token;
  if (isRecord(token)) {
    return asString(token.mode, "unknown");
  }

  return "unknown";
}

function shortHash(hash?: string | null): string {
  if (!hash) {
    return "pending";
  }

  return hash.length > 10 ? `${hash.slice(0, 6)}...${hash.slice(-4)}` : hash;
}

function emptyConstraints(): Constraints {
  return { days: [], budget: "", dietary: [], freeform: "" };
}

function toggle(list: string[], value: string): string[] {
  return list.includes(value)
    ? list.filter((item) => item !== value)
    : [...list, value];
}

function isReadyToSubmit(c: Constraints): boolean {
  return c.days.length > 0 && Number(c.budget) > 0;
}

function ConstraintCard({
  member,
  value,
  onChange,
  onSubmit,
  submitted,
  submitting,
}: {
  member: Member;
  value: Constraints;
  onChange: (next: Constraints) => void;
  onSubmit: () => void;
  submitted: boolean;
  submitting: boolean;
}) {
  const canSubmit = isReadyToSubmit(value) && !submitted && !submitting;

  return (
    <div className={styles.phoneBlock}>
      <div className={styles.stepLabel}>
        <span>{personInitial(member.id)} — {member.name}</span>
        {submitted ? <em>ready</em> : null}
      </div>
      <div className={styles.phone}>
        <div className={styles.statusBar}>
          <span>9:41</span>
          <span>5G</span>
        </div>
        <h2>Your constraints</h2>
        <p className={styles.subtitle}>What works for you?</p>

        <div className={styles.field}>
          <span className={styles.fieldLabel}>Available days</span>
          <div className={styles.chipRow}>
            {DAY_OPTIONS.map((day) => (
              <button
                key={day}
                type="button"
                disabled={submitted}
                className={`${styles.chip} ${value.days.includes(day) ? styles.chipOn : ""}`}
                onClick={() => onChange({ ...value, days: toggle(value.days, day) })}
              >
                {day}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.field}>
          <span className={styles.fieldLabel}>Budget / head (SGD)</span>
          <input
            className={styles.numInput}
            type="number"
            min={0}
            inputMode="numeric"
            placeholder="e.g. 60"
            disabled={submitted}
            value={value.budget}
            onChange={(event) => onChange({ ...value, budget: event.target.value })}
          />
        </div>

        <div className={styles.field}>
          <span className={styles.fieldLabel}>Dietary</span>
          <div className={styles.chipRow}>
            {DIET_OPTIONS.map((diet) => (
              <button
                key={diet.id}
                type="button"
                disabled={submitted}
                className={`${styles.chip} ${value.dietary.includes(diet.id) ? styles.chipOn : ""}`}
                onClick={() => onChange({ ...value, dietary: toggle(value.dietary, diet.id) })}
              >
                {diet.label}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.field}>
          <span className={styles.fieldLabel}>Anything else</span>
          <input
            className={styles.textInput}
            type="text"
            placeholder="e.g. somewhere walkable"
            disabled={submitted}
            value={value.freeform}
            onChange={(event) => onChange({ ...value, freeform: event.target.value })}
          />
        </div>

        <button
          className={styles.primaryButton}
          style={{ marginTop: "auto", width: "100%" }}
          type="button"
          onClick={onSubmit}
          disabled={!canSubmit}
        >
          {submitted ? "Ready ✓" : submitting ? "Sending..." : "Find our plan"}
        </button>
      </div>
    </div>
  );
}

function CheckPill({
  label,
  ok,
  detail,
}: {
  label: string;
  ok: boolean;
  detail: string;
}) {
  return (
    <div className={`${styles.checkPill} ${ok ? styles.checkOk : styles.checkWait}`}>
      <span>{ok ? "OK" : "WAIT"}</span>
      <strong>{label}</strong>
      <small>{detail}</small>
    </div>
  );
}

function Phone({
  eyebrow,
  title,
  children,
  moneyShot = false,
}: {
  eyebrow: string;
  title: string;
  children: React.ReactNode;
  moneyShot?: boolean;
}) {
  return (
    <section className={styles.phoneBlock}>
      <div className={styles.stepLabel}>
        <span>{eyebrow}</span>
        {moneyShot ? <em>money shot</em> : null}
      </div>
      <div className={styles.phone}>
        <div className={styles.statusBar}>
          <span>9:41</span>
          <span>5G</span>
        </div>
        <h2>{title}</h2>
        {children}
      </div>
    </section>
  );
}

function PlanPhone({ plan }: { plan: Plan }) {
  const tags = Array.isArray(plan.venue?.tags) ? plan.venue.tags : [];
  const conflicts = Array.isArray(plan.conflicts) ? plan.conflicts : [];

  return (
    <Phone eyebrow="3 - Review the plan" title={plan.title ?? "Dinner plan"}>
      <p className={styles.subtitle}>
        {plan.day ?? "FRI"} - {plan.time ?? "19:30"}
      </p>
      <div className={styles.mapGrid} aria-hidden="true" />
      <div className={styles.venuePanel}>
        <div>
          <strong>{plan.venue?.name ?? "Venue"}</strong>
          <span>{plan.venue?.address ?? "Address pending"}</span>
        </div>
        <div className={styles.tags}>
          {tags.slice(0, 4).map((tag) => (
            <span key={tag}>{tag.replace("_", " ")}</span>
          ))}
        </div>
      </div>
      <div className={styles.priceRow}>
        <span>Total {dollars(plan.total_cost)}</span>
        <strong>{dollars(plan.per_person)} / person</strong>
      </div>
      <div className={styles.acceptance}>
        <span>{plan.satisfies?.length ?? 0} agents accept</span>
        <span>{conflicts.length} conflicts</span>
      </div>
    </Phone>
  );
}

function NegotiationPhone({ messages, plan }: { messages: Message[]; plan: Plan }) {
  const visibleMessages = messages.slice(-6);
  const conflicts = Array.isArray(plan.conflicts) ? plan.conflicts : [];

  return (
    <Phone eyebrow="2 - Agents converge" title="Finding your plan..." moneyShot>
      <p className={styles.subtitle}>Five agents, one Friday night</p>
      <div className={styles.ring} aria-label="Agent negotiation ring">
        {["P-001", "P-002", "P-003", "P-004", "P-005"].map((id) => (
          <span key={id} className={`${styles.agentDot} ${styles[`dot${personInitial(id)}`]}`}>
            {personInitial(id)}
          </span>
        ))}
        <strong>3 -&gt; 1</strong>
      </div>
      <ul className={styles.messageList}>
        {visibleMessages.map((message, index) => (
          <li key={`${message.round}-${message.agent}-${index}`}>
            <span data-stance={message.stance}>{message.stance ?? "note"}</span>
            <p>{message.claim ?? "No claim"}</p>
          </li>
        ))}
      </ul>
      {conflicts.length > 0 ? (
        <p className={styles.microcopy}>
          Fewest-objection fallback: {personName(conflicts[0].agent)} -
          {` ${conflicts[0].constraint_ref ?? "constraint"}`}
        </p>
      ) : (
        <p className={styles.microcopy}>Everyone accepts the selected plan.</p>
      )}
    </Phone>
  );
}

function AcpPhone({ handshake }: { handshake: Handshake }) {
  const requestTime =
    asString(handshake.request?.request_time) || asString(handshake.request?.time, "19:00");
  const counterTime =
    asString(handshake.response?.counter_time) ||
    asString(handshake.response?.time_offered, "19:30");
  const mandate = handshake.mandate;
  const mode = paymentMode(mandate);
  const status = mandate?.status ?? handshake.status ?? "unknown";
  const bookingRef = mandate?.booking_ref ?? handshake.booking_ref ?? "pending";

  return (
    <Phone eyebrow="4 - Agent to agent booking" title="Booking confirmed" moneyShot>
      <div className={styles.exchange}>
        <div className={styles.buyerBubble}>
          <strong>Your agent</strong>
          <span>
            Table for {String(handshake.request?.party_size ?? 5)},{" "}
            {asString(handshake.request?.day, "FRI")} {requestTime}
          </span>
        </div>
        <div className={styles.merchantBubble}>
          <strong>{handshake.merchant ?? mandate?.merchant ?? "Merchant agent"}</strong>
          <span>
            {requestTime} full -&gt; {counterTime},{" "}
            {dollars(handshake.response?.per_head)} / head
          </span>
        </div>
      </div>
      <div className={styles.mandatePanel}>
        <span className={styles.lockIcon}>LOCK</span>
        <div>
          <strong>Mandate {status}</strong>
          <span>payment mode: {mode}</span>
        </div>
      </div>
      <div className={styles.bookingRef}>
        <span>Booking ref</span>
        <strong>{bookingRef}</strong>
      </div>
    </Phone>
  );
}

function SettlementPhone({
  settlement,
  onSettle,
  settling,
}: {
  settlement: Settlement;
  onSettle: () => void;
  settling: boolean;
}) {
  const transfers = Array.isArray(settlement.transfers) ? settlement.transfers : [];
  const allSettled =
    transfers.length > 0 &&
    transfers.every((transfer) => transfer.status === "settled" && transfer.tx_hash);

  return (
    <Phone
      eyebrow={allSettled ? "6 - Done" : "5 - Settle up"}
      title={allSettled ? "Everyone's square" : "Who owes what"}
      moneyShot={allSettled}
    >
      <p className={styles.subtitle}>
        {transfers.length} transfers - {allSettled ? "settled on x402" : "ready on x402"}
      </p>
      <ul className={styles.transferList}>
        {transfers.map((transfer, index) => (
          <li key={`${transfer.from}-${transfer.to}-${index}`}>
            <span className={styles.avatar}>{personInitial(transfer.from)}</span>
            <strong>{personName(transfer.from)}</strong>
            <span>-&gt;</span>
            <span className={styles.avatar}>{personInitial(transfer.to)}</span>
            <strong>{personName(transfer.to)}</strong>
            <b>{dollars(transfer.amount)}</b>
            <code>{shortHash(transfer.tx_hash)}</code>
          </li>
        ))}
      </ul>
      <button
        className={styles.primaryButton}
        type="button"
        onClick={onSettle}
        disabled={settling || allSettled || transfers.length === 0}
      >
        {allSettled ? "x402 settled" : settling ? "Settling..." : "Approve x402 transfers"}
      </button>
    </Phone>
  );
}

export default function Home() {
  const [stage, setStage] = useState<"group" | "working">("group");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [forms, setForms] = useState<Record<string, Constraints>>({});
  const [submitted, setSubmitted] = useState<Record<string, boolean>>({});
  const [submitting, setSubmitting] = useState<Record<string, boolean>>({});

  const [state, setState] = useState<DemoState | null>(null);
  const [working, setWorking] = useState(false);
  const [settling, setSettling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Spin up a fresh, unseeded session with 5 member identities on first load.
  useEffect(() => {
    let active = true;

    async function startGroup() {
      try {
        const live = await fetchJson<{ session_id: string; members: Member[] }>(
          `/api/session/live`,
          { method: "POST", body: "{}" },
        );
        if (!active) {
          return;
        }
        setSessionId(live.session_id);
        setMembers(live.members);
        setForms(
          Object.fromEntries(
            live.members.map((m): [string, Constraints] => [m.id, emptyConstraints()]),
          ),
        );
        setError(null);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Unable to reach backend");
        }
      }
    }

    void startGroup();
    return () => {
      active = false;
    };
  }, []);

  const allReady =
    members.length > 0 && members.every((m) => submitted[m.id]);

  // Once everyone has pressed find-our-plan, run the live pipeline and load it.
  const runPipeline = useCallback(
    async (id: string) => {
      setWorking(true);
      setError(null);
      try {
        // First status call drives compute_plan server-side (Exa + negotiation
        // + ACP booking). It blocks until the plan is ready.
        await fetchJson<{ phase?: string }>(`/api/status/${id}`);
        setState(await readLiveState(id));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to build the plan");
      } finally {
        setWorking(false);
      }
    },
    [],
  );

  useEffect(() => {
    if (stage === "group" && allReady && sessionId) {
      setStage("working");
      void runPipeline(sessionId);
    }
  }, [stage, allReady, sessionId, runPipeline]);

  async function submitMember(member: Member) {
    if (!sessionId) {
      return;
    }
    const form = forms[member.id];
    if (!form || !isReadyToSubmit(form)) {
      return;
    }

    setSubmitting((prev) => ({ ...prev, [member.id]: true }));
    setError(null);
    try {
      await fetchJson<{ ok: boolean }>(`/api/constraints`, {
        method: "POST",
        body: JSON.stringify({
          session_id: sessionId,
          id: member.id,
          name: member.name,
          constraints: {
            available_days: form.days,
            budget_max: Number(form.budget),
            dietary: form.dietary,
          },
          freeform: form.freeform,
        }),
      });
      await fetchJson<{ all_ready: boolean }>(`/api/ready/${sessionId}`, {
        method: "POST",
        body: JSON.stringify({ person_id: member.id }),
      });
      setSubmitted((prev) => ({ ...prev, [member.id]: true }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to submit constraints");
    } finally {
      setSubmitting((prev) => ({ ...prev, [member.id]: false }));
    }
  }

  async function settleTransfers() {
    if (!sessionId || !state?.settlement.transfers?.length) {
      return;
    }

    setSettling(true);
    setError(null);
    try {
      const pendingSenders = Array.from(
        new Set(
          state.settlement.transfers
            .filter((transfer) => transfer.status !== "settled" && transfer.from)
            .map((transfer) => transfer.from as string),
        ),
      );

      await Promise.all(
        pendingSenders.map((person_id) =>
          fetchJson<{ ok: boolean }>(`/api/settle/${sessionId}`, {
            method: "POST",
            body: JSON.stringify({ person_id }),
          }),
        ),
      );

      setState(await readLiveState(sessionId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to settle transfers");
    } finally {
      setSettling(false);
    }
  }

  const checks = useMemo(() => {
    const mandate = state?.handshake.mandate;
    const requestTime =
      asString(state?.handshake.request?.request_time) ||
      asString(state?.handshake.request?.time);
    const counterTime =
      asString(state?.handshake.response?.counter_time) ||
      asString(state?.handshake.response?.time_offered);
    const transfers = state?.settlement.transfers ?? [];
    const allSettled =
      transfers.length > 0 &&
      transfers.every((transfer) => transfer.status === "settled" && transfer.tx_hash);

    return {
      plan: Boolean(state?.plan.title && state.plan.venue?.name),
      acp: mandate?.status === "co-signed" && Boolean(mandate.booking_ref),
      counter: Boolean(requestTime && counterTime && requestTime !== counterTime),
      payment: ["mock", "stripe_test"].includes(paymentMode(mandate)),
      x402: allSettled,
    };
  }, [state]);

  const readyCount = members.filter((m) => submitted[m.id]).length;

  return (
    <main className={styles.shell}>
      <section className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>Orkestr — live</p>
          <h1>{stage === "group" ? "The squad sets the rules" : "The plan makes itself"}</h1>
          <p>
            {stage === "group"
              ? `Session ${sessionId ?? "..."} - each member enters constraints, then taps Find our plan`
              : `Session ${sessionId ?? "..."} - Backend: `}
            {stage === "working" ? <code>{API_BASE}</code> : null}
          </p>
        </div>
        <div className={styles.actions}>
          {stage === "group" ? (
            <span className={styles.eyebrow}>{readyCount} / {members.length || 5} ready</span>
          ) : null}
        </div>
      </section>

      {error ? <p className={styles.error}>Backend check failed: {error}</p> : null}

      {stage === "group" ? (
        <section className={styles.groupGrid} aria-label="Group constraints">
          {members.length === 0 ? (
            <p className={styles.loading}>Assembling the group...</p>
          ) : (
            members.map((member) => (
              <ConstraintCard
                key={member.id}
                member={member}
                value={forms[member.id] ?? emptyConstraints()}
                onChange={(next) => setForms((prev) => ({ ...prev, [member.id]: next }))}
                onSubmit={() => void submitMember(member)}
                submitted={Boolean(submitted[member.id])}
                submitting={Boolean(submitting[member.id])}
              />
            ))
          )}
        </section>
      ) : null}

      {stage === "working" ? (
        <>
          <section className={styles.checks} aria-label="System checks">
            <CheckPill label="Plan" ok={checks.plan} detail={state?.phase ?? "loading"} />
            <CheckPill
              label="ACP"
              ok={checks.acp && checks.counter && checks.payment}
              detail={paymentMode(state?.handshake.mandate)}
            />
            <CheckPill label="x402" ok={checks.x402} detail={checks.x402 ? "settled" : "pending"} />
          </section>

          {working && !state ? (
            <p className={styles.loading}>
              Agents negotiating, discovering venues, and striking the booking...
            </p>
          ) : null}

          {state ? (
            <section className={styles.phoneGrid}>
              <NegotiationPhone messages={state.negotiation} plan={state.plan} />
              <PlanPhone plan={state.plan} />
              <AcpPhone handshake={state.handshake} />
              <SettlementPhone
                settlement={state.settlement}
                onSettle={() => void settleTransfers()}
                settling={settling}
              />
            </section>
          ) : null}

          <footer className={styles.footer}>
            Last checked {state?.checkedAt ?? "--"} - ACP and x402 are read from the live API.
          </footer>
        </>
      ) : null}
    </main>
  );
}
