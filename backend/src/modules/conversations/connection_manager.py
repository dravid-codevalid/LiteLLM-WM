# File: connection_manager.py. Description: WebSocket connection tracking. Consists of: ConnectionManager class to handle active websockets and broadcast presence per workspace.
import uuid
from collections.abc import AsyncIterator

from fastapi import WebSocket


class ConnectionManager:
    """Tracks active WebSocket connections per workspace for presence."""

    def __init__(self):
        # workspace_id -> {user_id: (username, websocket)}
        self._connections: dict[uuid.UUID, dict[uuid.UUID, tuple[str, WebSocket]]] = {}

    async def connect(self, ws: WebSocket, workspace_id: uuid.UUID, user_id: uuid.UUID, username: str):
        await ws.accept()
        if workspace_id not in self._connections:
            self._connections[workspace_id] = {}
        self._connections[workspace_id][user_id] = (username, ws)
        await self._broadcast_presence(workspace_id)

    async def disconnect(self, workspace_id: uuid.UUID, user_id: uuid.UUID):
        if workspace_id in self._connections:
            self._connections[workspace_id].pop(user_id, None)
            if not self._connections[workspace_id]:
                del self._connections[workspace_id]
            else:
                await self._broadcast_presence(workspace_id)

    async def _broadcast_presence(self, workspace_id: uuid.UUID):
        if workspace_id not in self._connections:
            return
        active_users = [
            {"id": str(uid), "username": uname}
            for uid, (uname, _) in self._connections[workspace_id].items()
        ]
        msg = {"type": "presence_update", "active_users": active_users}
        for _, ws in self._connections[workspace_id].values():
            try:
                await ws.send_json(msg)
            except Exception:
                pass


manager = ConnectionManager()
