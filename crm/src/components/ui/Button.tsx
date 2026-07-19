import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "text" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  icon?: ReactNode;
}

const base =
  "inline-flex items-center gap-2 justify-center text-sm font-medium px-5 py-2.5 transition-colors disabled:opacity-40 disabled:pointer-events-none cursor-pointer";

const variants: Record<Variant, string> = {
  primary: "bg-google-blue text-white hover:bg-google-blue-dark shadow-sm",
  secondary: "bg-white text-google-blue border border-border hover:bg-google-blue-bg",
  text: "text-google-blue hover:bg-google-blue-bg px-3",
  danger: "bg-white text-google-red border border-border hover:bg-google-red-bg",
};

export function Button({ variant = "secondary", icon, className = "", children, ...rest }: ButtonProps) {
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...rest}>
      {icon}
      {children}
    </button>
  );
}
