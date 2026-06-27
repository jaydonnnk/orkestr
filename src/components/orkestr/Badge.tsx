import { Persona } from "@/lib/mock-data";

type BadgeVariant = "amber" | "negative" | "ref" | "status";
type StatusDot = "active" | "complete" | "pending";

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
  statusDot?: StatusDot;
}

export function Badge({ variant, children, statusDot }: BadgeProps) {
  if (variant === "status") {
    return (
      <span className="badge-status">
        {statusDot ? <span className={`dot dot--${statusDot}`} /> : null}
        {children}
      </span>
    );
  }

  return <span className={`badge-${variant}`}>{children}</span>;
}

interface AvatarProps {
  persona: Persona;
  size?: "md" | "lg";
  initials: string;
}

export function Avatar({ persona, size = "md", initials }: AvatarProps) {
  return (
    <span className={`avatar avatar--${size} avatar--${persona}`} aria-hidden="true">
      {initials}
    </span>
  );
}

export function AvatarGroup({ personas }: { personas: { persona: Persona; initials: string }[] }) {
  return (
    <div className="avatar-group">
      {personas.map((p) => (
        <Avatar key={p.persona} persona={p.persona} initials={p.initials} />
      ))}
    </div>
  );
}

export function TagChip({
  children,
  positive,
}: {
  children: React.ReactNode;
  positive?: boolean;
}) {
  return (
    <span className={`tag-chip${positive ? " tag-positive" : ""}`}>{children}</span>
  );
}
