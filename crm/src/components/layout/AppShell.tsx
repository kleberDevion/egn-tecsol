import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export function AppShell() {
  return (
    <div className="min-h-screen bg-canvas">
      <TopBar />
      <div className="flex">
        <Sidebar />
        <main className="min-w-0 flex-1 md:ml-64">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
