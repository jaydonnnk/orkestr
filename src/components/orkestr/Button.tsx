import { ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "tertiary" | "destructive";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  inline?: boolean;
}

export function Button({
  variant = "primary",
  inline = false,
  className = "",
  children,
  ...props
}: ButtonProps) {
  const classes = [`btn-${variant}`, inline ? "btn-inline" : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <button type="button" className={classes} {...props}>
      {children}
    </button>
  );
}

export function IconButton({
  children,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button type="button" className={`btn-icon ${className}`.trim()} {...props}>
      {children}
    </button>
  );
}
