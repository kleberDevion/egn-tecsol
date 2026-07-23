import { initials } from "@/lib/user";

// A API devolve o caminho relativo (/api/v1/auth/foto/3). Em producao o CRM e
// a API ficam em enderecos diferentes, entao o caminho precisa ser resolvido
// contra o host da API — senao o navegador busca no proprio CRM e da 404.
const API_BASE = import.meta.env.VITE_API_URL ?? "";

interface AvatarProps {
  nome: string;
  fotoUrl?: string | null;
  size?: number;
  className?: string;
}

export function Avatar({ nome, fotoUrl, size = 36, className = "" }: AvatarProps) {
  if (fotoUrl) {
    const src = fotoUrl.startsWith("http") ? fotoUrl : `${API_BASE}${fotoUrl}`;
    return (
      <img
        src={src}
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
