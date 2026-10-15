from __future__ import annotations

import os
from typing import Any

import requests

from utils.logger import AppLogger

logger = AppLogger("weather_service").get_logger()


class WeatherService:
    def __init__(self) -> None:
        self.provider = os.getenv("WEATHER_API_PROVIDER", "open-meteo").lower()
        self.base_url = os.getenv("WEATHER_API_BASE_URL", "https://api.open-meteo.com/v1/forecast")

    def get_weather_summary(self, destination: str) -> dict[str, Any]:
        if self.provider in {"open-meteo", "openmeteo", "meteo"}:
            return self._get_open_meteo_weather(destination)

        return self._fallback_weather(destination)

    def _get_open_meteo_weather(self, destination: str) -> dict[str, Any]:
        try:
            geocode_response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"format": "jsonv2", "limit": 1, "q": destination},
                headers={"User-Agent": "AgentTripPlanner/1.0"},
                timeout=10,
            )
            geocode_response.raise_for_status()
            geodata = geocode_response.json()
            if not geodata:
                raise ValueError("No geocoded location found")

            lat = geodata[0]["lat"]
            lon = geodata[0]["lon"]
            response = requests.get(
                self.base_url,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,weathercode",
                    "timezone": "auto",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            current = data.get("current", {})
            temperature = current.get("temperature_2m")
            weather_code = current.get("weathercode")
            return {
                "destination": destination,
                "summary": self._weather_code_to_text(weather_code),
                "temperature_celsius": temperature,
                "forecast": f"Weather code {weather_code} at {destination}.",
                "travel_suitability": self._suitability_label(temperature),
            }
        except Exception as exc:  # pragma: no cover
            logger.warning("Open-Meteo weather lookup failed for %s: %s", destination, exc)
            return self._fallback_weather(destination)

    def _weather_code_to_text(self, weather_code: Any) -> str:
        mapping = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            95: "Thunderstorm",
        }
        return mapping.get(weather_code, "Weather information unavailable")

    def _fallback_weather(self, destination: str) -> dict[str, Any]:
        return {
            "destination": destination,
            "summary": f"Weather data is currently unavailable for {destination}.",
            "temperature_celsius": None,
            "forecast": "Please verify local seasonal conditions before you depart.",
            "travel_suitability": "Check locally",
        }

    def _suitability_label(self, temp: Any) -> str:
        if isinstance(temp, (int, float)):
            if temp >= 25:
                return "Great for outdoor plans"
            if temp >= 15:
                return "Good for most activities"
            return "Cooler conditions, pack layers"
        return "Check locally"
