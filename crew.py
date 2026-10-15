from __future__ import annotations

from typing import Any

from services.budget_service import BudgetService
from services.deepseek_service import DeepSeekService
from services.location_service import LocationService
from services.maps_service import MapsService
from services.markdown_service import MarkdownService
from services.pdf_service import PdfService
from services.weather_service import WeatherService
from utils.logger import AppLogger

logger = AppLogger("crew").get_logger()


class TravelPlannerCrew:
    def __init__(self) -> None:
        self.markdown_service = MarkdownService()
        self.pdf_service = PdfService()

    def run(self, trip_inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info("Starting DeepSeek-based planning flow for destination %s", trip_inputs.get("destination"))
        result = self._build_offline_result(trip_inputs)

        markdown_content = self._build_markdown_report(result, trip_inputs)
        markdown_path = self.markdown_service.write_report(markdown_content)
        pdf_path = self.pdf_service.generate_pdf(markdown_content)
        return {
            "result": str(result),
            "markdown_path": str(markdown_path),
            "pdf_path": str(pdf_path),
        }

    def _build_offline_result(self, trip_inputs: dict[str, Any]) -> str:
        destination = trip_inputs.get("destination", "Unknown Destination")
        start = trip_inputs.get("start", "").strip() or "Your current location"
        days = trip_inputs.get("days", 3)
        style = trip_inputs.get("travel_style", "standard")
        budget = trip_inputs.get("budget", 1000)
        travelers = trip_inputs.get("travelers", 2)
        preferences = trip_inputs.get("preferences", "Balanced")

        weather = WeatherService().get_weather_summary(destination)
        budget_breakdown = BudgetService().calculate_budget(float(budget), int(travelers), int(days), style)
        location_data = LocationService().get_location_data(destination)
        map_context = MapsService().get_map_context(destination)
        deepseek = DeepSeekService().generate_content(
            f"Create a concise travel plan for {destination} for {days} days with {travelers} travelers and preferences {preferences}."
        )

        return f"""Itinerary: Balance sightseeing, local cuisine, and rest across {days} days.\nRoute: Start from {start} and travel to {destination}.\nResearch: {destination} offers {', '.join(location_data['nearby_attractions'])}.\nBudget: Hotel {budget_breakdown['hotel_cost']}, food {budget_breakdown['food_cost']}, transport {budget_breakdown['transport_cost']}, activities {budget_breakdown['activity_cost']}.\nLive weather: {weather['summary']}\nLive maps: {map_context['map_links']['openstreetmap']}\nAdvisor: {deepseek}"""

    def _build_markdown_report(self, result: Any, trip_inputs: dict[str, Any]) -> str:
        destination = trip_inputs.get("destination", "Unknown Destination")
        start = trip_inputs.get("start", "").strip() or "Your current location"
        days = trip_inputs.get("days", 3)
        budget = trip_inputs.get("budget", 1000)
        travelers = trip_inputs.get("travelers", 2)
        style = trip_inputs.get("travel_style", "standard")
        preferences = trip_inputs.get("preferences", "Balanced")

        return f"""# Travel Plan Report

## Executive Summary
A thoughtfully curated {style.lower()} travel plan for {destination} for {days} days, designed for {travelers} traveler(s) with a budget of {budget} and preferences focused on {preferences}.

## Destination Overview
- Start Point: {start}
- Destination: {destination}
- Duration: {days} days
- Travelers: {travelers}
- Budget: {budget}
- Travel Style: {style}
- Preferences: {preferences}

## Day-wise Itinerary
- Day 1: Arrive, explore the historic center, enjoy local cuisine, and relax at a scenic viewpoint.
- Day 2: Visit major attractions, use local transport, and experience the food scene.
- Day 3: Enjoy a flexible day with shopping, neighborhood walks, and optional add-ons.

## Hotel Recommendations
- Boutique stay in the city center for convenience.
- Mid-range option near public transit for better value.
- Premium property with local amenities for a luxury-style experience.

## Restaurant Recommendations
- Casual local bistro for breakfast and coffee.
- Traditional restaurant for lunch and regional specialties.
- Upscale dinner spot for a celebratory evening.

## Tourist Attractions
- Nearby map-based attractions: {', '.join(MapsService().get_map_context(destination)['nearby_places'])}
- Suggested route: use the map links in the report to inspect specific stops
- Local highlights: {', '.join(LocationService().get_location_data(destination)['local_highlights'])}

## Transportation Guide
- Use public transit for city exploration.
- Reserve airport transfers in advance.
- Keep cash and cards ready for local rides.

## Budget Breakdown
- Accommodation: {budget * 0.35:.0f}
- Food: {budget * 0.25:.0f}
- Transportation: {budget * 0.15:.0f}
- Activities: {budget * 0.15:.0f}
- Miscellaneous: {budget * 0.10:.0f}

## Packing Checklist
- Comfortable walking shoes
- Lightweight clothing layers
- Adapter and chargers
- Travel documents
- Sun protection and water bottle

## Weather Information
- Current weather summary: {WeatherService().get_weather_summary(destination)['summary']}
- Temperature: {WeatherService().get_weather_summary(destination)['temperature_celsius'] if WeatherService().get_weather_summary(destination)['temperature_celsius'] is not None else 'Unavailable'}°C
- Suitability: {WeatherService().get_weather_summary(destination)['travel_suitability']}

## Safety Tips
- Keep valuables secure.
- Follow local guidance and avoid isolated areas at night.
- Save emergency contacts on your phone.

## Emergency Contacts
- Local emergency services: 112
- Embassy or consulate help desk
- Hotel reception desk

## Local Customs
- Respect local dress codes.
- Greet people politely.
- Ask before photographing people or private spaces.

## Travel Recommendations
- Book early for popular attractions.
- Reserve dining and airport transfers where possible.
- Stay flexible and leave room for spontaneous discoveries.

## Crew Output
{result}
"""
