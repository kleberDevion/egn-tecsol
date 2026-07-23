import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { SidebarProvider, useSidebar } from "@/contexts/SidebarContext";

function Conteudo() {
  const { colapsada } = useSidebar();
  return (
    <div className="min-h-screen bg-canvas">
      <TopBar />
      <div className="flex">
        <Sidebar />
        {/* A margem acompanha a largura da barra (zero no mobile, onde ela vira gaveta). */}
        <main
          className={`min-w-0 flex-1 transition-[margin] duration-200 ${colapsada ? "md:ml-16" : "md:ml-64"}`}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function AppShell() {
  return (
    <SidebarProvider>
      <Conteudo />
    </SidebarProvider>
  );
}
