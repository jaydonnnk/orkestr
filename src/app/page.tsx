"use client";

import { useEffect, useMemo, useState } from "react";
import styles from "./page.module.css";

const SESSION_ID = "ORK-001";
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

async function readDemo(reseed = false): Promise<DemoState> {
  if (reseed) {
    await fetchJson<{ ok: boolean }>(`/api/dev/reseed`, {
      method: "POST",
      body: "{}",
    });
  }

  const [status, negotiation, plan, handshake, settlement] = await Promise.all([
    fetchJson<{ phase?: string }>(`/api/status/${SESSION_ID}`),
    fetchJson<Message[]>(`/api/negotiation/${SESSION_ID}`),
    fetchJson<Plan>(`/api/plan/${SESSION_ID}`),
    fetchJson<Handshake>(`/api/handshake/${SESSION_ID}`),
    fetchJson<Settlement>(`/api/settlement/${SESSION_ID}`),
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
  const [state, setState] = useState<DemoState | null>(null);
  const [loading, setLoading] = useState(true);
  const [settling, setSettling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runCheck(reseed = false) {
    setLoading(true);
    setError(null);

    try {
      setState(await readDemo(reseed));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reach backend");
    } finally {
      setLoading(false);
    }
  }

  async function settleTransfers() {
    if (!state?.settlement.transfers?.length) {
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
          fetchJson<{ ok: boolean }>(`/api/settle/${SESSION_ID}`, {
            method: "POST",
            body: JSON.stringify({ person_id }),
          }),
        ),
      );

      setState(await readDemo(false));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to settle transfers");
    } finally {
      setSettling(false);
    }
  }

  useEffect(() => {
    let active = true;

    async function loadInitial() {
      try {
        const nextState = await readDemo(false);
        if (active) {
          setState(nextState);
          setError(null);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Unable to reach backend");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadInitial();

    return () => {
      active = false;
    };
  }, []);

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

  return (
    <main className={styles.shell}>
      <section className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>Orkestr demo console</p>
          <h1>System check for {SESSION_ID}</h1>
          <p>
            Backend: <code>{API_BASE}</code>
          </p>
        </div>
        <div className={styles.actions}>
          <button className={styles.secondaryButton} type="button" onClick={() => void runCheck(true)}>
            Reseed ORK-001
          </button>
          <button className={styles.primaryButton} type="button" onClick={() => void runCheck(false)}>
            Run check
          </button>
        </div>
      </section>

      <section className={styles.checks} aria-label="System checks">
        <CheckPill label="Plan" ok={checks.plan} detail={state?.phase ?? "loading"} />
        <CheckPill label="ACP" ok={checks.acp && checks.counter && checks.payment} detail={paymentMode(state?.handshake.mandate)} />
        <CheckPill label="x402" ok={checks.x402} detail={checks.x402 ? "settled" : "pending"} />
      </section>

      {error ? <p className={styles.error}>Backend check failed: {error}</p> : null}
      {loading && !state ? <p className={styles.loading}>Loading ORK-001...</p> : null}

      {state ? (
        <section className={styles.phoneGrid}>
          <NegotiationPhone messages={state.negotiation} plan={state.plan} />
          <PlanPhone plan={state.plan} />
          <AcpPhone handshake={state.handshake} />
          <SettlementPhone settlement={state.settlement} onSettle={() => void settleTransfers()} settling={settling} />
        </section>
      ) : null}

      <footer className={styles.footer}>
        Last checked {state?.checkedAt ?? "--"} - ACP and x402 are read from the live API.
      </footer>
    </main>
  );
}
