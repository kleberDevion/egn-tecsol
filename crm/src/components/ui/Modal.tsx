import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { IconButton } from "./IconButton";
import { IconX } from "@/components/icons";

interface ModalProps {
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg";
}

const sizes = {
  sm: "max-w-md",
  md: "max-w-xl",
  lg: "max-w-3xl",
};

export function Modal({ title, onClose, children, footer, size = "md" }: ModalProps) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const dragState = useRef<{ startX: number; startY: number; origX: number; origY: number } | null>(null);
  const [dragging, setDragging] = useState(false);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    const drag = dragState.current;
    if (!drag) return;
    setPosition({
      x: drag.origX + (e.clientX - drag.startX),
      y: drag.origY + (e.clientY - drag.startY),
    });
  }, []);

  const handleMouseUp = useCallback(() => {
    dragState.current = null;
    setDragging(false);
  }, []);

  useEffect(() => {
    if (!dragging) return;
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [dragging, handleMouseMove, handleMouseUp]);

  const handleHeaderMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest("button")) return;
    dragState.current = { startX: e.clientX, startY: e.clientY, origX: position.x, origY: position.y };
    setDragging(true);
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div
        className={`relative w-full ${sizes[size]} max-h-[90vh] overflow-y-auto bg-white shadow-2xl`}
        style={{ transform: `translate(${position.x}px, ${position.y}px)` }}
      >
        <div
          onMouseDown={handleHeaderMouseDown}
          className={`sticky top-0 flex items-center justify-between border-b border-border bg-white px-6 py-4 ${
            dragging ? "cursor-grabbing select-none" : "cursor-grab"
          }`}
        >
          <h2 className="text-lg font-medium text-ink">{title}</h2>
          <IconButton label="Fechar" onClick={onClose}>
            <IconX width={18} height={18} />
          </IconButton>
        </div>
        <div className="px-6 py-5">{children}</div>
        {footer && (
          <div className="sticky bottom-0 flex justify-end gap-3 border-t border-border bg-white px-6 py-4">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body,
  );
}
