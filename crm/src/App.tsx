import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { ToastProvider } from "@/components/ui/ToastProvider";
import { AuthProvider } from "@/contexts/AuthContext";
import { RequireAdmin, RequireAuth, RequireGrupo } from "@/components/auth/RouteGuards";
import { LoginPage } from "@/pages/auth/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { ClientesPage } from "@/pages/clientes/ClientesPage";
import { ProjetosPage } from "@/pages/projetos/ProjetosPage";
import { ProjetoDetailPage } from "@/pages/projetos/ProjetoDetailPage";
import { UsinasPage } from "@/pages/usinas/UsinasPage";
import { UsinaDetailPage } from "@/pages/usinas/UsinaDetailPage";
import { ConcessionariasPage } from "@/pages/concessionarias/ConcessionariasPage";
import { AdminPage } from "@/pages/admin/AdminPage";
import { IndicacoesPage } from "@/pages/indicacoes/IndicacoesPage";
import { AtendimentoPage } from "@/pages/atendimento/AtendimentoPage";
import { SuportePage } from "@/pages/suporte/SuportePage";
import { WorkspacePage } from "@/pages/workspace/WorkspacePage";

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<RequireAuth />}>
              <Route element={<AppShell />}>
                <Route index element={<DashboardPage />} />
                <Route path="clientes" element={<ClientesPage />} />
                <Route path="projetos" element={<ProjetosPage />} />
                <Route path="projetos/:id" element={<ProjetoDetailPage />} />
                <Route path="usinas" element={<UsinasPage />} />
                <Route path="usinas/:id" element={<UsinaDetailPage />} />
                <Route path="concessionarias" element={<ConcessionariasPage />} />
                <Route path="atendimento" element={<AtendimentoPage />} />
                <Route path="suporte" element={<SuportePage />} />
                <Route path="workspace/:grupo" element={<WorkspacePage />} />
                <Route element={<RequireGrupo grupo="vendas" />}>
                  <Route path="indicacoes" element={<IndicacoesPage />} />
                </Route>
                <Route element={<RequireAdmin />}>
                  <Route path="admin" element={<AdminPage />} />
                </Route>
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ToastProvider>
  );
}
