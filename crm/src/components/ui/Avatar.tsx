import { initials } from "@/lib/user";

interface AvatarProps {
  nome: string;
  fotoUrl?: string | null;
  size?: number;
  className?: string;
}

export function Avatar({ nome, fotoUrl, size = 36, className = "" }: AvatarProps) {
  if (fotoUrl) {
    return (
      <img
        src={fotoUrl}
        alt={nome}
        style={{ width: size, height: size }}
        className={`shrink-0 rounded-full object-cover ${className}`}
      />
    );
  }

  return (
    <span
      style={{ width: size, height: size, fontSize: size * 0.4 }}
      className={`flex shrink-0 items-center justify-center rounded-full bg-google-blue-bg font-medium text-google-blue-dark ${className}`}
    >
      {initials(nome)}
    </span>
  );
}
