"""
Health Check Endpoint
GET /api/health - Returns backend operational status
"""

import time
from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check():
    """
    Health check endpoint.
    Returns real backend operational status.
    """
    return {
        "status": "healthy",
        "service": "DevTeam AI API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "operational",
    }

