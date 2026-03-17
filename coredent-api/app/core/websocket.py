"""
WebSocket Support
Real-time updates for the dental practice management system
"""

import json
import logging
from typing import Dict, Set, Any
from datetime import datetime
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    # Appointment events
    APPOINTMENT_CREATED = "appointment.created"
    APPOINTMENT_UPDATED = "appointment.updated"
    APPOINTMENT_CANCELLED = "appointment.cancelled"
    
    # Patient events
    PATIENT_CREATED = "patient.created"
    PATIENT_UPDATED = "patient.updated"
    
    # Billing events
    PAYMENT_RECEIVED = "payment.received"
    INVOICE_CREATED = "invoice.created"
    
    # Insurance events
    CLAIM_STATUS_UPDATED = "claim.status_updated"
    ELIGIBILITY_CHECKED = "eligibility.checked"
    
    # Lab events
    LAB_CASE_UPDATED = "lab_case.updated"
    LAB_RESULT_RECEIVED = "lab_result.received"
    
    # Chat/Message events
    NEW_MESSAGE = "message.new"
    MESSAGE_READ = "message.read"
    
    # System events
    NOTIFICATION = "notification"
    ERROR = "error"


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    """
    
    def __init__(self):
        # Active connections by user ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Active connections by practice ID
        self.practice_connections: Dict[str, Set[WebSocket]] = {}
        # All active connections for broadcasting
        self.all_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, user_id: str, practice_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        
        # Add to user-specific connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Add to practice-specific connections
        if practice_id not in self.practice_connections:
            self.practice_connections[practice_id] = set()
        self.practice_connections[practice_id].add(websocket)
        
        # Add to all connections
        self.all_connections.add(websocket)
        
        logger.info(f"WebSocket connected: user={user_id}, practice={practice_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str, practice_id: str):
        """Disconnect a WebSocket client"""
        # Remove from user connections
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remove from practice connections
        if practice_id in self.practice_connections:
            self.practice_connections[practice_id].discard(websocket)
            if not self.practice_connections[practice_id]:
                del self.practice_connections[practice_id]
        
        # Remove from all connections
        self.all_connections.discard(websocket)
        
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected sockets
            for ws in disconnected:
                self.active_connections[user_id].discard(ws)
    
    async def send_practice_message(self, message: dict, practice_id: str):
        """Send a message to all users in a practice"""
        if practice_id in self.practice_connections:
            disconnected = set()
            for websocket in self.practice_connections[practice_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to practice {practice_id}: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected sockets
            for ws in disconnected:
                self.practice_connections[practice_id].discard(ws)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        disconnected = set()
        for websocket in self.all_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.add(websocket)
        
        # Clean up
        for ws in disconnected:
            self.all_connections.discard(ws)


# Singleton instance
manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    WebSocket endpoint for real-time updates
    
    Connect: ws://host/ws
    Headers: Authorization: Bearer <token>
    
    Message format:
    {
        "event": "event.type",
        "data": {...},
        "timestamp": "ISO8601"
    }
    """
    practice_id = str(current_user.practice_id)
    user_id = str(current_user.id)
    
    await manager.connect(websocket, user_id, practice_id)
    
    try:
        while True:
            # Wait for messages from client (ping/pong, subscriptions, etc.)
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle subscription to specific events
                if message.get("type") == "subscribe":
                    # Client wants to subscribe to specific events
                    # For now, auto-subscribe to practice events
                    await websocket.send_json({
                        "event": "subscribed",
                        "data": {"events": ["*"]},
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from user {user_id}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, practice_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id, practice_id)


# Convenience functions for sending events

async def notify_appointment_created(appointment_data: dict, practice_id: str):
    """Notify about new appointment"""
    await manager.send_practice_message({
        "event": EventType.APPOINTMENT_CREATED,
        "data": appointment_data,
        "timestamp": datetime.utcnow().isoformat(),
    }, practice_id)


async def notify_appointment_updated(appointment_data: dict, practice_id: str):
    """Notify about appointment update"""
    await manager.send_practice_message({
        "event": EventType.APPOINTMENT_UPDATED,
        "data": appointment_data,
        "timestamp": datetime.utcnow().isoformat(),
    }, practice_id)


async def notify_new_message(message_data: dict, user_id: str):
    """Notify user about new message"""
    await manager.send_personal_message({
        "event": EventType.NEW_MESSAGE,
        "data": message_data,
        "timestamp": datetime.utcnow().isoformat(),
    }, user_id)


async def notify_claim_update(claim_data: dict, practice_id: str):
    """Notify about insurance claim status update"""
    await manager.send_practice_message({
        "event": EventType.CLAIM_STATUS_UPDATED,
        "data": claim_data,
        "timestamp": datetime.utcnow().isoformat(),
    }, practice_id)


async def notify_lab_case_update(case_data: dict, practice_id: str):
    """Notify about lab case update"""
    await manager.send_practice_message({
        "event": EventType.LAB_CASE_UPDATED,
        "data": case_data,
        "timestamp": datetime.utcnow().isoformat(),
    }, practice_id)


async def notify_payment_received(payment_data: dict, practice_id: str):
    """Notify about received payment"""
    await manager.send_practice_message({
        "event": EventType.PAYMENT_RECEIVED,
        "data": payment_data,
        "timestamp": datetime.utcnow().isoformat(),
    }, practice_id)
