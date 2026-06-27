import Link from "next/link";
import { ReactNode } from "react";

interface MobileFrameProps {
  children: ReactNode;
}

export function MobileFrame({ children }: MobileFrameProps) {
  return (
    <div className="desktop-shell">
      <div className="mobile-frame">{children}</div>
    </div>
  );
}

interface ScreenHeaderProps {
  title: string;
  subtitle?: string;
  backHref?: string;
  action?: ReactNode;
}

export function ScreenHeader({ title, subtitle, backHref = "/", action }: ScreenHeaderProps) {
  return (
    <header className="screen-header">
      <div className="screen-header-row">
        {backHref ? (
          <Link href={backHref} className="btn-icon" aria-label="Go back">
            ←
          </Link>
        ) : null}
        {action}
      </div>
      <h1 className="text-display-md">{title}</h1>
      {subtitle ? <p className="text-body-sm" style={{ marginTop: "var(--space-sm)" }}>{subtitle}</p> : null}
    </header>
  );
}

interface ScreenProps {
  children: ReactNode;
  soft?: boolean;
}

export function Screen({ children, soft }: ScreenProps) {
  return <div className={`screen${soft ? " screen--soft" : ""}`}>{children}</div>;
}

export function ScreenContent({ children, soft }: { children: ReactNode; soft?: boolean }) {
  return (
    <main className={`screen-content${soft ? " screen-content--soft" : ""}`}>
      {children}
    </main>
  );
}

export function BottomBar({ children }: { children: ReactNode }) {
  return <footer className="bottom-bar">{children}</footer>;
}

export function ComponentLabel({ children }: { children: ReactNode }) {
  return <p className="text-eyebrow component-label">{children}</p>;
}
