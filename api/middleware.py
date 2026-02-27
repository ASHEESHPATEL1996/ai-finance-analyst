from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error on {request.method} {request.url}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "An unexpected server error occurred. Please try again.",
                "detail": str(exc),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning(f"Validation error on {request.method} {request.url}: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(exc),
            },
        )