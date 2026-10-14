from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Any, Dict, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.predictor import MLUnavailableError, ml_service
from app.submissions import save_text_submission

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "ml" / ".env", override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load the ML model once before taking incoming requests
    ml_service.load_model()
    yield
    # Shutdown: Clean up resources if necessary
    print("Shutting down server and releasing resources...")


app = FastAPI(
    title="ML Inference Backend",
    version="1.0.0",
    description="Backend API serving ML predictions to frontend client",
    lifespan=lifespan,
)

# Enable CORS for local frontend dev servers (Vite: 5173, Next/React: 3000)
DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:8443",
]
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", ",".join(DEFAULT_ORIGINS)).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    mode: Literal["github", "text"]
    query: str = Field(..., min_length=1, description="GitHub username or interest description")
    language: str | None = Field(default=None, max_length=80, description="Primary programming language for text requests")

    model_config = {
        "json_schema_extra": {
            "example": {
                "mode": "github",
                "query": "demo-alex-py"
            }
        }
    }


class RecommendResponse(BaseModel):
    status: str
    query: str
    mode: str
    user: Dict[str, Any]
    repos: list[Dict[str, Any]]


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    return {"status": "healthy"}


@app.post("/api/recommend", response_model=RecommendResponse, tags=["Inference"])
def recommend(payload: RecommendRequest) -> Dict[str, Any]:
    try:
        query = payload.query.strip()
        if payload.mode == "text":
            language = (payload.language or "").strip()
            if not language:
                raise HTTPException(status_code=422, detail="Please choose or enter a programming language.")
            save_text_submission(query, language)
            query = f"{language}. {query}"
        else:
            query = query.removeprefix("https://github.com/").removeprefix("http://github.com/").strip("/").lstrip("@")
        return ml_service.recommend(payload.mode, query)
    except HTTPException:
        raise
    except MLUnavailableError as exc:
        raise HTTPException(status_code=503, detail="ML dataset is not available. Run the data pipeline first.") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="GitHub demo user was not found.") from exc
    except (RuntimeError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SystemExit as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
