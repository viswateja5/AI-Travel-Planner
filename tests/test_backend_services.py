import json
import os
import unittest
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api import app
from config import ENV_PATH, get_gemini_diagnostic, load_project_env
from crew.crew import TravelPlannerCrew
from services.budget_service import BudgetService
from services.gemini_service import GeminiProviderError, GeminiService
from services.maps_service import MapsService
from services.weather_service import WeatherService
from utils.helpers import format_currency


class GeminiServiceTests(unittest.TestCase):
    def test_missing_api_key_raises_clear_error(self):
        service = GeminiService(api_key="")
        with self.assertRaisesRegex(ValueError, "GEMINI_API_KEY"):
            service.generate_content("Create an itinerary for Mysore")

    @patch("services.gemini_service.request.urlopen")
    def test_successful_response_parsing_uses_gemini_content(self, mock_urlopen):
        mock_response = Mock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        mock_response.read.return_value = b'{"candidates": [{"content": {"parts": [{"text": "Gemini-generated Mysore itinerary."}]}}]}'
        mock_urlopen.return_value = mock_response

        service = GeminiService(api_key="test-key", model="gemini-3.8-flash")
        result = service.generate_content("Create an itinerary for Mysore")

        self.assertEqual(result, "Gemini-generated Mysore itinerary.")
        request_arg = mock_urlopen.call_args.args[0]
        self.assertEqual(
            request_arg.full_url,
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
        )
        self.assertEqual(request_arg.get_header("X-goog-api-key"), "test-key")
        self.assertNotIn("test-key", request_arg.full_url)
        self.assertEqual(
            json.loads(request_arg.data),
            {
                "contents": [{"parts": [{"text": "Create an itinerary for Mysore"}]}],
                "generationConfig": {"maxOutputTokens": 1024},
            },
        )

    @patch("services.gemini_service.request.urlopen")
    def test_400_provider_body_is_logged_safely_and_mapped_to_gateway_error(self, mock_urlopen):
        prompt = "Private travel details for Mysore"
        mock_urlopen.side_effect = HTTPError(
            "https://generativelanguage.googleapis.com/",
            400,
            "Bad Request",
            {},
            BytesIO(
                json.dumps(
                    {
                        "error": {
                            "code": 400,
                            "status": "INVALID_ARGUMENT",
                            "message": (
                                "Invalid request for Private travel details for Mysore; "
                                "x-goog-api-key=test-secret-key"
                            ),
                        }
                    }
                ).encode("utf-8")
            ),
        )
        service = GeminiService(api_key="test-secret-key", model="gemini-3.8-flash")

        with self.assertLogs("gemini_service", level="ERROR") as captured:
            with self.assertRaises(GeminiProviderError) as raised:
                service.generate_content(prompt)

        self.assertEqual(raised.exception.api_status_code, 502)
        self.assertIn("Gemini rejected the generation request", str(raised.exception))
        log_output = "\n".join(captured.output)
        self.assertIn('"status": "INVALID_ARGUMENT"', log_output)
        self.assertIn("Invalid request for [PROMPT REDACTED]", log_output)
        self.assertNotIn("test-secret-key", log_output)
        self.assertNotIn(prompt, log_output)

    @patch("services.gemini_service.request.urlopen")
    def test_404_is_mapped_and_logged_without_secrets_or_prompt(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            "https://generativelanguage.googleapis.com/",
            404,
            "Not Found",
            {},
            None,
        )
        service = GeminiService(api_key="test-secret-key", model="gemini-3.8-flash")

        with self.assertLogs("gemini_service", level="ERROR") as captured:
            with self.assertRaisesRegex(ValueError, "model is unavailable"):
                service.generate_content("Private travel details for Mysore")

        log_output = "\n".join(captured.output)
        self.assertIn("exception_class=HTTPError", log_output)
        self.assertIn("http_status=404", log_output)
        self.assertIn("model=gemini-3.8-flash", log_output)
        self.assertIn("api_key_present=True", log_output)
        self.assertNotIn("test-secret-key", log_output)
        self.assertNotIn("Private travel details", log_output)

    def test_empty_explicit_api_key_does_not_fall_back_to_environment(self):
        service = GeminiService(api_key="", model="gemini-3.8-flash")

        self.assertFalse(service.is_configured)
        with self.assertRaisesRegex(ValueError, "GEMINI_API_KEY"):
            service.generate_content("Create an itinerary")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-3.8-flash"}, clear=False)
    @patch("crew.crew.MapsService.get_route_context")
    @patch("crew.crew.MapsService.get_map_context")
    @patch("crew.crew.LocationService.get_location_data")
    @patch("crew.crew.WeatherService.get_weather_summary")
    @patch("crew.crew.GeminiService.generate_content")
    def test_gemini_is_used_for_itinerary_generation(
        self,
        mock_gemini,
        mock_weather,
        mock_location,
        mock_map_context,
        mock_route_context,
    ):
        mock_weather.return_value = {
            "summary": "Weather data is currently unavailable for Mysore.",
            "temperature_celsius": None,
            "travel_suitability": "Check locally",
            "source": "unavailable",
        }
        mock_location.return_value = {"local_highlights": ["Mysore Palace", "Chamundi Hills", "Devaraja Market"]}
        mock_map_context.return_value = {
            "nearby_places": ["Mysore Palace", "Chamundi Hills", "Devaraja Market"],
            "map_links": {"openstreetmap": "https://example.com/map"},
        }
        mock_route_context.return_value = {
            "status": "unavailable",
            "summary": "Route data is unavailable; recommendations remain advisory.",
        }
        mock_gemini.return_value = "Gemini-generated Mysore day plan with palace, market, and hills."

        result = TravelPlannerCrew().run(
            {
                "start": "Bangalore",
                "destination": "Mysore",
                "days": 2,
                "travelers": 2,
                "budget": 10000,
                "travel_style": "standard",
                "currency": "INR",
                "preferences": "heritage and food",
            }
        )

        self.assertEqual(result["ai_source"], "gemini_live")
        self.assertIn("Gemini-generated", result["result"])
        self.assertIn("Mysore Palace", result["result"])

    def test_no_legacy_ai_provider_references_remain_in_active_code(self):
        files_to_scan = [
            Path("config.py"),
            Path("crew/crew.py"),
            Path("services/gemini_service.py"),
            Path("api.py"),
            Path("main.py"),
        ]
        for file_path in files_to_scan:
            content = file_path.read_text(encoding="utf-8")
            self.assertNotIn("DeepSeek", content)
            self.assertNotIn("DEEPSEEK_API_KEY", content)
            self.assertNotIn("DEEPSEEK_BASE_URL", content)
            self.assertNotIn("DEEPSEEK_MODEL", content)


