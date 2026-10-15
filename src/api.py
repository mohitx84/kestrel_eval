import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.predict import KestrelPredictor

# Global predictor instance
predictor: Optional[KestrelPredictor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global predictor
    try:
        predictor = KestrelPredictor()
    except Exception as e:
        print(f"Warning: Model could not be loaded at startup: {e}")
        predictor = None
    yield


# Initialize FastAPI App
app = FastAPI(
    title="Kestrel Service-Request Routing API",
    description="Local, privacy-preserving routing and explanation service for customer requests.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Schemas
class ServiceRequestInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "SR510823",
                "channel": "chat",
                "product_family": "Water Purifier",
                "warranty_status": "in_warranty",
                "request_text": "water purifier leaking from bottom after technician visit",
                "source": "crm",
            }
        }
    )

    request_id: Optional[str] = Field(
        default=None, description="Optional service request identifier (e.g., SR510823)"
    )
    channel: Optional[str] = Field(
        default="chat", description="Intake channel: chat, whatsapp, ivr, email"
    )
    product_family: Optional[str] = Field(
        default="Water Purifier", description="Product category for the request"
    )
    warranty_status: Optional[str] = Field(
        default="in_warranty",
        description="Warranty status: in_warranty, out_of_warranty, shield",
    )
    request_text: str = Field(
        ..., description="Customer opening message or IVR transcript"
    )
    source: Optional[str] = Field(
        default="crm", description="System source: crm or legacy_zoho"
    )


class RoutingPredictionResponse(BaseModel):
    request_id: Optional[str] = Field(default=None)
    predicted_team: str = Field(..., description="Target destination queue")
    confidence: float = Field(
        ..., description="Calibrated posterior model confidence (0.0 to 1.0)"
    )
    reasons: List[str] = Field(
        ..., description="Evidence-grounded explanations and policy notes"
    )
    review_recommended: bool = Field(
        ..., description="Flag indicating ambiguity or policy review requirement"
    )
    runner_up_team: Optional[str] = Field(
        default=None, description="Second highest probability queue"
    )
    runner_up_confidence: Optional[float] = Field(
        default=None, description="Probability of runner-up queue"
    )


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str
    available_classes: List[str]


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Returns the operational status and model readiness of the routing service."""
    global predictor
    if predictor is None:
        try:
            predictor = KestrelPredictor()
        except Exception:
            pass

    loaded = predictor is not None
    classes = predictor.classes_ if loaded else []
    return {
        "status": "healthy" if loaded else "degraded",
        "model_loaded": loaded,
        "version": "1.0.0",
        "available_classes": classes,
    }


@app.post(
    "/predict",
    response_model=RoutingPredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Routing"],
)
def predict_service_request(request: ServiceRequestInput):
    """
    Classifies a customer service request into a destination queue with
    calibrated confidence and explainable rationale.
    """
    global predictor
    if predictor is None:
        try:
            predictor = KestrelPredictor()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Routing model is currently unavailable. Please verify model artifacts.",
            )

    try:
        req_dict = request.model_dump()
        result = predictor.predict_one(req_dict)
        return result
    except Exception as e:
        # Avoid logging customer text or leaking internal exceptions
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process service request. Please check input parameters.",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="127.0.0.1", port=8000, reload=False)
