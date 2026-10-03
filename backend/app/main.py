from fastapi import FastAPI

from app.api.router import api_router

from app.core.config import settings
from app.core.handlers import register_exception_handlers
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=(
        "AI Agent Platform for Small Businesses."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

#---------------------------------------------------------
# Middleware
#---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------

register_exception_handlers(
    app,
)


# ---------------------------------------------------------
# API Routes
# ---------------------------------------------------------

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


# ---------------------------------------------------------
# System
# ---------------------------------------------------------

@app.get(
    "/",
    tags=["System"],
)
def root():

    return {
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "running",
    }



@app.get(
    "/health",
    tags=["System"],
)
def health():

    return {
        "status": "ok",
    }