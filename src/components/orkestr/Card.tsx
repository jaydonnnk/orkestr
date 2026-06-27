import { HTMLAttributes } from "react";

type CardVariant = "default" | "surface" | "dark" | "featured";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
}

export function Card({ variant = "default", className = "", children, ...props }: CardProps) {
  const variantClass =
    variant === "surface"
      ? "card-surface"
      : variant === "dark"
        ? "card-dark"
        : variant === "featured"
          ? "card card-featured"
          : "card";

  return (
    <div className={`${variantClass} ${className}`.trim()} {...props}>
      {children}
    </div>
  );
}
