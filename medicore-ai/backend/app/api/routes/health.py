from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "service": "MEDICORE AI Backend",
        "version": "2.0.0"
    }

@router.get("/ready")
async def readiness_check():
    return {
        "ready": True,
        "message": "All services initialized"
    }
