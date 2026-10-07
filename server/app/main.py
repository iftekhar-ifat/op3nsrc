from contextlib import asynccontextmanager
from typing import Any, Dict, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.predictor import MLUnavailableError, ml_service


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
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8443",
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
        return ml_service.recommend(payload.mode, payload.query.strip().lstrip("@"))
    except MLUnavailableError as exc:
        raise HTTPException(status_code=503, detail="ML dataset is not available. Run the data pipeline first.") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="GitHub demo user was not found.") from exc
    except (RuntimeError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc