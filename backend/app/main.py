from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)

app.include_router(api_router)


@app.get("/", tags=["Root"])
def root():

    return {
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health():

    return {
        "status": "healthy",
    }