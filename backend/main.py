"""
DevTeam AI - FastAPI Backend Entry Point
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.router import api_router

# Load environment variables
load_dotenv()

# Create FastAPI application
app = FastAPI(
    title="DevTeam AI API",
    description="Multi-Agent AI Software Development Platform",
    version="1.0.0",
)

# Configure CORS for React frontend
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "DevTeam AI API is running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    # Disable reload by default to prevent watchfiles from killing long-running background jobs
    reload_enabled = os.getenv("RELOAD", "false").lower() == "true"
    reload_excludes = (
        [".crewai_storage/*", "generated_projects/*", "*.db", "*.json", "*.log"]
        if reload_enabled
        else None
    )
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload_enabled,
        reload_excludes=reload_excludes,
    )

