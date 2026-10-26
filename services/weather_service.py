from __future__ import annotations

import os
import time
from typing import Any

import requests

from utils.logger import AppLogger

logger = AppLogger("weather_service").get_logger()


class WeatherService:
    def __init__(self) -> None:
        self.provider = os.getenv("WEATHER_API_PROVIDER", "open-meteo").lower()
        self.base_url = os.getenv("WEATHER_API_BASE_URL", "https://api.open-meteo.com/v1/forecast")
        self._cache: dict[str, dict[str, Any]] = {}

    def get_weather_summary(self, destination: str) -> dict[str, Any]:
        normalized_destination = (destination or "").strip()
        if not normalized_destination:
            return self._fallback_weather("Destination")

        cache_key = normalized_destination.lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.provider in {"open-meteo", "openmeteo", "meteo"}:
            result = self._get_open_meteo_weather(normalized_destination)
            self._cache[cache_key] = result
            return result

        result = self._fallback_weather(normalized_destination)
        self._cache[cache_key] = result
        return result

    def _get_open_meteo_weather(self, destination: str) -> dict[str, Any]:
        retries = 2
        for attempt in range(retries + 1):
            try:
                geocode_response = requests.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"format": "jsonv2", "limit": 1, "q": destination},
                    headers={
                        "User-Agent": "AITravelPlanner/1.0 (+https://example.com)",
                        "Accept": "application/json",
                    },
                    timeout=(5, 15),
                )
                geocode_response.raise_for_status()
                geodata = geocode_response.json()
                if not isinstance(geodata, list) or not geodata:
                    raise ValueError("No geocoded location found for the destination.")

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
                    headers={
                        "User-Agent": "AITravelPlanner/1.0 (+https://example.com)",
                        "Accept": "application/json",
                    },
                    timeout=(5, 20),
                )
                if response.status_code in {429, 500, 502, 503, 504} and attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                response.raise_for_status()
                data = response.json()
                current = data.get("current")
                if not isinstance(current, dict):
                    raise ValueError("Weather API response did not include current conditions.")

                temperature = current.get("temperature_2m")
                weather_code = current.get("weathercode")
                normalized_temp = temperature
                if not isinstance(normalized_temp, (int, float)) or not __import__("math").isfinite(float(normalized_temp)):
                    normalized_temp = None
                return {
                    "destination": destination,
                    "summary": self._weather_code_to_text(weather_code),
                    "temperature_celsius": normalized_temp,
                    "forecast": f"Weather code {weather_code} at {destination}.",
                    "travel_suitability": self._suitability_label(normalized_temp),
                    "source": "open-meteo",
                }
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                logger.warning("Open-Meteo weather request failed for %s (attempt %s/%s): %s", destination, attempt + 1, retries + 1, exc)
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
            except requests.exceptions.HTTPError as exc:
                logger.warning("Open-Meteo HTTP error for %s: %s", destination, exc)
                if getattr(exc.response, "status_code", None) in {429, 500, 502, 503, 504} and attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                break
            except Exception as exc:  # pragma: no cover
                logger.warning("Open-Meteo weather lookup failed for %s: %s", destination, exc)
                break

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
            "source": "unavailable",
        }

    def _suitability_label(self, temp: Any) -> str:
        if isinstance(temp, (int, float)):
            if temp >= 25:
                return "Great for outdoor plans"
            if temp >= 15:
                return "Good for most activities"
            return "Cooler conditions, pack layers"
        return "Check locally"
