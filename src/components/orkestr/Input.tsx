import { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export function Input({ label, id, ...props }: InputProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");

  return (
    <div>
      <label htmlFor={inputId} className="input-label">
        {label}
      </label>
      <input id={inputId} className="input" {...props} />
    </div>
  );
}
