import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { ChangePasswordModal } from "./ChangePasswordModal";
import { ChangePhotoModal } from "./ChangePhotoModal";
import { Avatar } from "@/components/ui/Avatar";
import { IconCamera, IconChevronDown, IconLock, IconLogout, IconShield } from "@/components/icons";

export function ProfileMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [changingPhoto, setChangingPhoto] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!user) return null;

  async function handleLogout() {
    setOpen(false);
    await logout();
    navigate("/login");
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 py-1 pl-1 pr-2 text-sm transition-colors hover:bg-canvas cursor-pointer"
      >
        <Avatar nome={user.nome} fotoUrl={user.foto_url} size={36} />
        <IconChevronDown width={16} height={16} className="text-ink-faint" />
      </button>

      {open && (
        <div className="absolute right-0 top-12 z-20 w-64 border border-border bg-white py-2 shadow-lg">
          <div className="flex items-center gap-3 border-b border-border px-4 py-3">
            <Avatar nome={user.nome} fotoUrl={user.foto_url} size={40} />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-ink">{user.nome}</p>
              <p className="truncate text-xs text-ink-secondary">{user.email}</p>
              <p className="mt-0.5 text-xs text-ink-faint">
                {user.papel === "admin" ? "Administrador" : "Operador"}
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              setOpen(false);
              setChangingPhoto(true);
            }}
            className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm text-ink-secondary hover:bg-canvas cursor-pointer"
          >
            <IconCamera width={18} height={18} />
            Alterar foto
          </button>
          <button
            onClick={() => {
              setOpen(false);
              setChangingPassword(true);
            }}
            className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm text-ink-secondary hover:bg-canvas cursor-pointer"
          >
            <IconLock width={18} height={18} />
            Alterar senha
          </button>
          {user.papel === "admin" && (
            <button
              onClick={() => {
                setOpen(false);
                navigate("/admin");
              }}
              className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm text-ink-secondary hover:bg-canvas cursor-pointer"
            >
              <IconShield width={18} height={18} />
              Administração
            </button>
          )}
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm text-google-red hover:bg-google-red-bg cursor-pointer"
          >
            <IconLogout width={18} height={18} />
            Sair
          </button>
        </div>
      )}

      {changingPhoto && <ChangePhotoModal onClose={() => setChangingPhoto(false)} />}
      {changingPassword && <ChangePasswordModal onClose={() => setChangingPassword(false)} />}
    </div>
  );
}
