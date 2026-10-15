from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config import ENABLE_TRIP_HISTORY
from crew.crew import TravelPlannerCrew
from database.database import TripHistoryStore
from utils.logger import AppLogger

logger = AppLogger("main").get_logger()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a travel plan using CrewAI agents.")
    parser.add_argument("--start", default="", help="Starting point city or country")
    parser.add_argument("--destination", required=True, help="Destination city or country")
    parser.add_argument("--days", type=int, default=3, help="Number of days")
    parser.add_argument("--budget", type=float, default=1200.0, help="Estimated trip budget")
    parser.add_argument("--travelers", type=int, default=2, help="Number of travelers")
    parser.add_argument("--travel-style", default="standard", choices=["budget", "standard", "luxury"], help="Travel style")
    parser.add_argument("--preferences", default="balanced", help="Travel preferences")
    return parser.parse_args()


def prompt_for_missing_value(prompt_text: str) -> str:
    value = input(prompt_text).strip()
    return value


def main() -> None:
    args = parse_args()

    if not args.destination.strip():
        logger.error("Destination is required")
        sys.exit(1)

    start_point = args.start.strip()
    if not start_point:
        start_point = prompt_for_missing_value("Starting point (leave blank to skip): ")

    trip_inputs = {
        "start": start_point,
        "destination": args.destination,
        "days": args.days,
        "budget": args.budget,
        "travelers": args.travelers,
        "travel_style": args.travel_style,
        "preferences": args.preferences,
    }

    try:
        crew = TravelPlannerCrew()
        result = crew.run(trip_inputs)
        if ENABLE_TRIP_HISTORY:
            store = TripHistoryStore()
            store.save_trip(args.destination, args.budget, args.travelers, result["markdown_path"])
        print("Travel plan generated successfully.")
        print(f"Markdown report: {result['markdown_path']}")
        print(f"PDF report: {result['pdf_path']}")
    except Exception as exc:  # pragma: no cover
        logger.exception("Travel planning failed: %s", exc)
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
