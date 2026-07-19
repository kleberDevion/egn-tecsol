import { io, type Socket } from "socket.io-client";

let socket: Socket | null = null;

export function connectSocket(): Socket {
  if (!socket) {
    socket = io({ path: "/socket.io", withCredentials: true, autoConnect: false });
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
