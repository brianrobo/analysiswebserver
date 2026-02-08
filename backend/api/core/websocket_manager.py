"""
WebSocket Connection Manager for real-time analysis updates
Manages multiple WebSocket connections per analysis job
"""
import logging
from typing import Dict, Set, Any, Optional
from datetime import datetime
from fastapi import WebSocket
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for analysis jobs

    Supports:
    - Multiple clients per job_id
    - Real-time progress broadcasting
    - Connection lifecycle management
    - Heartbeat/ping-pong
    """

    def __init__(self):
        # job_id → Set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

        # WebSocket → metadata (connection time, last ping, etc.)
        self.connection_metadata: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, job_id: int, user_id: int):
        """
        Accept and register a new WebSocket connection

        Args:
            websocket: WebSocket connection
            job_id: Analysis job ID
            user_id: User ID (for authorization tracking)
        """
        await websocket.accept()

        # Add to active connections
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)

        # Store metadata
        self.connection_metadata[websocket] = {
            "job_id": job_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow(),
        }

        logger.info(f"WebSocket connected: job_id={job_id}, user_id={user_id}, total_connections={len(self.active_connections[job_id])}")

    def disconnect(self, websocket: WebSocket):
        """
        Remove and cleanup a WebSocket connection

        Args:
            websocket: WebSocket connection to remove
        """
        if websocket not in self.connection_metadata:
            return

        metadata = self.connection_metadata[websocket]
        job_id = metadata["job_id"]
        user_id = metadata["user_id"]

        # Remove from active connections
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)

            # Cleanup empty job entries
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

        # Remove metadata
        del self.connection_metadata[websocket]

        logger.info(f"WebSocket disconnected: job_id={job_id}, user_id={user_id}")

    async def broadcast_to_job(self, job_id: int, message: dict):
        """
        Broadcast a message to all connections for a specific job

        Args:
            job_id: Analysis job ID
            message: Message dictionary to send
        """
        if job_id not in self.active_connections:
            logger.debug(f"No active connections for job {job_id}")
            return

        # Get all connections for this job
        connections = self.active_connections[job_id].copy()

        # Track disconnected clients
        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to WebSocket: {e}")
                disconnected.append(websocket)

        # Cleanup disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)

    async def send_progress_update(
        self,
        job_id: int,
        progress: int,
        status: str,
        message: str = ""
    ):
        """
        Send progress update to all clients watching this job

        Args:
            job_id: Analysis job ID
            progress: Progress percentage (0-100)
            status: Job status (pending/running/completed/failed)
            message: Optional progress message
        """
        await self.broadcast_to_job(job_id, {
            "type": "progress",
            "job_id": job_id,
            "progress": progress,
            "status": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.debug(f"Progress update sent: job_id={job_id}, progress={progress}%, status={status}")

    async def send_completion(self, job_id: int, summary: dict):
        """
        Send completion notification with summary

        Args:
            job_id: Analysis job ID
            summary: Analysis summary data
        """
        await self.broadcast_to_job(job_id, {
            "type": "completed",
            "job_id": job_id,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.info(f"Completion notification sent: job_id={job_id}")

    async def send_error(self, job_id: int, error_message: str):
        """
        Send error notification

        Args:
            job_id: Analysis job ID
            error_message: Error description
        """
        await self.broadcast_to_job(job_id, {
            "type": "error",
            "job_id": job_id,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.error(f"Error notification sent: job_id={job_id}, error={error_message}")

    async def send_connected(self, websocket: WebSocket, job_id: int, current_status: str, current_progress: int):
        """
        Send initial connected message with current job state

        Args:
            websocket: WebSocket connection
            job_id: Analysis job ID
            current_status: Current job status
            current_progress: Current progress percentage
        """
        try:
            await websocket.send_json({
                "type": "connected",
                "job_id": job_id,
                "status": current_status,
                "progress": current_progress,
                "message": "WebSocket connection established",
                "timestamp": datetime.utcnow().isoformat()
            })

            logger.debug(f"Connected message sent: job_id={job_id}")
        except Exception as e:
            logger.error(f"Failed to send connected message: {e}")

    async def send_ping(self, websocket: WebSocket):
        """
        Send ping/heartbeat to client

        Args:
            websocket: WebSocket connection
        """
        try:
            await websocket.send_json({
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            })

            # Update last ping time
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["last_ping"] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Failed to send ping: {e}")

    def get_connection_count(self, job_id: int) -> int:
        """
        Get number of active connections for a job

        Args:
            job_id: Analysis job ID

        Returns:
            Number of active connections
        """
        if job_id not in self.active_connections:
            return 0
        return len(self.active_connections[job_id])

    def get_total_connections(self) -> int:
        """
        Get total number of active WebSocket connections

        Returns:
            Total connection count
        """
        return sum(len(connections) for connections in self.active_connections.values())

    def get_active_jobs(self) -> list[int]:
        """
        Get list of job IDs with active connections

        Returns:
            List of job IDs
        """
        return list(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()
