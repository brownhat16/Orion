"""
WebSocket Routes

Real-time updates for generation progress.
"""

from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio


router = APIRouter()


# Connection manager for WebSocket clients
class ConnectionManager:
    """Manages WebSocket connections per project."""
    
    def __init__(self):
        # Map of project_id -> set of connected WebSockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: int):
        """Accept and store a new connection."""
        await websocket.accept()
        
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        
        self.active_connections[project_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, project_id: int):
        """Remove a disconnected client."""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
    
    async def broadcast_to_project(self, project_id: int, message: dict):
        """Send a message to all clients watching a project."""
        if project_id not in self.active_connections:
            return
        
        dead_connections = set()
        
        for connection in self.active_connections[project_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            self.active_connections[project_id].discard(conn)


# Singleton manager
manager = ConnectionManager()


@router.websocket("/projects/{project_id}")
async def project_websocket(
    websocket: WebSocket,
    project_id: int,
):
    """
    WebSocket endpoint for real-time generation updates.
    
    Clients connect to receive:
    - Phase changes
    - Chapter progress
    - Beat completion
    - Error notifications
    
    Message format:
    {
        "type": "progress" | "error" | "complete",
        "data": {...}
    }
    """
    await manager.connect(websocket, project_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "data": {"project_id": project_id}
        })
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Receive any client messages (like heartbeats)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # Heartbeat interval
                )
                
                # Handle client messages
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await websocket.send_json({"type": "heartbeat"})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
    except Exception as e:
        manager.disconnect(websocket, project_id)


# ==================== BROADCAST FUNCTIONS ====================
# These are called from the Celery workers to send updates

async def broadcast_progress(
    project_id: int,
    phase: str,
    chapter: int,
    beat: int = None,
    total_beats: int = None,
    message: str = None,
):
    """Broadcast generation progress."""
    await manager.broadcast_to_project(project_id, {
        "type": "progress",
        "data": {
            "phase": phase,
            "chapter": chapter,
            "beat": beat,
            "total_beats": total_beats,
            "message": message,
        }
    })


async def broadcast_chapter_complete(
    project_id: int,
    chapter: int,
    word_count: int,
):
    """Broadcast chapter completion."""
    await manager.broadcast_to_project(project_id, {
        "type": "chapter_complete",
        "data": {
            "chapter": chapter,
            "word_count": word_count,
        }
    })


async def broadcast_error(
    project_id: int,
    error: str,
    recoverable: bool = True,
):
    """Broadcast an error."""
    await manager.broadcast_to_project(project_id, {
        "type": "error",
        "data": {
            "error": error,
            "recoverable": recoverable,
        }
    })


async def broadcast_complete(
    project_id: int,
    total_words: int,
    total_chapters: int,
):
    """Broadcast generation complete."""
    await manager.broadcast_to_project(project_id, {
        "type": "complete",
        "data": {
            "total_words": total_words,
            "total_chapters": total_chapters,
        }
    })
