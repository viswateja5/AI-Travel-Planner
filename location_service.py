from __future__ import annotations

from typing import Any


class LocationService:
    def get_location_data(self, destination: str) -> dict[str, Any]:
        return {
            "destination": destination,
            "nearby_attractions": ["Historic center", "Local market", "Scenic viewpoints"],
            "transportation_options": ["Metro", "Bus", "Taxi"],
            "local_highlights": ["Great food scene", "Walkable neighborhoods", "Cultural landmarks"],
        }
