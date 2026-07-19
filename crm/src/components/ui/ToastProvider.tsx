import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { IconAlertCircle, IconCheckCircle } from "@/components/icons";

interface Toast {
  id: number;
  kind: "success" | "error";
  message: string;
}

interface ToastContextValue {
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counter = useRef(0);

  const push = useCallback((kind: Toast["kind"], message: string) => {
    const id = ++counter.current;
    setToasts((prev) => [...prev, { id, kind, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const value: ToastContextValue = {
    showSuccess: (message) => push("success", message),
    showError: (message) => push("error", message),
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      {createPortal(
        <div className="fixed bottom-5 left-1/2 z-[100] flex -translate-x-1/2 flex-col gap-2">
          {toasts.map((toast) => (
            <div
              key={toast.id}
              className={`flex items-center gap-2 px-4 py-3 text-sm text-white shadow-lg ${
                toast.kind === "error" ? "bg-google-red" : "bg-ink"
              }`}
            >
              {toast.kind === "error" ? (
                <IconAlertCircle width={18} height={18} />
              ) : (
                <IconCheckCircle width={18} height={18} />
              )}
              {toast.message}
            </div>
          ))}
        </div>,
        document.body,
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast deve ser usado dentro de ToastProvider");
  return ctx;
}
