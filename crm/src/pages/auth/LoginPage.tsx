import { useEffect, useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { authApi } from "@/api/auth";
import { useAuth } from "@/contexts/AuthContext";
import { Input } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { Spinner, FullPageSpinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/ToastProvider";
import { getErrorMessage } from "@/lib/errors";
import { IconBolt } from "@/components/icons";

export function LoginPage() {
  const { user, login, setup } = useAuth();
  const { showError } = useToast();
  const [needsSetup, setNeedsSetup] = useState<boolean | null>(null);
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    authApi
      .setupStatus()
      .then((res) => setNeedsSetup(res.needs_setup))
      .catch(() => setNeedsSetup(false));
  }, []);

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (needsSetup) {
        await setup({ nome, email, senha });
      } else {
        await login({ email, senha });
      }
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4">
      <div className="w-full max-w-sm border border-border bg-white p-8">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-google-blue text-white">
            <IconBolt width={20} height={20} />
          </span>
          <div>
            <h1 className="text-lg font-medium text-ink">
              <span className="font-medium">Tecsol</span> CRM
            </h1>
            {needsSetup === null ? (
              <p className="mt-1 text-sm text-ink-secondary">Verificando configuração…</p>
            ) : needsSetup ? (
              <p className="mt-1 text-sm text-ink-secondary">Crie a conta de administrador para começar</p>
            ) : (
              <p className="mt-1 text-sm text-ink-secondary">Entre com sua conta</p>
            )}
          </div>
        </div>

        {needsSetup === null ? (
          <FullPageSpinner />
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {needsSetup && (
              <Input
                label="Nome"
                required
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                autoComplete="name"
              />
            )}
            <Input
              label="E-mail"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
            <Input
              label="Senha"
              type="password"
              required
              minLength={needsSetup ? 8 : undefined}
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              autoComplete={needsSetup ? "new-password" : "current-password"}
            />
            <Button type="submit" variant="primary" disabled={submitting} className="mt-2 w-full">
              {submitting && <Spinner className="h-4 w-4 border-white/40 border-t-white" />}
              {needsSetup ? "Criar conta de administrador" : "Entrar"}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
