from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from services.budget_service import BudgetService
from services.gemini_service import GeminiService
from services.location_service import LocationService
from services.weather_service import WeatherService


class GeminiPromptInput(BaseModel):
    prompt: str = Field(..., description="Prompt to send to the Gemini model")


class GeminiTool(BaseTool):
    name: str = "Gemini Prompt Tool"
    description: str = "Sends a prompt to Gemini and returns a formatted response"
    args_schema: type[BaseModel] = GeminiPromptInput

    def _run(self, prompt: str) -> str:
        return GeminiService().generate_content(prompt)


class WeatherTool(BaseTool):
    name: str = "Weather Tool"
    description: str = "Returns weather summary and travel suitability information"

    def _run(self, destination: str) -> dict[str, Any]:
        return WeatherService().get_weather_summary(destination)


class BudgetTool(BaseTool):
    name: str = "Budget Calculator Tool"
    description: str = "Calculates a travel budget breakdown"

    def _run(self, budget: float, travelers: int, days: int, style: str) -> dict[str, Any]:
        return BudgetService().calculate_budget(budget, travelers, days, style)


class LocationTool(BaseTool):
    name: str = "Location Information Tool"
    description: str = "Provides nearby attractions, transport options, and travel highlights"

    def _run(self, destination: str) -> dict[str, Any]:
        return LocationService().get_location_data(destination)
