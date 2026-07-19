import { useEffect, useRef, useState, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { IconChevronDown } from "@/components/icons";

const fieldBase =
  "w-full border border-border bg-white px-3.5 py-2.5 text-sm text-ink outline-none transition-shadow focus:border-google-blue focus:ring-2 focus:ring-google-blue-bg";

interface WrapperProps {
  label: string;
  required?: boolean;
  error?: string;
  children: ReactNode;
}

export function FieldWrapper({ label, required, error, children }: WrapperProps) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-ink-secondary">
        {label}
        {required && <span className="text-google-red"> *</span>}
      </span>
      {children}
      {error && <span className="mt-1 block text-xs text-google-red">{error}</span>}
    </label>
  );
}

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function Input({ label, required, error, className = "", ...rest }: InputProps) {
  return (
    <FieldWrapper label={label} required={required} error={error}>
      <input className={`${fieldBase} ${className}`} {...rest} />
    </FieldWrapper>
  );
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  error?: string;
}

export function Select({ label, required, error, className = "", children, ...rest }: SelectProps) {
  return (
    <FieldWrapper label={label} required={required} error={error}>
      <select className={`${fieldBase} ${className}`} {...rest}>
        {children}
      </select>
    </FieldWrapper>
  );
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
}

export function Textarea({ label, required, error, className = "", ...rest }: TextareaProps) {
  return (
    <FieldWrapper label={label} required={required} error={error}>
      <textarea className={`${fieldBase} resize-none ${className}`} {...rest} />
    </FieldWrapper>
  );
}

interface CheckboxGroupOption<T extends string> {
  value: T;
  label: string;
}

interface CheckboxGroupProps<T extends string> {
  label: string;
  required?: boolean;
  error?: string;
  options: CheckboxGroupOption<T>[];
  values: T[];
  onChange: (values: T[]) => void;
  hint?: string;
}

export function CheckboxGroup<T extends string>({
  label,
  required,
  error,
  options,
  values,
  onChange,
  hint,
}: CheckboxGroupProps<T>) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggle = (value: T) => {
    onChange(values.includes(value) ? values.filter((v) => v !== value) : [...values, value]);
  };

  const resumo =
    values.length === 0
      ? "Nenhum selecionado"
      : options
          .filter((opt) => values.includes(opt.value))
          .map((opt) => opt.label)
          .join(", ");

  return (
    <div className="relative" ref={ref}>
      <span className="mb-1.5 block text-xs font-medium text-ink-secondary">
        {label}
        {required && <span className="text-google-red"> *</span>}
      </span>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`${fieldBase} flex items-center justify-between gap-2 text-left`}
      >
        <span className="truncate text-ink">{resumo}</span>
        <IconChevronDown width={16} height={16} className={`shrink-0 text-ink-faint transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute left-0 top-full z-20 mt-1 w-full border border-border bg-white shadow-lg">
          <div className="flex flex-wrap gap-2 p-3">
            {options.map((opt) => {
              const checked = values.includes(opt.value);
              return (
                <label
                  key={opt.value}
                  className={`flex cursor-pointer items-center gap-2 border px-3 py-1.5 text-sm transition-colors ${
                    checked
                      ? "border-google-blue bg-google-blue-bg text-google-blue-dark"
                      : "border-border text-ink-secondary hover:bg-canvas"
                  }`}
                >
                  <input
                    type="checkbox"
                    className="sr-only"
                    checked={checked}
                    onChange={() => toggle(opt.value)}
                  />
                  {opt.label}
                </label>
              );
            })}
          </div>
        </div>
      )}
      {hint && !error && <span className="mt-1 block text-xs text-ink-faint">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-google-red">{error}</span>}
    </div>
  );
}
