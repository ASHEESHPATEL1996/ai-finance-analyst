import uvicorn
from fastapi import FastAPI
from api.middleware import register_middleware
from api.routes.analyst import router as analyst_router
from api.routes.portfolio import router as portfolio_router
from api.routes.sentiment import router as sentiment_router
from api.routes.assistant import router as assistant_router
from core.config import settings

app = FastAPI(
    title="Fintelligence AI",
    description="AI-powered investment research platform",
    version="1.0.0",
)

register_middleware(app)

app.include_router(analyst_router)
app.include_router(portfolio_router)
app.include_router(sentiment_router)
app.include_router(assistant_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "app": "Fintelligence AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )