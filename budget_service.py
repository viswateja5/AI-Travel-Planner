from __future__ import annotations

from typing import Any

from utils.logger import AppLogger

logger = AppLogger("budget_service").get_logger()


class BudgetService:
    def calculate_budget(self, budget: float, travelers: int, days: int, style: str) -> dict[str, Any]:
        multiplier = {"budget": 0.85, "standard": 1.0, "luxury": 1.35}.get(style.lower(), 1.0)
        hotel = budget * 0.4 * multiplier
        food = budget * 0.25 * multiplier
        transport = budget * 0.15 * multiplier
        activities = budget * 0.15 * multiplier
        misc = budget * 0.05 * multiplier

        total = hotel + food + transport + activities + misc
        return {
            "hotel_cost": round(hotel / travelers, 2),
            "food_cost": round(food / travelers, 2),
            "transport_cost": round(transport / travelers, 2),
            "activity_cost": round(activities / travelers, 2),
            "misc_cost": round(misc / travelers, 2),
            "total_estimated_cost": round(total / travelers, 2),
            "days": days,
            "travelers": travelers,
            "style": style,
        }
