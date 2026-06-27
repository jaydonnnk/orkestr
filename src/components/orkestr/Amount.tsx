interface AmountProps {
  value: number;
  size?: "lg" | "md" | "sm";
  negative?: boolean;
  prefix?: string;
}

function formatAmount(value: number) {
  return value.toFixed(2);
}

export function Amount({ value, size = "md", negative, prefix = "$" }: AmountProps) {
  const className = `text-amount-${size}${negative ? " text-amount-negative" : ""}`;

  return (
    <span className={className}>
      {prefix}
      {formatAmount(Math.abs(value))}
    </span>
  );
}
