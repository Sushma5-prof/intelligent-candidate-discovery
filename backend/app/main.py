import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import search
from app.services import state

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Intelligent Candidate Discovery API",
    description="Sub-2.5s semantic candidate ranking with trajectory-aware reranking.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    state.bootstrap()


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "embedding_backend": state.embedding_service.backend_name if state.embedding_service else None,
        "reranker_backend": state.reranker.backend_name if state.reranker else None,
        "candidates_indexed": True,
    }


app.include_router(search.router)
