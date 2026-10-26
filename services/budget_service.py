from __future__ import annotations

from typing import Any

from utils.logger import AppLogger

logger = AppLogger("budget_service").get_logger()


class BudgetService:
    def calculate_budget(
        self,
        budget: float,
        travelers: int,
        days: int,
        style: str,
        currency: str = "INR",
    ) -> dict[str, Any]:
        cleaned_budget = float(budget or 0)
        if not cleaned_budget or cleaned_budget <= 0:
            cleaned_budget = 0.0

        style_key = (style or "standard").lower()
        style_weights = {
            "budget": {
                "hotel": 0.38,
                "food": 0.24,
                "transport": 0.14,
                "activities": 0.14,
                "contingency": 0.10,
            },
            "standard": {
                "hotel": 0.40,
                "food": 0.25,
                "transport": 0.15,
                "activities": 0.15,
                "contingency": 0.05,
            },
            "luxury": {
                "hotel": 0.45,
                "food": 0.22,
                "transport": 0.12,
                "activities": 0.15,
                "contingency": 0.06,
            },
        }
        weights = style_weights.get(style_key, style_weights["standard"])

        totals = {
            "hotel_cost": round(cleaned_budget * weights["hotel"], 2),
            "food_cost": round(cleaned_budget * weights["food"], 2),
            "transport_cost": round(cleaned_budget * weights["transport"], 2),
            "activity_cost": round(cleaned_budget * weights["activities"], 2),
            "misc_cost": round(cleaned_budget * weights["contingency"], 2),
        }

        total_estimated_cost = round(sum(totals.values()), 2)
        normalized_travelers = max(1, int(travelers or 1))
        per_traveler = {
            key: round(value / normalized_travelers, 2) for key, value in totals.items()
        }

        return {
            "currency": (currency or "INR").upper(),
            "group_budget": round(cleaned_budget, 2),
            "budget_per_traveler": round(cleaned_budget / normalized_travelers, 2),
            "hotel_cost": round(totals["hotel_cost"], 2),
            "food_cost": round(totals["food_cost"], 2),
            "transport_cost": round(totals["transport_cost"], 2),
            "activity_cost": round(totals["activity_cost"], 2),
            "misc_cost": round(totals["misc_cost"], 2),
            "hotel_cost_per_traveler": per_traveler["hotel_cost"],
            "food_cost_per_traveler": per_traveler["food_cost"],
            "transport_cost_per_traveler": per_traveler["transport_cost"],
            "activity_cost_per_traveler": per_traveler["activity_cost"],
            "misc_cost_per_traveler": per_traveler["misc_cost"],
            "total_estimated_cost": total_estimated_cost,
            "days": int(days or 1),
            "travelers": normalized_travelers,
            "style": style_key,
        }

    def calculate_route_budget(
        self,
        distance_km: float | None,
        mode: str = "driving",
        travelers: int = 1,
        travel_style: str = "standard",
        currency: str = "INR",
    ) -> dict[str, Any]:
        """Calculate detailed route travel budget including fuel, tolls, and highway refreshments."""
        dist = max(0.0, float(distance_km or 0.0))
        num_travelers = max(1, int(travelers or 1))
        style_key = (travel_style or "standard").lower()
        normalized_mode = (mode or "driving").lower()
        curr = (currency or "INR").upper()

        # Rates per km in INR
        fuel_rates = {"budget": 6.0, "standard": 7.5, "luxury": 11.0}
        toll_rates = {"budget": 1.6, "standard": 2.0, "luxury": 2.5}
        refreshment_per_head = {"budget": 150.0, "standard": 250.0, "luxury": 500.0}
        transit_per_km_head = {"budget": 1.2, "standard": 2.2, "luxury": 4.0}

        fuel_rate = fuel_rates.get(style_key, 7.5)
        toll_rate = toll_rates.get(style_key, 2.0)
        refreshment_rate = refreshment_per_head.get(style_key, 250.0)

        fuel_cost = 0.0
        toll_cost = 0.0
        transit_fare = 0.0
        refreshments = round(refreshment_rate * num_travelers, 2)

        if normalized_mode in {"driving", "standard", "best_available"}:
            fuel_cost = round(dist * fuel_rate, 2)
            toll_cost = round(dist * toll_rate, 2) if dist >= 25 else 0.0
            transit_fare = 0.0
        elif normalized_mode == "public_transport":
            fare_rate = transit_per_km_head.get(style_key, 2.2)
            transit_fare = round(dist * fare_rate * num_travelers, 2)
            fuel_cost = 0.0
            toll_cost = 0.0
        elif normalized_mode == "flight":
            base_flight = 3500.0 if style_key == "budget" else (5500.0 if style_key == "standard" else 9500.0)
            transit_fare = round(base_flight * num_travelers, 2)
            toll_cost = round(150.0 * num_travelers, 2)  # airport access/tolls
            fuel_cost = 0.0
        elif normalized_mode in {"walking", "cycling"}:
            refreshments = round(refreshment_rate * 0.75 * num_travelers, 2)
            fuel_cost = 0.0
            toll_cost = 0.0
            transit_fare = 0.0
        else:
            fuel_cost = round(dist * fuel_rate, 2)
            toll_cost = round(dist * toll_rate, 2) if dist >= 25 else 0.0

        total_one_way = round(fuel_cost + toll_cost + transit_fare + refreshments, 2)
        total_round_trip = round((fuel_cost * 2) + (toll_cost * 2) + (transit_fare * 2) + (refreshments * 2), 2)
        cost_per_traveler = round(total_one_way / num_travelers, 2)

        mode_label = normalized_mode.replace("_", " ").title()
        return {
            "currency": curr,
            "mode": normalized_mode,
            "mode_label": mode_label,
            "distance_km": round(dist, 1),
            "fuel_cost": fuel_cost,
            "toll_cost": toll_cost,
            "transit_fare": transit_fare,
            "highway_refreshments": refreshments,
            "total_one_way": total_one_way,
            "total_round_trip": total_round_trip,
            "cost_per_traveler": cost_per_traveler,
            "travelers": num_travelers,
            "travel_style": style_key,
            "notes": (
                f"Estimated {mode_label} travel budget for {dist:.1f} km: "
                f"Fuel: {curr} {fuel_cost:,.0f}, Tolls: {curr} {toll_cost:,.0f}, "
                f"Refreshments: {curr} {refreshments:,.0f}."
                if normalized_mode in {"driving", "best_available"}
                else f"Estimated {mode_label} travel budget for {dist:.1f} km: {curr} {total_one_way:,.0f} one-way."
            ),
        }
