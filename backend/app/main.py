from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)


app.include_router(api_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)