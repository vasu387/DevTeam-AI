"""
API Router - Aggregates all API endpoints
"""

from fastapi import APIRouter
from api.endpoints import health, projects

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])

