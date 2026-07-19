import { api, ApiError } from "./client";
import type { ChangePasswordInput, LoginInput, SetupInput, Usuario } from "@/types";
import type { ApiErrorBody } from "@/types";

async function uploadFoto(file: File): Promise<Usuario> {
  const form = new FormData();
  form.append("foto", file);
  const response = await fetch("/api/v1/auth/foto", {
    method: "POST",
    credentials: "include",
    body: form,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const errorBody = body as ApiErrorBody | null;
    throw new ApiError(
      errorBody?.error?.code ?? "UNKNOWN_ERROR",
      errorBody?.error?.message ?? "Erro ao enviar a foto",
      response.status,
    );
  }
  return body as Usuario;
}

export const authApi = {
  setupStatus: () => api.get<{ needs_setup: boolean }>("/auth/setup-status"),
  setup: (input: SetupInput) => api.post<Usuario>("/auth/setup", input),
  login: (input: LoginInput) => api.post<Usuario>("/auth/login", input),
  logout: () => api.post<void>("/auth/logout", {}),
  me: () => api.get<Usuario>("/auth/me"),
  changePassword: (input: ChangePasswordInput) => api.post<void>("/auth/change-password", input),
  uploadFoto,
};
