"""
WebSocket endpoints for real-time analysis updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional
import asyncio
import logging

from api.core.websocket_manager import manager
from api.core.security import verify_token
from api.core.cache import cache
from api.core.dependencies import get_db
from api.db.models import User, AnalysisJob

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


async def get_current_user_ws(token: str = Query(...), db: Session = Depends(get_db)) -> Optional[User]:
    """
    Get current user from JWT token (for WebSocket)

    WebSocket doesn't support headers easily, so we use query parameter
    """
    try:
        payload = verify_token(token)
        user_id = int(payload.get("sub"))

        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        return None


@router.websocket("/ws/analysis/{job_id}")
async def websocket_analysis_endpoint(
    websocket: WebSocket,
    job_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time analysis updates

    **Connection URL**: ws://localhost:8000/ws/analysis/{job_id}?token={jwt_token}

    **Message Types**:
    - connected: Initial connection confirmation with current job state
    - progress: Progress update (0-100%)
    - completed: Analysis completed with summary
    - error: Error occurred
    - ping: Server heartbeat (client should respond with pong)

    **Client Messages**:
    - pong: Response to ping (optional)

    **Authentication**: JWT token via query parameter
    """
    # Authenticate user
    current_user = await get_current_user_ws(token, db)

    if not current_user:
        await websocket.close(code=1008, reason="Authentication failed")
        logger.warning(f"WebSocket connection rejected: invalid token for job {job_id}")
        return

    # Verify job ownership
    job = db.query(AnalysisJob).filter(
        AnalysisJob.id == job_id,
        AnalysisJob.user_id == current_user.id
    ).first()

    if not job:
        await websocket.close(code=1008, reason="Analysis job not found or access denied")
        logger.warning(f"WebSocket connection rejected: job {job_id} not found for user {current_user.id}")
        return

    # Accept connection
    await manager.connect(websocket, job_id, current_user.id)

    try:
        # Send initial connected message with current job state
        await manager.send_connected(
            websocket,
            job_id,
            job.status,
            job.progress
        )

        # Check cache for current progress
        cached_progress = await cache.get_progress(job_id)
        if cached_progress:
            await manager.send_progress_update(
                job_id,
                cached_progress["progress"],
                cached_progress["status"],
                cached_progress.get("message", "")
            )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (with timeout for heartbeat)
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0  # 30 second timeout
                )

                # Handle pong response
                if data.get("type") == "pong":
                    logger.debug(f"Received pong from job {job_id}")
                    continue

                # Handle other client messages (future extension)
                logger.debug(f"Received message from job {job_id}: {data}")

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await manager.send_ping(websocket)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally: job_id={job_id}, user_id={current_user.id}")
        manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