class EnvironmentConfigTests(unittest.TestCase):
    def test_project_root_env_is_loaded_from_backend_root_and_reports_status_safely(self):
        env_path = load_project_env()

        self.assertTrue(env_path.is_absolute())
        self.assertEqual(env_path.parent, Path(__file__).resolve().parents[1])
        self.assertNotEqual(str(env_path), str(Path(__file__).resolve().parents[1] / "frontend" / ".env"))

        status = get_gemini_diagnostic()
        self.assertIn("gemini_api_key_configured", status)
        self.assertIsInstance(status["gemini_api_key_configured"], bool)
        self.assertIn("gemini_model", status)
        self.assertIn("env_file", status)
        self.assertNotIn("AIz", str(status))


class BudgetServiceTests(unittest.TestCase):
    def test_total_budget_is_group_budget_and_inr(self):
        budget = BudgetService().calculate_budget(10000, 2, 2, "standard", currency="INR")
        self.assertEqual(budget["currency"], "INR")
        self.assertEqual(budget["group_budget"], 10000.0)
        self.assertEqual(budget["budget_per_traveler"], 5000.0)
        self.assertEqual(budget["total_estimated_cost"], 10000.0)

    def test_inr_formatting_uses_rupee_symbol(self):
        self.assertEqual(format_currency(10000, "INR"), "₹10,000")
        self.assertEqual(format_currency(150000, "INR"), "₹1,50,000")

    def test_calculate_route_budget_driving(self):
        service = BudgetService()
        route_budget = service.calculate_route_budget(distance_km=140.0, mode="driving", travelers=2, travel_style="standard")
        self.assertEqual(route_budget["currency"], "INR")
        self.assertEqual(route_budget["distance_km"], 140.0)
        self.assertGreater(route_budget["fuel_cost"], 0)
        self.assertGreater(route_budget["toll_cost"], 0)
        self.assertGreater(route_budget["highway_refreshments"], 0)
        self.assertEqual(
            route_budget["total_one_way"],
            round(route_budget["fuel_cost"] + route_budget["toll_cost"] + route_budget["highway_refreshments"], 2),
        )
        self.assertEqual(route_budget["total_round_trip"], round(route_budget["total_one_way"] * 2, 2))
        self.assertEqual(route_budget["cost_per_traveler"], round(route_budget["total_one_way"] / 2, 2))

    def test_calculate_route_budget_public_transport(self):
        service = BudgetService()
        route_budget = service.calculate_route_budget(distance_km=140.0, mode="public_transport", travelers=2, travel_style="standard")
        self.assertEqual(route_budget["fuel_cost"], 0.0)
        self.assertEqual(route_budget["toll_cost"], 0.0)
        self.assertGreater(route_budget["transit_fare"], 0)
        self.assertGreater(route_budget["total_one_way"], 0)


