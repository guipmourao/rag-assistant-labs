from app.api.v1.endpoints import documents, health
from app.core.security import require_api_key
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"],
    dependencies=[require_api_key],
)
