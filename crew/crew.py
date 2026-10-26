from __future__ import annotations

from typing import Any

from services.budget_service import BudgetService
from services.gemini_service import GeminiProviderError, GeminiService
from services.location_service import LocationService
from services.maps_service import MapsService
from services.markdown_service import MarkdownService
from services.pdf_service import PdfService
from services.weather_service import WeatherService
from utils.helpers import format_currency
from utils.logger import AppLogger

logger = AppLogger("crew").get_logger()


class TravelPlannerCrew:
    def __init__(self) -> None:
        self.markdown_service = MarkdownService()
        self.pdf_service = PdfService()

    def _generate_ai_content(
        self,
        trip: dict[str, Any],
        weather: dict[str, Any],
        budget_breakdown: dict[str, Any],
        location_data: dict[str, Any],
        map_context: dict[str, Any],
        route_context: dict[str, Any],
    ) -> tuple[str, str, list[str]]:
        prompt = self._build_prompt(trip, weather, budget_breakdown, location_data, map_context, route_context)
        gemini_service = GeminiService()

        try:
            ai_text = gemini_service.generate_content(prompt, max_output_tokens=8192)
            if not ai_text or not str(ai_text).strip():
                raise ValueError("Gemini returned an empty itinerary.")
            return ai_text, "gemini_live", []
        except GeminiProviderError as exc:
            # Re-raise client errors (400, 401, 403) so API / tests map them properly
            if exc.provider_status in {400, 401, 403, 422}:
                raise
            logger.warning("Gemini live generation unavailable (%s). Using structured offline fallback.", exc)
            fallback_text = self._build_fallback_ai_text(trip, location_data, route_context)
            return fallback_text, "offline_fallback", [str(exc)]
        except Exception as exc:
            logger.warning("Gemini generation failed (%s). Using structured offline fallback.", exc)
            fallback_text = self._build_fallback_ai_text(trip, location_data, route_context)
            return fallback_text, "offline_fallback", [str(exc)]

    def _build_fallback_ai_text(
        self, trip: dict[str, Any], location_data: dict[str, Any], route_context: dict[str, Any]
    ) -> str:
        destination = trip.get("destination", "Mysore")
        start = trip.get("start") or "Bangalore"
        style = trip.get("travel_style", "standard")
        travel_mode = trip.get("travel_mode", "driving")

        if "mysore" in destination.lower():
            return (
                f"Personalized Travel Advisory for {destination} ({style} style via {travel_mode}):\n"
                f"• Route Strategy: Take the Bangalore-Mysore Expressway (NH 275) early morning to avoid peak tollway queues. "
                f"Make sure to stop at Ramanagara for the Ramadevara Betta viewpoint and enjoy hot Maddur Vada at Maddur.\n"
                f"• Sightseeing Strategy: Book Mysore Palace tickets online in advance to bypass long entry queues. Visit Chamundi Hills around 17:30 for cooler evening breeze and sunset panoramas.\n"
                f"• Culinary Recommendations: Do not miss breakfast at Mylari (famous for soft butter dosas) and freshly made warm Mysore Pak from Guru Sweets on Sayyaji Rao Road.\n"
                f"• Heritage & Crafts: Dedicate time on the return route for Channapatna's lacquerware craft emporiums and Srirangapatna's Dariya Daulat Bagh."
            )
        if "coorg" in destination.lower() or "madikeri" in destination.lower():
            return (
                f"Personalized Travel Advisory for {destination} ({style} style via {travel_mode}):\n"
                f"• Route Strategy: Drive via the 10-lane Bangalore-Mysore Expressway (NH 275) to Srirangapatna, then continue towards Hunsur and Kushalnagar. "
                f"Stop at Bylakuppe Golden Temple for serene Tibetan chanting and lunch, followed by Kaveri Nisargadhama bamboo island.\n"
                f"• Sightseeing Strategy: Visit Abbey Falls early in the morning before crowds arrive. Reserve sunset hours for Raja's Seat to witness mist rolling across the Western Ghat valleys.\n"
                f"• Adventure & Coffee: Book a 4x4 open-top jeep safari to Mandalpatti Peak for sweeping vistas above the clouds. Take an authentic guided coffee & spice plantation walk.\n"
                f"• Kodava Gastronomy: Savor authentic Kodava cuisine featuring spicy Pandi Curry (or mushroom/bamboo shoot curry), Kadambuttu (steamed rice dumplings), and freshly brewed estate filter coffee."
            )
        if "goa" in destination.lower():
            return (
                f"Personalized Travel Advisory for {destination} ({style} style via {travel_mode}):\n"
                f"• Route Strategy: Depart early morning via NH 67 / NH 748 passing Bellary, Hampi, and Hubli. Enjoy scenic Western Ghats ghat sections through Mollem.\n"
                f"• Beach & Heritage Strategy: Spend mornings exploring Portuguese heritage in Fontainhas (Panaji) and Basilica of Bom Jesus (Old Goa). Reserve afternoons for Baga/Calangute water sports.\n"
                f"• Sunset & Dining: Watch the sunset from Fort Aguada or Chapora Fort. Indulge in beachfront seafood shacks with authentic Goan Fish Curry Thali and warm Bebinca.\n"
                f"• Nature Excursion: Plan a day trip to the 310m Dudhsagar Waterfalls and a guided spice plantation lunch in Ponda."
            )
        return (
            f"Personalized Travel Advisory for {destination} ({style} style):\n"
            f"• Route Strategy: Follow primary highway corridors and depart during early morning hours for optimal travel time.\n"
            f"• Exploration: Focus on cultural heritage sites during morning hours, enjoy local dining at noon, and reserve scenic viewpoints for sunset.\n"
            f"• Practical Tips: Keep reservations flexible and stay hydrated throughout the journey."
        )

    def run(self, trip_inputs: dict[str, Any]) -> dict[str, Any]:
        trip = self._normalize_trip_inputs(trip_inputs)
        destination = trip["destination"]
        logger.info("Starting travel planning flow for destination %s", destination)

        weather = WeatherService().get_weather_summary(destination)
        budget_breakdown = BudgetService().calculate_budget(
            float(trip["budget"]),
            int(trip["travelers"]),
            int(trip["days"]),
            trip["travel_style"],
            currency=trip.get("currency", "INR"),
        )
        location_data = LocationService().get_location_data(destination)
        map_context = MapsService().get_map_context(destination)
        route_context = MapsService().get_route_context(
            trip.get("start") or destination,
            destination,
            mode=trip.get("travel_mode", "driving"),
            travelers=int(trip["travelers"]),
            travel_style=trip["travel_style"],
        )
        route_data = MapsService().get_route_details(
            trip.get("start") or destination,
            destination,
            mode=trip.get("travel_mode", "driving"),
            travelers=int(trip["travelers"]),
            travel_style=trip["travel_style"],
        )
        ai_text, ai_source, warnings = self._generate_ai_content(
            trip, weather, budget_breakdown, location_data, map_context, route_context
        )

        result = self._build_trip_result(
            trip,
            weather,
            budget_breakdown,
            location_data,
            map_context,
            route_context,
            ai_text,
        )
        markdown_content = self._build_markdown_report(
            result,
            trip,
            weather,
            map_context,
            location_data,
            budget_breakdown,
            route_context,
            ai_source,
        )
        markdown_path = self.markdown_service.write_report(markdown_content)
        pdf_path = self.pdf_service.generate_pdf(markdown_content)

        return {
            "result": str(result),
            "markdown_path": str(markdown_path),
            "pdf_path": str(pdf_path),
            "markdown_content": markdown_content,
            "ai_source": ai_source,
            "warnings": warnings,
            "currency": trip.get("currency", "INR"),
            "budget_breakdown": budget_breakdown,
            "route_context": route_context,
            "route_data": route_data,
        }

    def _normalize_trip_inputs(self, trip_inputs: dict[str, Any]) -> dict[str, Any]:
        destination = (trip_inputs.get("destination") or "").strip()
        if not destination:
            raise ValueError("Destination is required.")

        days = max(1, min(int(trip_inputs.get("days", 3) or 3), 30))
        travelers = max(1, min(int(trip_inputs.get("travelers", 2) or 2), 50))
        budget = max(1.0, float(trip_inputs.get("budget", 1200.0) or 1200.0))
        style = str(trip_inputs.get("travel_style", "standard") or "standard").lower()
        style = style if style in {"budget", "standard", "luxury"} else "standard"
        travel_mode = str(trip_inputs.get("travel_mode", "driving") or "driving").lower()
        currency = str(trip_inputs.get("currency", "INR") or "INR").upper()
        currency = currency if currency in {"INR"} else "INR"

        return {
            "start": (trip_inputs.get("start") or "").strip(),
            "destination": destination,
            "days": days,
            "budget": budget,
            "travelers": travelers,
            "travel_style": style,
            "travel_mode": travel_mode,
            "currency": currency,
            "preferences": (trip_inputs.get("preferences") or "balanced").strip() or "balanced",
        }

    def _build_prompt(
        self,
        trip: dict[str, Any],
        weather: dict[str, Any],
        budget_breakdown: dict[str, Any],
        location_data: dict[str, Any],
        map_context: dict[str, Any],
        route_context: dict[str, Any],
    ) -> str:
        destination = trip["destination"]
        start = trip.get("start") or "Departure City"
        preferences = trip["preferences"]
        style = trip["travel_style"]
        days = trip["days"]
        travelers = trip["travelers"]
        budget = trip["budget"]
        currency = trip.get("currency", "INR")
        travel_mode = trip.get("travel_mode", "driving")

        route_summary = route_context.get("summary", "Route data verified.")
        en_route_places = route_context.get("en_route_places", [])
        en_route_str = ", ".join(en_route_places) if en_route_places else "Scenic highway viewpoints, regional food stalls, and heritage craft towns"

        nearby_places = map_context.get("nearby_places") or ["Historic center", "Local market", "Scenic viewpoint"]
        destination_lower = destination.lower()
        if "mysore" in destination_lower:
            nearby_places = [
                "Mysore Palace",
                "Chamundi Hills",
                "Devaraja Market",
                "St. Philomena's Church",
                "Brindavan Gardens",
            ]
            if not en_route_places:
                en_route_str = "Ramadevara Betta (Sholay Hills), Janapada Loka Museum, Channapatna Toy Village, Maddur Vada Stop, Srirangapatna Fort, Ranganathittu Bird Sanctuary"

        route_budget = route_context.get("route_budget") or {}
        fuel_est = route_budget.get("fuel_cost", 0)
        toll_est = route_budget.get("toll_cost", 0)
        route_budget_note = f"Estimated fuel: {currency} {fuel_est}, Tolls: {currency} {toll_est}." if fuel_est else ""

        return (
            f"You are an expert AI Travel Planner. Generate a comprehensive, professional, all-details travel itinerary for a {days}-day trip "
            f"from {start} to {destination} for {travelers} traveler(s) with a {style} travel style and total budget of {format_currency(budget, currency)}. "
            f"Travel mode: {travel_mode}. Preferences: {preferences}. "
            f"\n\nCRITICAL REQUIREMENTS - INCLUDE ALL OF THE FOLLOWING TRIP DETAILS:\n"
            f"1. DAY-BY-DAY ITINERARY: Structure each day ({1} to {days}) with distinct, detailed sections:\n"
            f"   - Morning (08:00 - 12:30): Specific landmark visits, historical context, entry ticket estimates in {currency}, arrival strategy.\n"
            f"   - Afternoon (12:30 - 17:00): Recommended dining spots with iconic regional dishes, afternoon activities, and scenic spots.\n"
            f"   - Evening (17:00 - 21:30): Sunset viewpoints, evening markets, cultural walks, and dinner suggestions.\n"
            f"2. FAMOUS PLACES TO VISIT BETWEEN THE ROUTE: Highlight famous stopovers and attractions along the highway between {start} and {destination} "
            f"   (En route stops: {en_route_str}). Explain what makes each place famous and why travelers should make a quick stop.\n"
            f"3. ACCURATE ROUTE & DRIVING DIRECTIONS: Provide accurate directions, route distance, travel duration, highway name (e.g. NH 275 / Bangalore-Mysore Expressway), "
            f"   best departure time to avoid traffic, and highway pitstops.\n"
            f"4. ITEMIZED BUDGET BREAKDOWN: Provide clear estimates in {currency} for:\n"
            f"   - Route Travel / Transport (Fuel, highway tolls, parking, or public transit tickets) {route_budget_note}\n"
            f"   - Accommodations ({budget_breakdown.get('hotel_cost', 0)})\n"
            f"   - Meals & Dining ({budget_breakdown.get('food_cost', 0)})\n"
            f"   - Activities & Entry Tickets ({budget_breakdown.get('activity_cost', 0)})\n"
            f"   - Contingency Buffer ({budget_breakdown.get('misc_cost', 0)})\n"
            f"   - Total estimated group cost & per-person cost.\n"
            f"5. LOCAL FOOD & DINING: Signature dishes to try and renowned eateries.\n"
            f"6. WEATHER & PRACTICAL TIPS: Weather summary ({weather.get('summary', 'Seasonal conditions')}), packing essentials, and travel safety.\n"
            f"\nContext data:\n"
            f"- Route summary: {route_summary}\n"
            f"- Destination highlights: {', '.join(nearby_places)}\n"
            f"- Local culture: {', '.join(location_data.get('local_highlights', ['local heritage']))}\n"
            f"- Food suggestions: {', '.join(location_data.get('famous_foods', ['regional cuisine']))}\n"
            f"If visiting Mysore, prioritize specific places such as Mysore Palace, Devaraja Market, Chamundi Hills, St. Philomena's Church, and Brindavan Gardens when they align with the trip style and timing. "
            f"Clearly label any unverified information as not confirmed."
        )

    def _build_day_plans(self, destination: str, days: int, location_data: dict[str, Any]) -> list[dict[str, str]]:
        dest_norm = destination.lower()
        plans: list[dict[str, str]] = []

        if "goa" in dest_norm:
            goa_templates = [
                {
                    "title": "North Goa Coastal Discovery & Fort Aguada",
                    "morning": "Depart early for Fort Aguada, a 17th-century Portuguese fortress and historic 4-storey lighthouse with sweeping Arabian Sea panoramas (Entry: ₹50). Stroll along pristine Sinquerim beach.",
                    "afternoon": "Head to Calangute and Baga beach for water sports (parasailing, jet-skiing). Relish lunch at a beachfront shack with authentic Goan Fish Curry Thali, fried calamari, and chilled tender coconut.",
                    "evening": "Stroll along vibrant Tito's lane and Baga night market stalls, followed by a candlelit seaside dinner with live acoustic music and warm Bebinca dessert.",
                    "summary": "Day 1: Explore Fort Aguada's 17th-century coastal ramparts, experience water sports at Baga and Calangute, and enjoy a seaside sunset dinner with authentic Goan fish curry.",
                },
                {
                    "title": "Old Goa UNESCO Heritage & Fontainhas Latin Quarter",
                    "morning": "Explore Velha Goa (Old Goa) UNESCO landmarks: Basilica of Bom Jesus (sacred relics of St. Francis Xavier) and the grand Se Cathedral with its Golden Bell (Free entry).",
                    "afternoon": "Drive to Panaji and wander through Fontainhas, Asia's only surviving Portuguese Latin quarter. Admire vibrant yellow and cobalt-blue heritage villas and stop by 31st January Bakery for warm pastel de nata.",
                    "evening": "Board an evening Mandovi River sunset cruise featuring Goan folk dances (Corridinho and Fugdi), followed by a riverfront dinner near Miramar beach.",
                    "summary": "Day 2: Marvel at Old Goa's UNESCO baroque basilicas, wander the colorful Portuguese alleys of Fontainhas in Panaji, and take an evening Mandovi river cruise.",
                },
                {
                    "title": "Dudhsagar Waterfalls Safari & Ponda Spice Plantation",
                    "morning": "Early morning jeep safari excursion through Mollem National Park to the majestic 310m 4-tiered Dudhsagar Waterfalls. Take a refreshing dip in the natural pool below the cascades.",
                    "afternoon": "Visit Sahakari or Tropical Spice Plantation in Ponda for a guided botanical spice walk, followed by an authentic traditional Goan buffet served on banana leaves.",
                    "evening": "Drive to peaceful South Goa — relax at Colva or Palolem crescent beach, watch the fishing boats return, and savor sunset seafood balchão.",
                    "summary": "Day 3: Take an exhilarating 4x4 jungle safari to the 310m Dudhsagar Waterfalls, visit a traditional spice plantation in Ponda, and relax on peaceful South Goa beaches.",
                },
                {
                    "title": "Clifftop Forts, Flea Markets & Farewell Sunset",
                    "morning": "Hike up to the red-laterite ramparts of Chapora Fort (Bollywood 'Dil Chahta Hai' viewpoint) for spectacular vistas of the Vagator coast and Chapora river.",
                    "afternoon": "Leisurely café lunch in Anjuna or Vagator (try Goan Chicken Xacuti and Poee bread). Browse local artisanal markets for cashews, feni, spices, and handmade souvenirs.",
                    "evening": "Sunset farewell dinner at Vagator clifftop overlooking the Arabian Sea, celebrating a memorable Goan holiday with friends.",
                    "summary": "Day 4: Take in coastal panoramas from Chapora Fort, browse artisan flea markets in Anjuna, and enjoy a celebratory farewell sunset dinner.",
                },
                {
                    "title": "South Goa Heritage & Secluded Shores",
                    "morning": "Journey south to Cabo de Rama clifftop fort with sweeping views over the southern Arabian coastline.",
                    "afternoon": "Relax on pristine Agonda Beach, known for peaceful palm groves and Olive Ridley turtle nesting grounds. Enjoy lunch at an eco-shack.",
                    "evening": "Scenic sunset walk along Palolem's crescent bay, followed by freshly caught grilled kingfish dinner under beach lanterns.",
                    "summary": "Day 5: Discover the remote clifftop ruins of Cabo de Rama and unwind on the secluded golden sands of Agonda and Palolem.",
                },
            ]
            for day_idx in range(days):
                if day_idx < len(goa_templates):
                    plans.append(goa_templates[day_idx])
                else:
                    d_num = day_idx + 1
                    plans.append({
                        "title": "Hidden Gems & Backwaters of Goa",
                        "morning": "Take a ferry to Divar or Chorão Island for peaceful morning cycling past mangrove reserves and the Salim Ali Bird Sanctuary.",
                        "afternoon": "Relaxed lunch at an island taverna, followed by local cashew processing workshop or Ayurvedic wellness spa.",
                        "evening": "Sunset boat ride on the Chapora backwaters and a farewell celebratory coastal feast.",
                        "summary": f"Day {d_num}: Experience tranquil backwater cycling on Divar Island, bird watching at Salim Ali Sanctuary, and relaxing sunset river cruises.",
                    })
            return plans

        if "mysore" in dest_norm:
            mysore_templates = [
                {
                    "title": "Royal Heritage & Palatial Wonders",
                    "morning": "Arrive in Mysore and visit the magnificent Mysore Palace (Amba Vilas). Marvel at the Durbar Hall, ornate stained glass, and royal courtyards (Est. Entry: ₹100/adult).",
                    "afternoon": "Savor authentic lunch with Mysore Mylari Dosa or a traditional Karnataka plantain-leaf thali. Stroll through the bustling heritage Devaraja Market for Mysore sandalwood, silk, and spices.",
                    "evening": "Ascend Chamundi Hills to visit the Sri Chamundeshwari Temple and observe the monolithic Nandi bull statue while enjoying panoramic sunset vistas across the city.",
                    "summary": "Day 1: Begin with the magnificent Mysore Palace and its royal heritage quarter, stroll through vibrant Devaraja Market for spices, silk, and local delicacies, and spend the evening enjoying panoramic sunset views at Chamundi Hills.",
                },
                {
                    "title": "Art, Architecture & Illuminated Fountains",
                    "morning": "Visit the majestic neo-gothic St. Philomena's Cathedral with its twin 175-foot spires, followed by the Jaganmohan Palace and Art Gallery housing rare Raja Ravi Varma oil masterpieces.",
                    "afternoon": "Enjoy a relaxed South Indian meal followed by visits to sandalwood oil and silk weaving artisan craft emporiums.",
                    "evening": "Scenic drive to Brindavan Gardens built across the Krishnarajasagara (KRS) Dam to witness the terrace gardens, musical fountain light show, and lakeside promenade.",
                    "summary": "Day 2: Explore the neo-gothic St. Philomena's Cathedral and Jaganmohan Palace Art Gallery, stop by heritage artisan workshops, and head to Brindavan Gardens and the KRS Dam for evening musical fountain lights.",
                },
                {
                    "title": "River Island Fortress & Bird Sanctuary Safari",
                    "morning": "Excursion to the historic island of Srirangapatna — explore Tipu Sultan's Summer Palace (Dariya Daulat Bagh), the river moat, and the ancient Sri Ranganathaswamy Temple.",
                    "afternoon": "Boat safari at Ranganathittu Bird Sanctuary on the Kaveri river observing nesting painted storks, spoonbills, and marsh crocodiles.",
                    "evening": "Return to Mysore for farewell shopping, box of warm melt-in-mouth Mysore Pak from Guru Sweets, and a leisurely rooftop dinner.",
                    "summary": "Day 3: Take an excursion to nearby Srirangapatna island fortress, visit Ranganathittu Bird Sanctuary for a Kaveri river boat safari, and enjoy a traditional Mysore dinner.",
                },
                {
                    "title": "Leisurely Exploration & Countryside Excursion",
                    "morning": "Visit Somnathpura Chennakeshava Temple (Hoysala architecture) or Karanji Lake nature walk.",
                    "afternoon": "Local dining and craft souvenir shopping.",
                    "evening": "Relaxed dinner and café visits around Gokulam.",
                    "summary": "Day 4: Take an excursion to nearby Somnathpura Hoysala temple and enjoy a nature walk around Karanji Lake.",
                },
            ]
            for day_idx in range(days):
                if day_idx < len(mysore_templates):
                    plans.append(mysore_templates[day_idx])
                else:
                    d_num = day_idx + 1
                    plans.append({
                        "title": "Mysore Countryside & Cultural Excursion",
                        "morning": "Morning nature walk at Karanji Lake Aviary or Lalitha Mahal Palace heritage grounds.",
                        "afternoon": "Artisanal silk weaving demonstration and local South Indian lunch.",
                        "evening": "Sunset leisure time at Kukkarahalli Lake and farewell dinner.",
                        "summary": f"Day {d_num}: Enjoy tranquil nature trails around Karanji Lake, explore artisan silk emporiums, and relax at local heritage cafes.",
                    })
            return plans

        if "coorg" in dest_norm or "madikeri" in dest_norm:
            coorg_templates = [
                {
                    "title": "Madikeri Hilltop Citadel & Cascading Abbey Falls",
                    "morning": "Arrive in Madikeri and visit the 17th-century Madikeri Fort & Palace Museum, observing Kodagu royal artifacts and stone elephant sculptures. Hike down through private coffee and spice plantations to Abbey Falls & the suspension hanging bridge (Entry: ₹30).",
                    "afternoon": "Relish an authentic Kodava lunch featuring spicy Pandi Curry (or bamboo shoot / mushroom curry) paired with fluffy Kadambuttu (steamed rice dumplings) and Akki Roti.",
                    "evening": "Head to Raja's Seat terraced gardens for a mesmerizing sunset overlooking rolling mist-draped Western Ghats valleys, followed by the musical fountain light show.",
                    "summary": "Day 1: Explore historic Madikeri Fort, witness the majestic 70-foot Abbey Falls framed by lush coffee plantations, savor traditional Kodava cuisine, and catch the sunset at Raja's Seat.",
                },
                {
                    "title": "Tibetan Culture & Kaveri River Island Wildlife",
                    "morning": "Drive to Bylakuppe, the second largest Tibetan settlement in India, to marvel at the Namdroling Monastery (Golden Temple) with its 40-foot gilded Buddha statues and reverberating prayer halls.",
                    "afternoon": "Enjoy a Tibetan lunch of steamed momos and thukpa in Bylakuppe, then visit Kaveri Nisargadhama — an enchanting 64-acre bamboo island reached via a hanging rope bridge with deer park and pedal boats.",
                    "evening": "Visit Dubare Elephant Camp along the banks of the Kaveri river; observe elephant activities and enjoy peaceful evening coracle boating on the river.",
                    "summary": "Day 2: Marvel at the Golden Temple at Namdroling Tibetan Monastery in Bylakuppe, walk the rope bridge of Kaveri Nisargadhama bamboo island, and visit Dubare Elephant Camp on the Kaveri river.",
                },
                {
                    "title": "Sacred Kaveri Birthplace & Brahmagiri Mountain Vistas",
                    "morning": "Embark on a scenic drive through misty Western Ghats ridges to Talacauvery (1,276m) nestled in the Brahmagiri Hills, the sacred origin of the holy Kaveri river with panoramic peak lookouts.",
                    "afternoon": "Visit the sacred temple confluence at Bhagamandala (Triveni Sangam). Return through coffee country for a guided coffee and black pepper plantation tour with estate-brewed coffee tasting.",
                    "evening": "Stroll through Madikeri's local spices bazaar to shop for estate-grown Arabica & Robusta coffee beans, pure Kodagu honey, homemade chocolates, and fresh green cardamom.",
                    "summary": "Day 3: Journey to Talacauvery atop Brahmagiri Hills at the sacred birth source of the river Kaveri, explore Bhagamandala Triveni Sangam, and take a guided coffee estate plantation walk.",
                },
                {
                    "title": "Mandalpatti 4x4 Jeep Safari & Cloud-Kissed Ridges",
                    "morning": "Take an exhilarating open-top 4x4 jeep safari up to Mandalpatti Peak (4,050 feet) inside Pushpagiri Wildlife Sanctuary for breathtaking views floating above a sea of clouds.",
                    "afternoon": "Descend towards Chelavara Falls or Chingara Falls, followed by lunch at a scenic countryside homestay featuring authentic Kodava bamboo shoot curries and estate tea.",
                    "evening": "Sunset walk around Gaddige (Raja's Tomb) featuring Indo-Saracenic royal mausoleums, followed by a celebratory candlelit dinner featuring local Coorg specialties.",
                    "summary": "Day 4: Experience a thrilling 4x4 off-road jeep safari to Mandalpatti Peak above the clouds, visit Chelavara Falls, and enjoy a farewell Kodava feast in Madikeri.",
                },
            ]
            for day_idx in range(days):
                if day_idx < len(coorg_templates):
                    plans.append(coorg_templates[day_idx])
                else:
                    d_num = day_idx + 1
                    plans.append({
                        "title": f"Nagarhole Safari & Western Ghats Nature ({destination})",
                        "morning": "Early morning wildlife safari into Nagarhole National Park (Kabini corridor) in search of Asian elephants, spotted deer, and leopards.",
                        "afternoon": "Relaxed lunch by the forest lodge, followed by an Ayurvedic spice wellness massage or visit to Iruppu Falls.",
                        "evening": "Sunset nature walk along the Kabini riverfront and a warm farewell estate dinner.",
                        "summary": f"Day {d_num}: Take an exhilarating Nagarhole National Park wildlife safari, visit pristine Iruppu Falls, and relax on peaceful forest river walks.",
                    })
            return plans

        # Generic dynamic itinerary builder for ANY Indian city or district
        generic_themes = [
            ("Historic Old Town & Heritage Monuments",
             f"Begin the journey exploring {destination}'s iconic historic landmarks, sacred heritage sites, and architectural monuments.",
             f"Enjoy authentic regional dining at a renowned local eatery, followed by neighborhood explorations and artisan bazaars.",
             f"Take a scenic sunset walk along popular promenades, ending with a relaxing dinner featuring signature local dishes.",
             f"Day 1: Explore top architectural and heritage monuments in {destination}, savor authentic regional lunch, and take an evening promenade walk."),
            ("Scenic Vistas, Nature & Waterfronts",
             f"Head out for morning scenic viewpoints, lush gardens, or waterfront trails offering panoramic vistas across {destination}.",
             f"Visit traditional craft centers and handicraft emporiums, followed by a relaxed afternoon lunch at a garden restaurant.",
             f"Catch the golden hour at an iconic sunset spot, followed by evening shopping and sampling famous local street food.",
             f"Day 2: Experience {destination}'s top scenic viewpoints and nature trails, browse artisan craft bazaars, and enjoy sunset dining."),
            ("Cultural Museums, Art & Gastronomic Tour",
             f"Visit prominent cultural museums and art galleries showcasing the rich history and artistic traditions of {destination}.",
             f"Embark on a signature culinary food trail tasting regional delicacies and traditional desserts.",
             f"Enjoy an evening cultural performance, music event, or a relaxed stroll through the city's illuminated market square.",
             f"Day 3: Immerse in {destination}'s cultural museums, experience a signature gastronomic food trail, and enjoy an evening cultural stroll."),
            ("Countryside Excursion & Local Sanctuaries",
             f"Take a half-day excursion to nearby natural reserves, fortress ruins, or tranquil countryside villages outside {destination}.",
             f"Enjoy rustic countryside lunch featuring farm-fresh regional specialties.",
             f"Return to the city for farewell souvenir shopping, picking up famous local handicrafts, spices, and confectionery.",
             f"Day 4: Excursion to scenic countryside outskirts and nature reserves, followed by farewell souvenir shopping and celebratory dining."),
        ]
        for day_idx in range(days):
            theme = generic_themes[day_idx % len(generic_themes)]
            d_num = day_idx + 1
            plans.append({
                "title": f"{theme[0]} ({destination})",
                "morning": theme[1],
                "afternoon": theme[2],
                "evening": theme[3],
                "summary": f"Day {d_num}: {theme[4].split(': ', 1)[-1]}",
            })
        return plans

    def _build_trip_result(
        self,
        trip: dict[str, Any],
        weather: dict[str, Any],
        budget_breakdown: dict[str, Any],
        location_data: dict[str, Any],
        map_context: dict[str, Any],
        route_context: dict[str, Any],
        ai_text: str,
    ) -> str:
        destination = trip["destination"]
        start = trip["start"] or "Current location"
        days = trip["days"]
        travelers = trip["travelers"]
        currency = trip.get("currency", "INR")
        style = trip["travel_style"].title()
        preferences = trip["preferences"]
        nearby_places = map_context.get("nearby_places", ["Historic center", "Local market", "Scenic viewpoint"])

        # En route places between start and destination
        en_route_places = route_context.get("en_route_places") or [
            "Midway Highway Rest Stop",
            "Scenic Regional Viewpoint",
            "Historic Corridor Landmark",
        ]

        day_plans = self._build_day_plans(destination, days, location_data)
        day_sections = [plan["summary"] for plan in day_plans]
        total_group_budget = budget_breakdown.get("group_budget", trip["budget"])
        total_per_traveler = budget_breakdown.get("budget_per_traveler", total_group_budget / max(travelers, 1))

        route_note = route_context.get("summary", "Route data unavailable; recommendations remain advisory.")
        dist_km = route_context.get("distance_km")
        dur_min = route_context.get("duration_minutes")
        route_stats = f"Distance: {dist_km} km, Estimated Travel Duration: {dur_min} mins." if dist_km else "Route distance estimated from travel corridor."

        route_budget = route_context.get("route_budget") or {}
        route_budget_text = ""
        if route_budget.get("total_one_way"):
            route_budget_text = (
                f"Route travel cost estimate: {format_currency(route_budget['total_one_way'], currency)} one-way "
                f"({format_currency(route_budget.get('total_round_trip', route_budget['total_one_way'] * 2), currency)} round-trip), "
                f"including fuel ({format_currency(route_budget.get('fuel_cost', 0), currency)}), "
                f"highway tolls ({format_currency(route_budget.get('toll_cost', 0), currency)}), "
                f"and refreshments."
            )

        weather_summary = weather.get("summary", "Weather information unavailable")
        weather_temperature = weather.get("temperature_celsius")
        temp_text = (
            f"Temperature: {weather_temperature}°C."
            if isinstance(weather_temperature, (int, float)) and weather_temperature is not None
            else "Temperature: unavailable."
        )
        budget_summary = (
            f"Estimated group budget: {format_currency(total_group_budget, currency)}; "
            f"estimated cost per traveler: {format_currency(total_per_traveler, currency)}. "
            f"All amounts are estimates in INR."
        )

        lines = [
            f"Itinerary overview: A {style.lower()} {days}-day trip from {start} to {destination} for {travelers} traveler(s).",
            *day_sections,
            f"Route note: {route_note}",
            f"Route navigation: {route_stats}",
            f"Places between route: {', '.join(en_route_places[:5])}",
            f"Budget guidance: {budget_summary}",
        ]
        if route_budget_text:
            lines.append(f"Route budget: {route_budget_text}")
        lines.extend([
            f"Travel preferences: {preferences}",
            f"Weather status: {weather_summary}. {temp_text}",
            f"Map context: {map_context.get('map_links', {}).get('openstreetmap', 'Map preview unavailable')}",
            f"Local highlights: {', '.join(location_data.get('local_highlights', ['local culture']))}",
            f"Popular stops: {', '.join(nearby_places[:3])}",
            f"Advisor: {ai_text}",
        ])

        return "\n".join(lines)

    def _build_markdown_report(
        self,
        result: str,
        trip_inputs: dict[str, Any],
        weather: dict[str, Any],
        map_context: dict[str, Any],
        location_data: dict[str, Any],
        budget_breakdown: dict[str, Any],
        route_context: dict[str, Any],
        ai_source: str,
    ) -> str:
        destination = trip_inputs.get("destination", "Unknown Destination")
        start = trip_inputs.get("start", "").strip() or "Current location"
        days = trip_inputs.get("days", 3)
        travelers = trip_inputs.get("travelers", 2)
        currency = trip_inputs.get("currency", "INR")
        budget = float(trip_inputs.get("budget", 1200.0) or 0)
        style = trip_inputs.get("travel_style", "standard").title()
        travel_mode = str(trip_inputs.get("travel_mode", "driving")).replace("_", " ").title()
        preferences = trip_inputs.get("preferences", "balanced")
        nearby_places = map_context.get("nearby_places", ["Historic center", "Local market", "Scenic viewpoint"])
        route_note = route_context.get("summary", "Route data unavailable; recommendations remain advisory.")
        distance_km = route_context.get("distance_km")
        duration_minutes = route_context.get("duration_minutes")

        weather_summary = weather.get("summary", "Weather information unavailable")
        weather_temperature = weather.get("temperature_celsius")
        formatted_temp = (
            f"{weather_temperature}°C" if isinstance(weather_temperature, (int, float)) and weather_temperature is not None else "Unavailable"
        )

        route_budget = route_context.get("route_budget") or {}
        directions = route_context.get("directions") or []
        en_route_places = route_context.get("en_route_places") or []

        # Build Day-wise detailed itinerary
        day_plans = self._build_day_plans(destination, days, location_data)
        day_blocks = []
        for idx, plan in enumerate(day_plans, start=1):
            day_blocks.append(
                f"### Day {idx}: {plan['title']}\n"
                f"- **Morning (08:30 - 12:30):** {plan['morning']}\n"
                f"- **Afternoon (12:30 - 16:30):** {plan['afternoon']}\n"
                f"- **Evening (17:00 - 21:00):** {plan['evening']}"
            )
        day_entries_text = "\n\n".join(day_blocks)

        # Build en route stops list
        if en_route_places:
            en_route_text = "\n".join(f"- **{place}**: Famous highway stopover between {start} and {destination}." for place in en_route_places)
        elif "mysore" in destination.lower():
            en_route_text = """- **Ramadevara Betta (Ramanagara)**: Famous rocky hills where Bollywood classic *Sholay* was filmed; India's only dedicated vulture sanctuary.
- **Janapada Loka Museum**: 15-acre open-air museum preserving Karnataka's rural folk arts and traditional puppets.
- **Channapatna Toy Village**: Renowned 'Town of Toys' famous for GI-tagged wooden toys and lacquerware artisan craft centers.
- **Maddur Tiffany's**: Historic home of the iconic *Maddur Vada* paired with hot filter coffee.
- **Srirangapatna Fort**: River island fortress featuring Tipu Sultan's Summer Palace (Dariya Daulat Bagh) and ancient temples.
- **Ranganathittu Bird Sanctuary**: Premier river bird sanctuary with boat safaris past painted storks and crocodiles."""
        else:
            en_route_text = "- Scenic midway highway viewpoints, regional food stalls, and heritage craft towns along the route."

        # Build directions text
        if directions:
            directions_text = "\n".join(
                f"{step['step']}. **{step.get('instruction')}** ({step.get('road')}, {step.get('distance_km')} km)"
                for step in directions[:8]
            )
        else:
            directions_text = (
                f"1. Depart {start} via the main arterial expressway towards {destination}.\n"
                f"2. Follow the designated intercity corridor past intermediate scenic waypoints.\n"
                f"3. Take the designated city exit towards {destination} center."
            )

        return f"""# Travel Plan Report: {start} to {destination}

## Executive Summary
A comprehensive {style.lower()} travel plan for **{destination}** for **{days} days**, designed for **{travelers} traveler(s)** with a total budget of **{format_currency(budget, currency)}** via **{travel_mode}**. Preferences focus on {preferences}.

## Destination Overview
- **Starting Point:** {start}
- **Destination:** {destination}
- **Duration:** {days} days
- **Travelers:** {travelers} traveler(s)
- **Travel Style:** {style}
- **Travel Mode:** {travel_mode}
- **Currency:** {currency}
- **Total Group Budget:** {format_currency(budget, currency)}
- **Estimated Cost Per Traveler:** {format_currency(budget / max(travelers, 1), currency)}
- **Preferences:** {preferences}

## Accurate Route Map & Travel Directions
- **Route Status:** {route_note}
- **Distance:** {distance_km if distance_km else 'Estimated ~140.0'} km
- **Estimated Travel Duration:** {duration_minutes if duration_minutes else 'Estimated ~135.0'} minutes
- **Recommended Highway:** Bangalore-Mysore Expressway (NH 275) / Intercity Corridor

### Step-by-Step Directions:
{directions_text}

## Famous Places to Visit Between Your Route
{en_route_text}

## Day-Wise Detailed Itinerary
{day_entries_text}

## Route Travel Budget
- **Estimated Fuel Cost:** {format_currency(route_budget.get('fuel_cost', 0), currency)}
- **Estimated Highway Tolls:** {format_currency(route_budget.get('toll_cost', 0), currency)}
- **Highway Refreshments & Food:** {format_currency(route_budget.get('highway_refreshments', 0), currency)}
- **Total Route Travel Cost (One-Way):** {format_currency(route_budget.get('total_one_way', 0), currency)}
- **Total Route Travel Cost (Round-Trip):** {format_currency(route_budget.get('total_round_trip', 0), currency)}
- **Route Cost Per Traveler:** {format_currency(route_budget.get('cost_per_traveler', 0), currency)}

## Overall Trip Budget Breakdown
- **Accommodation estimate:** {format_currency(budget_breakdown.get('hotel_cost', 0), currency)} total / {format_currency(budget_breakdown.get('hotel_cost_per_traveler', 0), currency)} per traveler
- **Food & Dining estimate:** {format_currency(budget_breakdown.get('food_cost', 0), currency)} total / {format_currency(budget_breakdown.get('food_cost_per_traveler', 0), currency)} per traveler
- **Transport & Route estimate:** {format_currency(budget_breakdown.get('transport_cost', 0), currency)} total / {format_currency(budget_breakdown.get('transport_cost_per_traveler', 0), currency)} per traveler
- **Activities & Entry Tickets estimate:** {format_currency(budget_breakdown.get('activity_cost', 0), currency)} total / {format_currency(budget_breakdown.get('activity_cost_per_traveler', 0), currency)} per traveler
- **Contingency & Miscellaneous estimate:** {format_currency(budget_breakdown.get('misc_cost', 0), currency)} total / {format_currency(budget_breakdown.get('misc_cost_per_traveler', 0), currency)} per traveler
- **Total estimated allocation:** {format_currency(budget_breakdown.get('total_estimated_cost', budget), currency)}

## Weather Information
- **Current weather summary:** {weather_summary}
- **Temperature:** {formatted_temp}
- **Weather source:** {weather.get('source', 'unavailable')}
- **Travel suitability:** {weather.get('travel_suitability', 'Good for travel')}

## Must-Visit Destination Attractions
- {', '.join(nearby_places)}

## AI Provider Status
- **AI source:** {'Gemini live response' if ai_source == 'gemini_live' else 'Offline fallback used; no live Gemini response was available'}
- **Notes:** Estimated costs, driving routes, and schedule timings are planning figures, not confirmed bookings. All amounts are in INR.

## Practical Travel Tips
- Start early (around 06:30 - 07:00 AM) to beat city traffic and enjoy a scenic morning highway drive.
- Wear comfortable footwear suitable for walking through palace corridors and heritage monuments.
- Carry hydration, sun protection, and a light shawl or scarf for temple visits.

## Crew Output Summary
{result}
"""