class MapsServiceTests(unittest.TestCase):
    @patch("services.maps_service.requests.post")
    def test_overpass_request_includes_headers_and_falls_back_on_error(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("406 Client Error")
        mock_post.return_value = mock_response

        service = MapsService()
        result = service._fetch_nearby_places(48.8566, 2.3522)

        self.assertEqual(result, ["Historic center", "Local market", "Scenic viewpoint"])
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://overpass-api.de/api/interpreter")
        self.assertIn("User-Agent", kwargs["headers"])
        self.assertIn("Accept", kwargs["headers"])
        self.assertIn("data", kwargs)

    @patch("services.maps_service.requests.get")
    def test_route_context_handles_missing_data_without_crashing(self, mock_get):
        mock_get.side_effect = Exception("Route unavailable")
        result = MapsService().get_route_context("Bangalore", "Mysore")
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("Route data is unavailable", result["summary"])

    @patch.object(MapsService, "geocode")
    @patch.object(MapsService, "get_nearby_places")
    def test_route_details_includes_accurate_directions_budget_and_enroute_places(self, mock_nearby, mock_geocode):
        mock_geocode.side_effect = lambda query: {
            "lat": "12.9716",
            "lon": "77.5946",
            "display_name": "Bangalore, Karnataka, India",
            "address": {"country": "India"},
        } if "bangalore" in query.lower() else {
            "lat": "12.2958",
            "lon": "76.6394",
            "display_name": "Mysore, Karnataka, India",
            "address": {"country": "India"},
        }
        mock_nearby.return_value = [
            {"id": "p1", "name": "Mysore Palace", "category": "Palace", "description": "Royal palace", "coordinates": [12.3052, 76.6552], "location": "Mysore"}
        ]

        service = MapsService()
        result = service.get_route_details("Bangalore", "Mysore", mode="driving", travelers=2, travel_style="standard")

        self.assertIn("directions", result)
        self.assertGreaterEqual(len(result["directions"]), 3)
        self.assertIn("route_budget", result)
        self.assertGreater(result["route_budget"]["fuel_cost"], 0)
        self.assertIn("en_route_places", result)
        en_route_names = [p["name"] for p in result["en_route_places"]]
        self.assertTrue(any("Ramanagara" in name for name in en_route_names))
        self.assertTrue(any("Channapatna" in name for name in en_route_names))
        self.assertTrue(any("Maddur" in name for name in en_route_names))
        self.assertTrue(any("Srirangapatna" in name for name in en_route_names))
        self.assertIn("geometry", result)
        self.assertIsNotNone(result["geometry"])


class WeatherServiceTests(unittest.TestCase):
    @patch("services.weather_service.requests.get")
    def test_weather_service_handles_service_failure_without_crashing(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("503 Service Unavailable")
        mock_get.return_value = mock_response

        service = WeatherService()
        result = service.get_weather_summary("Paris")

        self.assertIn("Weather data is currently unavailable", result["summary"])
        self.assertIsNone(result["temperature_celsius"])

    @patch("services.weather_service.requests.get")
    def test_weather_service_ignores_invalid_temperature_values(self, mock_get):
        geocode_response = Mock()
        geocode_response.raise_for_status.return_value = None
        geocode_response.json.return_value = [{"lat": "12.2958", "lon": "76.6394"}]

        weather_response = Mock()
        weather_response.raise_for_status.return_value = None
        weather_response.json.return_value = {"current": {"temperature_2m": "N/A", "weathercode": 0}}

        mock_get.side_effect = [geocode_response, weather_response]

        result = WeatherService().get_weather_summary("Mysore")
        self.assertIsNone(result["temperature_celsius"])
        self.assertEqual(result["source"], "open-meteo")


class ApiEndpointTests(unittest.TestCase):
    def test_health_endpoint_works(self):
        client = TestClient(app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    @patch("api.TravelPlannerCrew.run")
    def test_trip_generation_endpoint_returns_gemini_trip_and_report_links(self, mock_run):
        mock_run.return_value = {
            "result": "Gemini trip plan.",
            "ai_source": "gemini_live",
            "warnings": [],
            "markdown_path": "outputs/travel_plan.md",
            "pdf_path": "outputs/travel_plan.pdf",
        }

        response = TestClient(app).post(
            "/api/trips/generate",
            json={
                "start": "Bengaluru",
                "destination": "Mysore",
                "days": 2,
                "budget": 10000,
                "travelers": 2,
                "currency": "INR",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], "Gemini trip plan.")
        self.assertEqual(response.json()["ai_source"], "gemini_live")
        self.assertTrue(response.json()["markdown_available"])
        self.assertTrue(response.json()["pdf_available"])

    @patch("api.TravelPlannerCrew.run")
    def test_trip_generation_maps_gemini_400_to_safe_gateway_error(self, mock_run):
        mock_run.side_effect = GeminiProviderError(
            "Gemini rejected the generation request. Check the configured model and generation parameters.",
            provider_status=400,
        )

        response = TestClient(app).post(
            "/api/trips/generate",
            json={"destination": "Mysore", "days": 2, "budget": 10000},
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"],
            "Gemini rejected the generation request. Check the configured model and generation parameters.",
        )

    def test_trip_request_validation_errors_remain_fastapi_422(self):
        response = TestClient(app).post(
            "/api/trips/generate",
            json={"destination": "Mysore", "days": 0, "budget": 10000},
        )

        self.assertEqual(response.status_code, 422)
        self.assertTrue(any(error["loc"][-1] == "days" for error in response.json()["detail"]))

    @patch.object(MapsService, "get_route_details")
    def test_routes_endpoint_returns_directions_budget_and_enroute_stops(self, mock_get_route):
        mock_get_route.return_value = {
            "status": "success",
            "start": {"name": "Bangalore", "latitude": 12.9716, "longitude": 77.5946},
            "destination": {"name": "Mysore", "latitude": 12.2958, "longitude": 76.6394},
            "mode": "driving",
            "distance_km": 140.5,
            "duration_minutes": 130.0,
            "geometry": [[12.9716, 77.5946], [12.2958, 76.6394]],
            "directions": [{"step": 1, "instruction": "Depart Bangalore", "road": "Expressway", "distance_km": 10.0, "duration_minutes": 10.0}],
            "route_budget": {"fuel_cost": 1050.0, "toll_cost": 280.0, "total_one_way": 1830.0},
            "en_route_places": [{"name": "Ramadevara Betta", "is_en_route": True}],
            "destination_places": [{"name": "Mysore Palace", "is_en_route": False}],
            "stops": [{"name": "Ramadevara Betta"}, {"name": "Mysore Palace"}],
            "summary": "Verified driving route",
        }

        response = TestClient(app).get("/api/routes?start=Bangalore&destination=Mysore&mode=driving&travelers=2&travel_style=standard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["distance_km"], 140.5)
        self.assertIn("directions", data)
        self.assertEqual(len(data["directions"]), 1)
        self.assertIn("route_budget", data)
        self.assertEqual(data["route_budget"]["fuel_cost"], 1050.0)
        self.assertIn("en_route_places", data)
        self.assertEqual(data["en_route_places"][0]["name"], "Ramadevara Betta")


class CrewReportTests(unittest.TestCase):
    @patch("crew.crew.WeatherService.get_weather_summary")
    @patch("crew.crew.LocationService.get_location_data")
    @patch("crew.crew.MapsService.get_map_context")
    @patch("crew.crew.MapsService.get_route_context")
    @patch("crew.crew.MarkdownService.write_report")
    @patch("crew.crew.PdfService.generate_pdf")
    @patch("crew.crew.GeminiService.generate_content")
    def test_mysore_report_uses_inr_and_specific_itinerary(
        self,
        mock_gemini,
        mock_pdf,
        mock_markdown,
        mock_route_context,
        mock_map_context,
        mock_location,
        mock_weather,
    ):
        mock_weather.return_value = {
            "summary": "Weather data is currently unavailable for Mysore.",
            "temperature_celsius": None,
            "travel_suitability": "Check locally",
            "source": "unavailable",
        }
        mock_location.return_value = {"local_highlights": ["Mysore Palace", "Chamundi Hills", "Devaraja Market"]}
        mock_map_context.return_value = {
            "nearby_places": ["Mysore Palace", "Chamundi Hills", "Devaraja Market"],
            "map_links": {"openstreetmap": "https://example.com/map"},
        }
        mock_route_context.return_value = {
            "status": "unavailable",
            "summary": "Route data is unavailable; recommendations remain advisory.",
        }
        mock_gemini.return_value = "Gemini-generated Mysore plan with palace viewpoints and food markets."
        mock_markdown.return_value = "reports/mysore.md"
        mock_pdf.return_value = "reports/mysore.pdf"

        result = TravelPlannerCrew().run(
            {
                "start": "Bangalore",
                "destination": "Mysore",
                "days": 2,
                "travelers": 2,
                "budget": 10000,
                "travel_style": "standard",
                "currency": "INR",
                "preferences": "nature, food, heritage sites, relaxed scenic route",
            }
        )

        self.assertIn("₹10,000", result["result"])
        self.assertNotIn("$10,000", result["result"])
        self.assertIn("Mysore Palace", result["result"])
        self.assertIn("Chamundi Hills", result["result"])
        self.assertEqual(result["ai_source"], "gemini_live")

    def test_district_geocoding_anathapuram_maps_to_anantapur(self):
        service = MapsService()
        result = service.geocode("Anathapuram")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(float(result["lat"]), 14.6819, places=2)
        self.assertAlmostEqual(float(result["lon"]), 77.6006, places=2)
        self.assertIn("Anantapur", result["display_name"])

    def test_anathapuram_to_goa_route_and_enroute_stops(self):
        service = MapsService()
        result = service.get_route_details("Anathapuram", "Goa", mode="driving", travelers=2, travel_style="standard")
        self.assertIsNotNone(result["distance_km"])
        self.assertLess(result["distance_km"], 600.0)  # Must be direct ~500-520 km, NOT 838 km
        self.assertGreater(result["distance_km"], 450.0)
        self.assertGreaterEqual(len(result["en_route_places"]), 4)
        en_route_names = [p["name"] for p in result["en_route_places"]]
        self.assertTrue(any("Bellary" in name or "Ballari" in name for name in en_route_names))
        self.assertTrue(any("Hampi" in name for name in en_route_names))
        self.assertTrue(any("Hubli" in name or "Hubballi" in name for name in en_route_names))
        self.assertTrue(any("Dudhsagar" in name for name in en_route_names))

    def test_goa_itinerary_has_distinct_days_without_repetition(self):
        crew = TravelPlannerCrew()
        day_plans = crew._build_day_plans("Goa", 4, {})
        self.assertEqual(len(day_plans), 4)
        summaries = [p["summary"] for p in day_plans]
        # Ensure all 4 days have unique and distinct summaries
        self.assertEqual(len(set(summaries)), 4)
        self.assertTrue(any("Aguada" in summaries[0] or "Baga" in summaries[0] for _ in [1]))
        self.assertTrue(any("Fontainhas" in summaries[1] or "Old Goa" in summaries[1] for _ in [1]))
        self.assertTrue(any("Dudhsagar" in summaries[2] or "Spice" in summaries[2] for _ in [1]))
        self.assertTrue(any("Chapora" in summaries[3] or "Vagator" in summaries[3] for _ in [1]))

    def test_bangalore_to_coorg_route_highlights_and_destination_landmarks(self):
        service = MapsService()
        result = service.get_route_details("Bangalore", "Coorg", mode="driving", travelers=2, travel_style="standard")
        en_route_places = result.get("en_route_places", [])
        destination_places = result.get("destination_places", [])

        self.assertGreaterEqual(len(en_route_places), 5)
        en_route_names = [p["name"] for p in en_route_places]
        self.assertTrue(any("Ramanagara" in name for name in en_route_names))
        self.assertTrue(any("Channapatna" in name for name in en_route_names))
        self.assertTrue(any("Maddur" in name for name in en_route_names))
        self.assertTrue(any("Namdroling" in name or "Golden Temple" in name for name in en_route_names))
        self.assertTrue(any("Nisargadhama" in name for name in en_route_names))

        self.assertGreaterEqual(len(destination_places), 5)
        dest_names = [p["name"] for p in destination_places]
        self.assertTrue(any("Abbey Falls" in name for name in dest_names))
        self.assertTrue(any("Raja's Seat" in name or "Rajas Seat" in name for name in dest_names))
        self.assertTrue(any("Dubare" in name for name in dest_names))
        self.assertTrue(any("Talacauvery" in name for name in dest_names))
        self.assertTrue(any("Madikeri Fort" in name for name in dest_names))
        self.assertTrue(any("Mandalpatti" in name for name in dest_names))

        # Must never return generic "Historic center" or repetitive placeholders
        self.assertNotIn("Historic center", dest_names)
        for p in en_route_places:
            self.assertNotEqual(p["name"], "Scenic Midway Viewpoint & Heritage Rest Stop")

    def test_unregistered_corridor_intermediate_waypoints_distinct_and_no_generic_fallbacks(self):
        service = MapsService()
        result = service.get_route_details("Delhi", "Shimla", mode="driving", travelers=2, travel_style="standard")
        en_route_places = result.get("en_route_places", [])
        self.assertEqual(len(en_route_places), 3)

        # Ensure all 3 intermediate waypoints have distinct names
        names = [p["name"] for p in en_route_places]
        self.assertEqual(len(set(names)), 3)
        self.assertNotIn("Scenic Midway Viewpoint & Heritage Rest Stop", names)

    def test_coorg_itinerary_has_distinct_days_without_repetition(self):
        crew = TravelPlannerCrew()
        day_plans = crew._build_day_plans("Coorg", 4, {})
        self.assertEqual(len(day_plans), 4)
        summaries = [p["summary"] for p in day_plans]
        self.assertEqual(len(set(summaries)), 4)
        self.assertTrue(any("Abbey Falls" in summaries[0] or "Madikeri Fort" in summaries[0] for _ in [1]))
        self.assertTrue(any("Namdroling" in summaries[1] or "Nisargadhama" in summaries[1] for _ in [1]))
        self.assertTrue(any("Talacauvery" in summaries[2] or "Brahmagiri" in summaries[2] for _ in [1]))
        self.assertTrue(any("Mandalpatti" in summaries[3] or "Pushpagiri" in summaries[3] for _ in [1]))


if __name__ == "__main__":
    unittest.main()
