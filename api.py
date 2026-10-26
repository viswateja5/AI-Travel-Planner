from pathlib import Path
from threading import Lock
from typing import Literal
import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config import OUTPUTS_DIR, get_gemini_diagnostic
from crew.crew import TravelPlannerCrew
from services.gemini_service import GeminiProviderError
from services.maps_service import MapsService

app = FastAPI(
    title="AI Travel Planner API",
    description="Generate personalized travel plans using AI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

generation_lock = Lock()


class TripRequest(BaseModel):
    start: str = Field(default="", max_length=150)
    destination: str = Field(min_length=1, max_length=150)
    days: int = Field(default=3, ge=1, le=30)
    budget: float = Field(default=1200.0, gt=0, le=10_000_000)
    travelers: int = Field(default=2, ge=1, le=50)
    travel_style: Literal["budget", "standard", "luxury"] = "standard"
    travel_mode: Literal["driving", "public_transport", "walking", "cycling", "flight", "best_available"] = "best_available"
    currency: Literal["INR"] = "INR"
    preferences: str = Field(default="balanced", max_length=1000)


@app.get("/")
def home():
    return {
        "message": "AI Travel Planner API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    diagnostic = get_gemini_diagnostic()
    return {
        "status": "healthy",
        "service": "AI Travel Planner API",
        "gemini_api_key_configured": diagnostic["gemini_api_key_configured"],
    }


@app.post("/api/trips/generate")
def generate_trip(request: TripRequest):
    destination = request.destination.strip()

    if not destination:
        raise HTTPException(status_code=422, detail="Destination cannot be empty.")

    trip_inputs = {
        "start": request.start.strip(),
        "destination": destination,
        "days": request.days,
        "budget": request.budget,
        "travelers": request.travelers,
        "travel_style": request.travel_style,
        "travel_mode": request.travel_mode,
        "currency": request.currency,
        "preferences": request.preferences.strip() or "balanced",
    }

    try:
        with generation_lock:
            result = TravelPlannerCrew().run(trip_inputs)

        if not result.get("result", "").strip():
            raise HTTPException(status_code=500, detail="Travel plan generation returned an empty response.")

        return {
            "success": True,
            "destination": destination,
            "trip": trip_inputs,
            "result": result.get("result", ""),
            "ai_source": result.get("ai_source") or "gemini_live",
            "warnings": result.get("warnings", []),
            "markdown_available": bool(result.get("markdown_path")),
            "pdf_available": bool(result.get("pdf_path")),
            "pdf_url": "/api/reports/pdf",
            "markdown_url": "/api/reports/markdown",
            "markdown_content": result.get("markdown_content", ""),
            "budget_breakdown": result.get("budget_breakdown"),
            "route_context": result.get("route_context"),
            "route_data": result.get("route_data"),
        }
    except GeminiProviderError as exc:
        raise HTTPException(status_code=exc.api_status_code, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logging.getLogger(__name__).exception("Travel plan generation failed")
        raise HTTPException(
            status_code=500,
            detail="Travel plan generation failed. Check the backend logs.",
        )


@app.get("/api/routes")
def get_route(
    start: str = Query(..., min_length=1, max_length=150),
    destination: str = Query(..., min_length=1, max_length=150),
    mode: str = Query("driving", pattern="^(driving|walking|cycling|public_transport|flight|best_available)$"),
    travelers: int = Query(2, ge=1, le=50),
    travel_style: str = Query("standard"),
):
    route_data = MapsService().get_route_details(
        start=start,
        destination=destination,
        mode=mode,
        travelers=travelers,
        travel_style=travel_style,
    )
    return {
        "status": route_data.get("status", "unavailable"),
        "start": route_data.get("start"),
        "destination": route_data.get("destination"),
        "mode": route_data.get("mode", mode),
        "distance_km": route_data.get("distance_km"),
        "duration_minutes": route_data.get("duration_minutes"),
        "geometry": route_data.get("geometry"),
        "directions": route_data.get("directions", []),
        "route_budget": route_data.get("route_budget", {}),
        "en_route_places": route_data.get("en_route_places", []),
        "destination_places": route_data.get("destination_places", []),
        "stops": route_data.get("stops", []),
        "summary": route_data.get("summary", "Route data is unavailable."),
    }


@app.get("/api/places/nearby")
def get_nearby_places(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius: int = Query(20000, ge=500, le=50000),
):
    places = MapsService().get_nearby_places(latitude, longitude, radius=radius)
    return {"status": "success" if places else "unavailable", "places": places, "count": len(places)}


@app.get("/api/reports/pdf")
def download_pdf():
    pdf_path = Path(OUTPUTS_DIR) / "travel_plan.pdf"

    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="No PDF report found.")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename="travel_plan.pdf",
    )


@app.get("/api/reports/markdown")
def get_markdown():
    markdown_path = Path(OUTPUTS_DIR) / "travel_plan.md"

    if not markdown_path.is_file():
        raise HTTPException(status_code=404, detail="No Markdown report found.")

    return {"content": markdown_path.read_text(encoding="utf-8")}
