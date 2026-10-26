from __future__ import annotations

from typing import Any


class LocationService:
    KNOWN_DESTINATIONS: dict[str, dict[str, Any]] = {
        "goa": {
            "nearby_attractions": [
                "Baga & Calangute Beach",
                "Fort Aguada & Lighthouse",
                "Basilica of Bom Jesus (Old Goa)",
                "Fontainhas Latin Quarter (Panaji)",
                "Dudhsagar Waterfalls & Mollem",
                "Chapora Fort (Vagator)",
                "Palolem & Agonda Beach",
            ],
            "transportation_options": ["Rental Scooters / Bikes", "Self-drive Thar / Cars", "Goa Miles App Cabs", "Local Ferry Services", "Kadamba Buses"],
            "local_highlights": ["Fort Aguada", "Basilica of Bom Jesus", "Baga Beach", "Fontainhas Latin Quarter"],
            "famous_foods": ["Goan Fish Curry Thali", "Prawns Balchão & Peri Peri", "Chicken Xacuti", "Bebinca & Bebik", "Pork Vindaloo", "Feni & Kokum Solkadhi"],
        },
        "mysore": {
            "nearby_attractions": [
                "Mysore Palace",
                "Chamundi Hills & Sri Chamundeshwari Temple",
                "Devaraja Market",
                "St. Philomena's Cathedral",
                "Brindavan Gardens",
                "Jaganmohan Art Gallery",
            ],
            "transportation_options": ["KSRTC City Bus", "Auto Rickshaw", "App Cabs", "Heritage Tonga Ride"],
            "local_highlights": ["Mysore Palace", "Chamundi Hills", "Devaraja Market"],
            "famous_foods": ["Mylari Masala Dosa", "Traditional Mysore Pak", "Bisi Bele Bath", "Degree Filter Coffee"],
        },
        "bangalore": {
            "nearby_attractions": [
                "Lalbagh Botanical Garden",
                "Cubbon Park",
                "Bangalore Palace",
                "Tipu Sultan's Summer Palace",
                "Vidhana Soudha",
            ],
            "transportation_options": ["Namma Metro", "BMTC Bus", "Auto Rickshaw", "Cabs"],
            "local_highlights": ["Lalbagh Garden", "Cubbon Park", "Bangalore Palace"],
            "famous_foods": ["Benne Dosa at CTR", "Filter Coffee", "Mangalore Buns", "Rava Idli at MTR"],
        },
        "anantapur": {
            "nearby_attractions": [
                "Lepakshi Veerabhadra Temple & Hanging Pillar",
                "Gooty Fort & Hill Citadel",
                "ISKCON Temple Anantapur",
                "Thimmamma Marrimanu Giant Banyan Tree",
                "Penukonda Fort",
            ],
            "transportation_options": ["APSRTC Buses", "Auto Rickshaws", "Private Cabs"],
            "local_highlights": ["Lepakshi Temple", "Gooty Fort", "Thimmamma Marrimanu"],
            "famous_foods": ["Rayalaseema Ragi Mudda", "Gongura Chicken & Pachadi", "Ugadi Pachadi", "Spicy Natu Kodi Biryani"],
        },
        "hampi": {
            "nearby_attractions": [
                "Virupaksha Temple",
                "Vijaya Vitthala Temple & Stone Chariot",
                "Matanga Hill Sunrise View",
                "Lotus Mahal & Elephant Stables",
                "Tungabhadra River Coracle Ride",
            ],
            "transportation_options": ["Rented Bicycles & Mopeds", "Auto Rickshaws", "Coracle Ferry Boats"],
            "local_highlights": ["Virupaksha Temple", "Stone Chariot", "Matanga Hill"],
            "famous_foods": ["South Indian Banana-Leaf Thali", "Mango Tree Special Curries", "Masala Chai & Nutella Pancakes"],
        },
        "coorg": {
            "nearby_attractions": [
                "Abbey Falls",
                "Raja's Seat Sunset Point",
                "Dubare Elephant Camp",
                "Namdroling Golden Temple (Bylakuppe)",
                "Talacauvery Origin of Kaveri River",
            ],
            "transportation_options": ["Private Taxi / Cabs", "Jeep Rentals", "KSRTC Buses"],
            "local_highlights": ["Abbey Falls", "Namdroling Monastery", "Raja's Seat"],
            "famous_foods": ["Coorg Pandi Curry", "Akki Roti with Bamboo Shoot Curry", "Kadamputtu (Rice Dumplings)", "Coorg Estate Filter Coffee"],
        },
        "jaipur": {
            "nearby_attractions": [
                "Amber Fort & Palace",
                "Hawa Mahal (Palace of Winds)",
                "City Palace & Jantar Mantar",
                "Nahargarh Fort Sunset Point",
                "Jal Mahal Water Palace",
            ],
            "transportation_options": ["Jaipur Metro", "E-Rickshaws", "App Cabs", "Auto Rickshaws"],
            "local_highlights": ["Amber Fort", "Hawa Mahal", "City Palace"],
            "famous_foods": ["Dal Baati Churma", "Pyaaz Kachori at Rawat", "Laal Maas", "Ghevar & Lassi at Lassiwala"],
        },
        "kerala": {
            "nearby_attractions": [
                "Alleppey Backwaters Houseboat",
                "Munnar Tea Gardens & Eravikulam",
                "Fort Kochi & Chinese Fishing Nets",
                "Varkala Cliff Beach",
                "Periyar Wildlife Sanctuary (Thekkady)",
            ],
            "transportation_options": ["KSRTC Buses", "Houseboats & Ferries", "Auto Rickshaws", "Tourist Cabs"],
            "local_highlights": ["Alleppey Backwaters", "Munnar Tea Plantations", "Fort Kochi"],
            "famous_foods": ["Kerala Sadya on Banana Leaf", "Appam with Stew", "Karimeen Pollichathu", "Malabar Parotta & Beef Curry"],
        },
        "manali": {
            "nearby_attractions": [
                "Solang Valley Adventure Sports",
                "Atal Tunnel & Sissu Waterfall",
                "Hadimba Temple & Van Vihar",
                "Rohtang Pass Snow View",
                "Old Manali Cafés & Vashisht Hot Springs",
            ],
            "transportation_options": ["Local 4x4 Jeeps", "Rented Royal Enfield Bikes", "HRTC Buses"],
            "local_highlights": ["Solang Valley", "Atal Tunnel", "Hadimba Temple"],
            "famous_foods": ["Himachali Siddu with Ghee", "Trout Fish Fry", "Thukpa & Steamed Momos", "Tibetan Butter Tea"],
        },
        "hyderabad": {
            "nearby_attractions": [
                "Charminar & Laad Bazaar",
                "Golconda Fort & Sound & Light Show",
                "Ramoji Film City",
                "Hussain Sagar Lake & Buddha Statue",
                "Salar Jung Museum & Qutb Shahi Tombs",
            ],
            "transportation_options": ["Hyderabad Metro", "TSRTC City Buses", "Auto Rickshaws", "App Cabs"],
            "local_highlights": ["Charminar", "Golconda Fort", "Ramoji Film City"],
            "famous_foods": ["Hyderabadi Dum Biryani", "Mirchi ka Salan", "Double ka Meetha", "Irani Chai & Osmania Biscuits", "Pathar ka Gosht"],
        },
        "chennai": {
            "nearby_attractions": [
                "Marina Beach Promenade",
                "Kapaleeshwarar Temple (Mylapore)",
                "San Thome Basilica",
                "Fort St. George & Museum",
                "DakshinaChitra Heritage Village",
            ],
            "transportation_options": ["Chennai Metro", "MTC Buses", "MRTS Suburban Trains", "Auto Rickshaws", "App Cabs"],
            "local_highlights": ["Marina Beach", "Kapaleeshwarar Temple", "Mylapore Heritage Walk"],
            "famous_foods": ["Authentic Filter Coffee", "Chettinad Chicken Pepper Fry", "Murugan Idli & Chutneys", "Marina Beach Sundal"],
        },
        "mumbai": {
            "nearby_attractions": [
                "Gateway of India & Taj Mahal Palace",
                "Marine Drive Queens Necklace",
                "Elephanta Caves UNESCO Rock Art",
                "Chhatrapati Shivaji Maharaj Terminus",
                "Colaba Causeway & Bandra Bandstand",
            ],
            "transportation_options": ["Mumbai Local Trains", "BEST Buses", "Mumbai Metro", "Kaali Peeli Taxis", "App Cabs"],
            "local_highlights": ["Gateway of India", "Marine Drive", "Elephanta Caves"],
            "famous_foods": ["Mumbai Vada Pav & Misal Pav", "Pav Bhaji at Sardar", "Bombay Duck Fry", "Bun Maska & Parsi Berry Pulao"],
        },
        "delhi": {
            "nearby_attractions": [
                "Qutub Minar & Mehrauli Archaeological Park",
                "Red Fort & Chandni Chowk Heritage Walk",
                "India Gate & Kartavya Path",
                "Humayun's Tomb Mughal Gardens",
                "Akshardham Temple & Lotus Temple",
            ],
            "transportation_options": ["Delhi Metro", "DTC Electric Buses", "Auto Rickshaws", "App Cabs"],
            "local_highlights": ["Qutub Minar", "India Gate", "Red Fort", "Chandni Chowk"],
            "famous_foods": ["Old Delhi Chhole Bhature", "Authentic Butter Chicken at Daryaganj", "Paranthas at Paranthe Wali Gali", "Dahi Bhalla & Chaat at Natraj"],
        },
        "agra": {
            "nearby_attractions": [
                "Taj Mahal UNESCO Monument of Love",
                "Agra Fort Red Sandstone Citadel",
                "Fatehpur Sikri Imperial Capital",
                "Mehtab Bagh Sunset Viewpoint",
                "Itmad-ud-Daulah (Baby Taj)",
            ],
            "transportation_options": ["Battery Electric Autos", "Tongas & Auto Rickshaws", "Tourist Cabs"],
            "local_highlights": ["Taj Mahal", "Agra Fort", "Fatehpur Sikri"],
            "famous_foods": ["Agra Petha (Paan, Angoori & Kesar)", "Bedmi Puri with Aloo Sabzi", "Mughlai Korma & Biryani", "Crispy Dalmoth Namkeen"],
        },
        "pondicherry": {
            "nearby_attractions": [
                "Promenade Beach & Rock Beach",
                "Auroville Matrimandir Dome of Peace",
                "White Town French Quarter & Cafes",
                "Sri Aurobindo Ashram",
                "Paradise Beach Ferry & Sandbar",
            ],
            "transportation_options": ["Rented Scooters & Bicycles", "Auto Rickshaws", "Tourist Cabs"],
            "local_highlights": ["White Town French Quarter", "Auroville", "Promenade Beach"],
            "famous_foods": ["French Crepes & Croissants", "Seafood Bouillabaisse", "Wood-fired Artisan Pizzas", "South Indian Filter Coffee & Tiffin"],
        },
        "tirupati": {
            "nearby_attractions": [
                "Sri Venkateswara Swamy Temple (Tirumala Hills)",
                "Kapila Theertham Waterfalls & Temple",
                "Silathoranam Natural Geological Arch",
                "Chandragiri Fort & Light Show",
                "Sri Padmavathi Ammavari Temple (Tiruchanur)",
            ],
            "transportation_options": ["Tirumala Ghat Buses", "APSRTC City Buses", "Auto Rickshaws", "Cabs"],
            "local_highlights": ["Tirumala Temple", "Kapila Theertham", "Chandragiri Fort"],
            "famous_foods": ["Tirupati Laddu Prasadam", "Traditional Andhra Banana Leaf Meals", "Ghee Pongal with Chutney", "Pulihora"],
        },
        "visakhapatnam": {
            "nearby_attractions": [
                "RK Beach & INS Kursura Submarine Museum",
                "Kailasagiri Hilltop Ropeway & Vistas",
                "Rushikonda Blue Flag Beach",
                "Araku Valley & Coffee Plantations",
                "Borra Caves Million-Year Stalactites",
            ],
            "transportation_options": ["APSRTC Buses", "Auto Rickshaws", "App Cabs", "Araku Vista Dome Train"],
            "local_highlights": ["Submarine Museum", "Kailasagiri Hill", "Araku Valley", "Borra Caves"],
            "famous_foods": ["Araku Valley Bamboo Chicken", "Andhra Chepala Pulusu (Fish Curry)", "Bongu Biryani", "Madugula Halwa"],
        },
        "ooty": {
            "nearby_attractions": [
                "Nilgiri Mountain Railway (Toy Train)",
                "Ooty Government Botanical Gardens",
                "Doddabetta Peak & Telescope House",
                "Pykara Lake, Boating & Waterfalls",
                "Avalanche Lake Nature Reserve",
            ],
            "transportation_options": ["Nilgiri Toy Train", "Local Tourist Taxis", "TNSTC Buses"],
            "local_highlights": ["Botanical Gardens", "Doddabetta Peak", "Nilgiri Mountain Railway"],
            "famous_foods": ["Ooty Handmade Truffles & Chocolates", "Fresh Nilgiri Orthodox Tea", "Crispy Ooty Varkey", "Fresh Strawberry Cream"],
        },
    }

    DESTINATION_ALIASES: dict[str, str] = {
        "anathapuram": "anantapur",
        "ananthapur": "anantapur",
        "ananthapuramu": "anantapur",
        "bengaluru": "bangalore",
        "mysuru": "mysore",
        "vizag": "visakhapatnam",
        "trivandrum": "kerala",
        "thiruvananthapuram": "kerala",
        "calicut": "kerala",
        "kozhikode": "kerala",
        "cochin": "kerala",
        "kochi": "kerala",
        "munnar": "kerala",
        "alleppey": "kerala",
        "alappuzha": "kerala",
        "madikeri": "coorg",
        "puducherry": "pondicherry",
        "bombay": "mumbai",
        "madras": "chennai",
        "calcutta": "kolkata",
        "kashi": "varanasi",
        "benares": "varanasi",
    }

    def get_location_data(self, destination: str) -> dict[str, Any]:
        dest_key = (destination or "").strip().lower()
        if dest_key in self.DESTINATION_ALIASES:
            dest_key = self.DESTINATION_ALIASES[dest_key]
        else:
            for alias_word, canonical in self.DESTINATION_ALIASES.items():
                if alias_word in dest_key:
                    dest_key = canonical
                    break

        for key, data in self.KNOWN_DESTINATIONS.items():
            if key in dest_key:
                return {
                    "destination": destination,
                    **data,
                }

        return {
            "destination": destination,
            "nearby_attractions": ["Historic center", "Local market", "Scenic viewpoints"],
            "transportation_options": ["Metro", "Bus", "Taxi"],
            "local_highlights": ["Great food scene", "Walkable neighborhoods", "Cultural landmarks"],
            "famous_foods": ["Local regional specialties", "Traditional breakfast", "Street food delicacies"],
        }
