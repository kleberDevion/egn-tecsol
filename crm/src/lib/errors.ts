import { ApiError } from "@/api/client";

export function getErrorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "Ocorreu um erro inesperado.";
}
