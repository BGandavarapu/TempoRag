from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import dashboard, ingest, query, sources

app = FastAPI(title="Temporal RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
