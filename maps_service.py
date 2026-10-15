from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from utils.logger import AppLogger

logger = AppLogger("maps_service").get_logger()


class MapsService:
    def __init__(self) -> None:
        self.geocode_url = "https://nominatim.openstreetmap.org/search"
        self.overpass_url = "https://overpass-api.de/api/interpreter"

    def get_map_context(self, destination: str) -> dict[str, Any]:
        location = self.geocode(destination)
        if not location:
            return {
                "destination": destination,
                "coordinates": {},
                "nearby_places": ["Historic center", "Local market", "Scenic viewpoint"],
                "map_links": {
                    "openstreetmap": f"https://www.openstreetmap.org/search?query={quote(destination)}",
                },
            }

        lat = location["lat"]
        lon = location["lon"]
        nearby_places = self._fetch_nearby_places(lat, lon)
        return {
            "destination": destination,
            "coordinates": {"lat": lat, "lon": lon},
            "nearby_places": nearby_places,
            "map_links": {
                "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=14/{lat}/{lon}",
            },
            "display_name": location.get("display_name", destination),
        }

    def geocode(self, destination: str) -> dict[str, Any] | None:
        params = {"format": "jsonv2", "limit": 1, "q": destination}
        try:
            response = requests.get(
                self.geocode_url,
                params=params,
                headers={"User-Agent": "travel-planner/1.0"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as exc:  # pragma: no cover
            logger.warning("Geocoding failed for %s: %s", destination, exc)
        return None

    def _fetch_nearby_places(self, lat: float, lon: float) -> list[str]:
        query = f"""
        [out:json][timeout:25];
        (
          node(around:2000,{lat},{lon})[tourism~"museum|attraction|viewpoint|gallery"];
          way(around:2000,{lat},{lon})[tourism~"museum|attraction|viewpoint|gallery"];
          relation(around:2000,{lat},{lon})[tourism~"museum|attraction|viewpoint|gallery"];
        );
        out body;
        """
        try:
            response = requests.post(self.overpass_url, data={"data": query}, timeout=20)
            response.raise_for_status()
            elements = response.json().get("elements", [])
            places = []
            for item in elements[:6]:
                name = item.get("tags", {}).get("name")
                if name and name not in places:
                    places.append(name)
            return places or ["Historic center", "Local market", "Scenic viewpoint"]
        except Exception as exc:  # pragma: no cover
            logger.warning("Nearby place lookup failed: %s", exc)
            return ["Historic center", "Local market", "Scenic viewpoint"]
