import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

// Estado do menu lateral:
//  - desktop: colapsada (so icones) ou expandida, com a preferencia salva;
//  - mobile: gaveta que abre por cima do conteudo (a barra fixa nao cabe).
// Fica num contexto porque o AppShell ajusta a margem do conteudo junto com a
// largura da barra, e a TopBar precisa do botao que abre a gaveta.
const CHAVE = "tecsol:sidebar-colapsada";

type Ctx = {
  colapsada: boolean;
  alternar: () => void;
  mobileAberta: boolean;
  abrirMobile: () => void;
  fecharMobile: () => void;
};

const SidebarContext = createContext<Ctx>({
  colapsada: false,
  alternar: () => {},
  mobileAberta: false,
  abrirMobile: () => {},
  fecharMobile: () => {},
});

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [colapsada, setColapsada] = useState(false);
  const [mobileAberta, setMobileAberta] = useState(false);

  // Le a preferencia salva depois da montagem (evita divergencia na hidratacao).
  useEffect(() => {
    setColapsada(localStorage.getItem(CHAVE) === "1");
  }, []);

  // Gaveta aberta trava o scroll do fundo.
  useEffect(() => {
    document.body.style.overflow = mobileAberta ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileAberta]);

  const alternar = useCallback(() => {
    setColapsada((atual) => {
      const proximo = !atual;
      localStorage.setItem(CHAVE, proximo ? "1" : "0");
      return proximo;
    });
  }, []);

  const abrirMobile = useCallback(() => setMobileAberta(true), []);
  const fecharMobile = useCallback(() => setMobileAberta(false), []);

  return (
    <SidebarContext.Provider value={{ colapsada, alternar, mobileAberta, abrirMobile, fecharMobile }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  return useContext(SidebarContext);
}
