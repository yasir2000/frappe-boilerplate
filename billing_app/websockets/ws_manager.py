from fastapi import WebSocket
from typing import Dict, List
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        await self.send_personal_message(f"Connected as {client_id}", client_id)
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except:
                # Connection might be closed, remove it
                self.disconnect(client_id)
    
    async def broadcast(self, message: str):
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except:
                disconnected.append(client_id)
        
        # Remove disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def send_invoice_update(self, invoice_id: int, status: str, client_id: str = None):
        message = json.dumps({
            "type": "invoice_update",
            "invoice_id": invoice_id,
            "status": status,
            "timestamp": str(datetime.utcnow())
        })
        
        if client_id:
            await self.send_personal_message(message, client_id)
        else:
            await self.broadcast(message)
    
    async def send_workflow_notification(self, invoice_id: int, action: str, user_id: int = None):
        message = json.dumps({
            "type": "workflow_notification",
            "invoice_id": invoice_id,
            "action": action,
            "user_id": user_id,
            "timestamp": str(datetime.utcnow())
        })
        await self.broadcast(message)

from datetime import datetime
