import { io, type Socket } from "socket.io-client";

let socket: Socket | null = null;

export function connectSocket(): Socket {
  if (!socket) {
    // Mesma lógica do client REST: em dev o Vite faz proxy (origem própria),
    // em produção o socket precisa apontar pro host da API.
    const url = import.meta.env.VITE_API_URL;
    const opts = { path: "/socket.io", withCredentials: true, autoConnect: false };
    socket = url ? io(url, opts) : io(opts);
  }
  if (!socket.connected) {
    socket.connect();
  }
  return socket;
}

export function disconnectSocket() {
  socket?.disconnect();
}

export function getSocket(): Socket | null {
  return socket;
}
