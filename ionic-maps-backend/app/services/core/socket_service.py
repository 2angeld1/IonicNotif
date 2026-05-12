from fastapi import WebSocket
from typing import List

class SocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔌 Cliente conectado al socket de Caitlyn. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"🔌 Cliente desconectado. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Envía un mensaje a todos los clientes conectados."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                # Si falla, probablemente la conexión se cerró
                print(f"⚠️ Error enviando broadcast: {e}")
                self.active_connections.remove(connection)

# Instancia única para toda la app
socket_manager = SocketManager()
