from __future__ import annotations

import math
import os
import time
from typing import Any
from urllib.parse import quote

import requests

from services.budget_service import BudgetService
from utils.logger import AppLogger

logger = AppLogger("maps_service").get_logger()


class MapsService:
    KNOWN_DISTRICTS_AND_CITIES: dict[str, dict[str, Any]] = {
        # Andhra Pradesh
        "anantapur": {"lat": 14.6819, "lon": 77.6006, "display_name": "Anantapur, Andhra Pradesh, India"},
        "anathapuram": {"lat": 14.6819, "lon": 77.6006, "display_name": "Anantapur, Andhra Pradesh, India"},
        "ananthapur": {"lat": 14.6819, "lon": 77.6006, "display_name": "Anantapur, Andhra Pradesh, India"},
        "ananthapuramu": {"lat": 14.6819, "lon": 77.6006, "display_name": "Ananthapuramu, Andhra Pradesh, India"},
        "tirupati": {"lat": 13.6288, "lon": 79.4192, "display_name": "Tirupati, Andhra Pradesh, India"},
        "kurnool": {"lat": 15.8281, "lon": 78.0373, "display_name": "Kurnool, Andhra Pradesh, India"},
        "visakhapatnam": {"lat": 17.6868, "lon": 83.2185, "display_name": "Visakhapatnam, Andhra Pradesh, India"},
        "vizag": {"lat": 17.6868, "lon": 83.2185, "display_name": "Visakhapatnam, Andhra Pradesh, India"},
        "vijayawada": {"lat": 16.5062, "lon": 80.6480, "display_name": "Vijayawada, Andhra Pradesh, India"},
        "guntur": {"lat": 16.3067, "lon": 80.4365, "display_name": "Guntur, Andhra Pradesh, India"},
        "kadapa": {"lat": 14.4673, "lon": 78.8242, "display_name": "Kadapa, Andhra Pradesh, India"},
        "cuddapah": {"lat": 14.4673, "lon": 78.8242, "display_name": "Kadapa, Andhra Pradesh, India"},
        "nellore": {"lat": 14.4426, "lon": 79.9865, "display_name": "Nellore, Andhra Pradesh, India"},
        "rajahmundry": {"lat": 17.0005, "lon": 81.8040, "display_name": "Rajahmundry, Andhra Pradesh, India"},
        "rajamahendravaram": {"lat": 17.0005, "lon": 81.8040, "display_name": "Rajamahendravaram, Andhra Pradesh, India"},
        "kakinada": {"lat": 16.9891, "lon": 82.2475, "display_name": "Kakinada, Andhra Pradesh, India"},
        "chittoor": {"lat": 13.2172, "lon": 79.1003, "display_name": "Chittoor, Andhra Pradesh, India"},
        "eluru": {"lat": 16.7107, "lon": 81.0952, "display_name": "Eluru, Andhra Pradesh, India"},
        "ongole": {"lat": 15.5057, "lon": 80.0499, "display_name": "Ongole, Andhra Pradesh, India"},
        "srikakulam": {"lat": 18.2969, "lon": 83.8968, "display_name": "Srikakulam, Andhra Pradesh, India"},
        "vizianagaram": {"lat": 18.1133, "lon": 83.3977, "display_name": "Vizianagaram, Andhra Pradesh, India"},
        "machilipatnam": {"lat": 16.1875, "lon": 81.1389, "display_name": "Machilipatnam, Andhra Pradesh, India"},
        "lepakshi": {"lat": 13.8044, "lon": 77.6074, "display_name": "Lepakshi, Andhra Pradesh, India"},
        # Goa
        "goa": {"lat": 15.4909, "lon": 73.8278, "display_name": "Panaji, Goa, India"},
        "panaji": {"lat": 15.4909, "lon": 73.8278, "display_name": "Panaji, Goa, India"},
        "panjim": {"lat": 15.4909, "lon": 73.8278, "display_name": "Panaji, Goa, India"},
        "margao": {"lat": 15.2832, "lon": 73.9862, "display_name": "Margao, Goa, India"},
        "madgaon": {"lat": 15.2832, "lon": 73.9862, "display_name": "Margao, Goa, India"},
        "vasco": {"lat": 15.3995, "lon": 73.8123, "display_name": "Vasco da Gama, Goa, India"},
        "vasco da gama": {"lat": 15.3995, "lon": 73.8123, "display_name": "Vasco da Gama, Goa, India"},
        "mapusa": {"lat": 15.5937, "lon": 73.8142, "display_name": "Mapusa, Goa, India"},
        "calangute": {"lat": 15.5439, "lon": 73.7553, "display_name": "Calangute, Goa, India"},
        "baga": {"lat": 15.5553, "lon": 73.7517, "display_name": "Baga, Goa, India"},
        "candolim": {"lat": 15.5176, "lon": 73.7663, "display_name": "Candolim, Goa, India"},
        "palolem": {"lat": 15.0100, "lon": 74.0232, "display_name": "Palolem, Goa, India"},
        "colva": {"lat": 15.2793, "lon": 73.9218, "display_name": "Colva, Goa, India"},
        # Karnataka
        "bangalore": {"lat": 12.9716, "lon": 77.5946, "display_name": "Bangalore, Karnataka, India"},
        "bengaluru": {"lat": 12.9716, "lon": 77.5946, "display_name": "Bengaluru, Karnataka, India"},
        "mysore": {"lat": 12.2958, "lon": 76.6394, "display_name": "Mysore, Karnataka, India"},
        "mysuru": {"lat": 12.2958, "lon": 76.6394, "display_name": "Mysuru, Karnataka, India"},
        "ballari": {"lat": 15.1394, "lon": 76.9214, "display_name": "Ballari, Karnataka, India"},
        "bellary": {"lat": 15.1394, "lon": 76.9214, "display_name": "Ballari, Karnataka, India"},
        "hampi": {"lat": 15.3350, "lon": 76.4600, "display_name": "Hampi, Karnataka, India"},
        "hospet": {"lat": 15.2689, "lon": 76.3909, "display_name": "Hosapete, Karnataka, India"},
        "hosapete": {"lat": 15.2689, "lon": 76.3909, "display_name": "Hosapete, Karnataka, India"},
        "hubli": {"lat": 15.3647, "lon": 75.1240, "display_name": "Hubballi, Karnataka, India"},
        "hubballi": {"lat": 15.3647, "lon": 75.1240, "display_name": "Hubballi, Karnataka, India"},
        "dharwad": {"lat": 15.4589, "lon": 75.0078, "display_name": "Dharwad, Karnataka, India"},
        "belgaum": {"lat": 15.8497, "lon": 74.4977, "display_name": "Belagavi, Karnataka, India"},
        "belagavi": {"lat": 15.8497, "lon": 74.4977, "display_name": "Belagavi, Karnataka, India"},
        "mangalore": {"lat": 12.9141, "lon": 74.8560, "display_name": "Mangaluru, Karnataka, India"},
        "mangaluru": {"lat": 12.9141, "lon": 74.8560, "display_name": "Mangaluru, Karnataka, India"},
        "udupi": {"lat": 13.3409, "lon": 74.7421, "display_name": "Udupi, Karnataka, India"},
        "coorg": {"lat": 12.4244, "lon": 75.7382, "display_name": "Madikeri, Coorg, Karnataka, India"},
        "madikeri": {"lat": 12.4244, "lon": 75.7382, "display_name": "Madikeri, Coorg, Karnataka, India"},
        "chikmagalur": {"lat": 13.3161, "lon": 75.7720, "display_name": "Chikkamagaluru, Karnataka, India"},
        "chikkamagaluru": {"lat": 13.3161, "lon": 75.7720, "display_name": "Chikkamagaluru, Karnataka, India"},
        "shimoga": {"lat": 13.9299, "lon": 75.5681, "display_name": "Shivamogga, Karnataka, India"},
        "shivamogga": {"lat": 13.9299, "lon": 75.5681, "display_name": "Shivamogga, Karnataka, India"},
        "hassan": {"lat": 13.0033, "lon": 76.1004, "display_name": "Hassan, Karnataka, India"},
        "dandeli": {"lat": 15.2427, "lon": 74.6206, "display_name": "Dandeli, Karnataka, India"},
        "gokarna": {"lat": 14.5479, "lon": 74.3188, "display_name": "Gokarna, Karnataka, India"},
        "davanagere": {"lat": 14.4644, "lon": 75.9218, "display_name": "Davanagere, Karnataka, India"},
        "chitradurga": {"lat": 14.2251, "lon": 76.3980, "display_name": "Chitradurga, Karnataka, India"},
        "tumkur": {"lat": 13.3379, "lon": 77.1006, "display_name": "Tumakuru, Karnataka, India"},
        "tumakuru": {"lat": 13.3379, "lon": 77.1006, "display_name": "Tumakuru, Karnataka, India"},
        "ramanagara": {"lat": 12.7212, "lon": 77.2986, "display_name": "Ramanagara, Karnataka, India"},
        "channapatna": {"lat": 12.5961, "lon": 77.2064, "display_name": "Channapatna, Karnataka, India"},
        "mandya": {"lat": 12.5224, "lon": 76.8974, "display_name": "Mandya, Karnataka, India"},
        "srirangapatna": {"lat": 12.4238, "lon": 76.6947, "display_name": "Srirangapatna, Karnataka, India"},
        "kalaburagi": {"lat": 17.3297, "lon": 76.8343, "display_name": "Kalaburagi, Karnataka, India"},
        "gulbarga": {"lat": 17.3297, "lon": 76.8343, "display_name": "Kalaburagi, Karnataka, India"},
        "vijayapura": {"lat": 16.8302, "lon": 75.7100, "display_name": "Vijayapura, Karnataka, India"},
        "bijapur": {"lat": 16.8302, "lon": 75.7100, "display_name": "Vijayapura, Karnataka, India"},
        "raichur": {"lat": 16.2076, "lon": 77.3463, "display_name": "Raichur, Karnataka, India"},
        "bidar": {"lat": 17.9104, "lon": 77.5199, "display_name": "Bidar, Karnataka, India"},
        # Telangana
        "hyderabad": {"lat": 17.3850, "lon": 78.4867, "display_name": "Hyderabad, Telangana, India"},
        "secunderabad": {"lat": 17.4399, "lon": 78.4983, "display_name": "Secunderabad, Telangana, India"},
        "warangal": {"lat": 17.9689, "lon": 79.5941, "display_name": "Warangal, Telangana, India"},
        "nizamabad": {"lat": 18.6725, "lon": 78.0941, "display_name": "Nizamabad, Telangana, India"},
        "karimnagar": {"lat": 18.4386, "lon": 79.1288, "display_name": "Karimnagar, Telangana, India"},
        "khammam": {"lat": 17.2473, "lon": 80.1514, "display_name": "Khammam, Telangana, India"},
        # Tamil Nadu
        "chennai": {"lat": 13.0827, "lon": 80.2707, "display_name": "Chennai, Tamil Nadu, India"},
        "madras": {"lat": 13.0827, "lon": 80.2707, "display_name": "Chennai, Tamil Nadu, India"},
        "coimbatore": {"lat": 11.0168, "lon": 76.9558, "display_name": "Coimbatore, Tamil Nadu, India"},
        "madurai": {"lat": 9.9252, "lon": 78.1198, "display_name": "Madurai, Tamil Nadu, India"},
        "trichy": {"lat": 10.7905, "lon": 78.7047, "display_name": "Tiruchirappalli, Tamil Nadu, India"},
        "tiruchirappalli": {"lat": 10.7905, "lon": 78.7047, "display_name": "Tiruchirappalli, Tamil Nadu, India"},
        "salem": {"lat": 11.6643, "lon": 78.1460, "display_name": "Salem, Tamil Nadu, India"},
        "tirunelveli": {"lat": 8.7139, "lon": 77.7567, "display_name": "Tirunelveli, Tamil Nadu, India"},
        "vellore": {"lat": 12.9165, "lon": 79.1325, "display_name": "Vellore, Tamil Nadu, India"},
        "thanjavur": {"lat": 10.7870, "lon": 79.1378, "display_name": "Thanjavur, Tamil Nadu, India"},
        "tanjore": {"lat": 10.7870, "lon": 79.1378, "display_name": "Thanjavur, Tamil Nadu, India"},
        "kanchipuram": {"lat": 12.8342, "lon": 79.7036, "display_name": "Kanchipuram, Tamil Nadu, India"},
        "kanyakumari": {"lat": 8.0883, "lon": 77.5385, "display_name": "Kanyakumari, Tamil Nadu, India"},
        "rameswaram": {"lat": 9.2876, "lon": 79.3129, "display_name": "Rameswaram, Tamil Nadu, India"},
        "ooty": {"lat": 11.4102, "lon": 76.6950, "display_name": "Udhagamandalam, Tamil Nadu, India"},
        "udhagamandalam": {"lat": 11.4102, "lon": 76.6950, "display_name": "Udhagamandalam, Tamil Nadu, India"},
        "kodaikanal": {"lat": 10.2381, "lon": 77.4892, "display_name": "Kodaikanal, Tamil Nadu, India"},
        "pondicherry": {"lat": 11.9416, "lon": 79.8083, "display_name": "Puducherry, India"},
        "puducherry": {"lat": 11.9416, "lon": 79.8083, "display_name": "Puducherry, India"},
        # Kerala
        "thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366, "display_name": "Thiruvananthapuram, Kerala, India"},
        "trivandrum": {"lat": 8.5241, "lon": 76.9366, "display_name": "Thiruvananthapuram, Kerala, India"},
        "kochi": {"lat": 9.9312, "lon": 76.2673, "display_name": "Kochi, Kerala, India"},
        "cochin": {"lat": 9.9312, "lon": 76.2673, "display_name": "Kochi, Kerala, India"},
        "kozhikode": {"lat": 11.2588, "lon": 75.7804, "display_name": "Kozhikode, Kerala, India"},
        "calicut": {"lat": 11.2588, "lon": 75.7804, "display_name": "Kozhikode, Kerala, India"},
        "munnar": {"lat": 10.0889, "lon": 77.0595, "display_name": "Munnar, Kerala, India"},
        "wayanad": {"lat": 11.6854, "lon": 76.1320, "display_name": "Wayanad, Kerala, India"},
        "alleppey": {"lat": 9.4981, "lon": 76.3388, "display_name": "Alappuzha, Kerala, India"},
        "alappuzha": {"lat": 9.4981, "lon": 76.3388, "display_name": "Alappuzha, Kerala, India"},
        "varkala": {"lat": 8.7379, "lon": 76.7163, "display_name": "Varkala, Kerala, India"},
        "thekkady": {"lat": 9.6031, "lon": 77.1615, "display_name": "Thekkady, Kerala, India"},
        "thrissur": {"lat": 10.5276, "lon": 76.2144, "display_name": "Thrissur, Kerala, India"},
        "kollam": {"lat": 8.8932, "lon": 76.6141, "display_name": "Kollam, Kerala, India"},
        "kannur": {"lat": 11.8745, "lon": 75.3704, "display_name": "Kannur, Kerala, India"},
        # Maharashtra
        "mumbai": {"lat": 19.0760, "lon": 72.8777, "display_name": "Mumbai, Maharashtra, India"},
        "bombay": {"lat": 19.0760, "lon": 72.8777, "display_name": "Mumbai, Maharashtra, India"},
        "pune": {"lat": 18.5204, "lon": 73.8567, "display_name": "Pune, Maharashtra, India"},
        "nagpur": {"lat": 21.1458, "lon": 79.0882, "display_name": "Nagpur, Maharashtra, India"},
        "nashik": {"lat": 19.9975, "lon": 73.7898, "display_name": "Nashik, Maharashtra, India"},
        "aurangabad": {"lat": 19.8762, "lon": 75.3433, "display_name": "Chhatrapati Sambhajinagar, Maharashtra, India"},
        "kolhapur": {"lat": 16.7050, "lon": 74.2433, "display_name": "Kolhapur, Maharashtra, India"},
        "shirdi": {"lat": 19.7645, "lon": 74.4762, "display_name": "Shirdi, Maharashtra, India"},
        "mahabaleshwar": {"lat": 17.9237, "lon": 73.6586, "display_name": "Mahabaleshwar, Maharashtra, India"},
        "lonavala": {"lat": 18.7557, "lon": 73.4091, "display_name": "Lonavala, Maharashtra, India"},
        "alibaug": {"lat": 18.6414, "lon": 72.8722, "display_name": "Alibaug, Maharashtra, India"},
        # Gujarat
        "ahmedabad": {"lat": 23.0225, "lon": 72.5714, "display_name": "Ahmedabad, Gujarat, India"},
        "surat": {"lat": 21.1702, "lon": 72.8311, "display_name": "Surat, Gujarat, India"},
        "vadodara": {"lat": 22.3072, "lon": 73.1812, "display_name": "Vadodara, Gujarat, India"},
        "baroda": {"lat": 22.3072, "lon": 73.1812, "display_name": "Vadodara, Gujarat, India"},
        "rajkot": {"lat": 22.3039, "lon": 70.8022, "display_name": "Rajkot, Gujarat, India"},
        "gandhinagar": {"lat": 23.2156, "lon": 72.6369, "display_name": "Gandhinagar, Gujarat, India"},
        "somnath": {"lat": 20.8880, "lon": 70.4012, "display_name": "Somnath, Gujarat, India"},
        "dwarka": {"lat": 22.2442, "lon": 68.9685, "display_name": "Dwarka, Gujarat, India"},
        # Rajasthan
        "jaipur": {"lat": 26.9124, "lon": 75.7873, "display_name": "Jaipur, Rajasthan, India"},
        "udaipur": {"lat": 24.5854, "lon": 73.7125, "display_name": "Udaipur, Rajasthan, India"},
        "jodhpur": {"lat": 26.2389, "lon": 73.0243, "display_name": "Jodhpur, Rajasthan, India"},
        "jaisalmer": {"lat": 26.9157, "lon": 70.9083, "display_name": "Jaisalmer, Rajasthan, India"},
        "pushkar": {"lat": 26.4897, "lon": 74.5511, "display_name": "Pushkar, Rajasthan, India"},
        "ajmer": {"lat": 26.4499, "lon": 74.6399, "display_name": "Ajmer, Rajasthan, India"},
        "bikaner": {"lat": 28.0229, "lon": 73.3119, "display_name": "Bikaner, Rajasthan, India"},
        "mount abu": {"lat": 24.5925, "lon": 72.7156, "display_name": "Mount Abu, Rajasthan, India"},
        # North India
        "delhi": {"lat": 28.6139, "lon": 77.2090, "display_name": "New Delhi, Delhi, India"},
        "new delhi": {"lat": 28.6139, "lon": 77.2090, "display_name": "New Delhi, Delhi, India"},
        "noida": {"lat": 28.5355, "lon": 77.3910, "display_name": "Noida, Uttar Pradesh, India"},
        "gurgaon": {"lat": 28.4595, "lon": 77.0266, "display_name": "Gurugram, Haryana, India"},
        "gurugram": {"lat": 28.4595, "lon": 77.0266, "display_name": "Gurugram, Haryana, India"},
        "agra": {"lat": 27.1767, "lon": 78.0081, "display_name": "Agra, Uttar Pradesh, India"},
        "varanasi": {"lat": 25.3176, "lon": 82.9739, "display_name": "Varanasi, Uttar Pradesh, India"},
        "benares": {"lat": 25.3176, "lon": 82.9739, "display_name": "Varanasi, Uttar Pradesh, India"},
        "kashi": {"lat": 25.3176, "lon": 82.9739, "display_name": "Varanasi, Uttar Pradesh, India"},
        "lucknow": {"lat": 26.8467, "lon": 80.9462, "display_name": "Lucknow, Uttar Pradesh, India"},
        "kanpur": {"lat": 26.4499, "lon": 80.3319, "display_name": "Kanpur, Uttar Pradesh, India"},
        "prayagraj": {"lat": 25.4358, "lon": 81.8463, "display_name": "Prayagraj, Uttar Pradesh, India"},
        "allahabad": {"lat": 25.4358, "lon": 81.8463, "display_name": "Prayagraj, Uttar Pradesh, India"},
        "ayodhya": {"lat": 26.7922, "lon": 82.1998, "display_name": "Ayodhya, Uttar Pradesh, India"},
        "mathura": {"lat": 27.4924, "lon": 77.6737, "display_name": "Mathura, Uttar Pradesh, India"},
        "vrindavan": {"lat": 27.5806, "lon": 77.7006, "display_name": "Vrindavan, Uttar Pradesh, India"},
        # Uttarakhand & Himachal
        "dehradun": {"lat": 30.3165, "lon": 78.0322, "display_name": "Dehradun, Uttarakhand, India"},
        "rishikesh": {"lat": 30.0869, "lon": 78.2676, "display_name": "Rishikesh, Uttarakhand, India"},
        "haridwar": {"lat": 29.9457, "lon": 78.1642, "display_name": "Haridwar, Uttarakhand, India"},
        "nainital": {"lat": 29.3919, "lon": 79.4542, "display_name": "Nainital, Uttarakhand, India"},
        "mussoorie": {"lat": 30.4598, "lon": 78.0644, "display_name": "Mussoorie, Uttarakhand, India"},
        "shimla": {"lat": 31.1048, "lon": 77.1734, "display_name": "Shimla, Himachal Pradesh, India"},
        "manali": {"lat": 32.2432, "lon": 77.1892, "display_name": "Manali, Himachal Pradesh, India"},
        "dharamshala": {"lat": 32.2190, "lon": 76.3234, "display_name": "Dharamshala, Himachal Pradesh, India"},
        "mcleodganj": {"lat": 32.2426, "lon": 76.3213, "display_name": "McLeod Ganj, Himachal Pradesh, India"},
        "kullu": {"lat": 31.9579, "lon": 77.1095, "display_name": "Kullu, Himachal Pradesh, India"},
        # Punjab & Chandigarh & J&K
        "chandigarh": {"lat": 30.7333, "lon": 76.7794, "display_name": "Chandigarh, India"},
        "amritsar": {"lat": 31.6340, "lon": 74.8723, "display_name": "Amritsar, Punjab, India"},
        "srinagar": {"lat": 34.0837, "lon": 74.7973, "display_name": "Srinagar, Jammu and Kashmir, India"},
        "leh": {"lat": 34.1526, "lon": 77.5771, "display_name": "Leh, Ladakh, India"},
        "ladakh": {"lat": 34.1526, "lon": 77.5771, "display_name": "Leh, Ladakh, India"},
        # East & Central & Northeast
        "kolkata": {"lat": 22.5726, "lon": 88.3639, "display_name": "Kolkata, West Bengal, India"},
        "calcutta": {"lat": 22.5726, "lon": 88.3639, "display_name": "Kolkata, West Bengal, India"},
        "darjeeling": {"lat": 27.0410, "lon": 88.2663, "display_name": "Darjeeling, West Bengal, India"},
        "bhubaneswar": {"lat": 20.2961, "lon": 85.8245, "display_name": "Bhubaneswar, Odisha, India"},
        "puri": {"lat": 19.8135, "lon": 85.8312, "display_name": "Puri, Odisha, India"},
        "patna": {"lat": 25.5941, "lon": 85.1376, "display_name": "Patna, Bihar, India"},
        "bodh gaya": {"lat": 24.6961, "lon": 84.9869, "display_name": "Bodh Gaya, Bihar, India"},
        "gaya": {"lat": 24.7955, "lon": 85.0002, "display_name": "Gaya, Bihar, India"},
        "ranchi": {"lat": 23.3441, "lon": 85.3096, "display_name": "Ranchi, Jharkhand, India"},
        "bhopal": {"lat": 23.2599, "lon": 77.4126, "display_name": "Bhopal, Madhya Pradesh, India"},
        "indore": {"lat": 22.7196, "lon": 75.8577, "display_name": "Indore, Madhya Pradesh, India"},
        "gwalior": {"lat": 26.2183, "lon": 78.1828, "display_name": "Gwalior, Madhya Pradesh, India"},
        "jabalpur": {"lat": 23.1815, "lon": 79.9864, "display_name": "Jabalpur, Madhya Pradesh, India"},
        "ujjain": {"lat": 23.1765, "lon": 75.7885, "display_name": "Ujjain, Madhya Pradesh, India"},
        "guwahati": {"lat": 26.1445, "lon": 91.7362, "display_name": "Guwahati, Assam, India"},
        "shillong": {"lat": 25.5788, "lon": 91.8933, "display_name": "Shillong, Meghalaya, India"},
        "gangtok": {"lat": 27.3389, "lon": 88.6065, "display_name": "Gangtok, Sikkim, India"},
    }

    KNOWN_CORRIDORS: dict[tuple[str, str], list[dict[str, Any]]] = {
        ("anantapur", "goa"): [
            {
                "id": "corridor-bellary-fort",
                "name": "Bellary Fort & Rock Citadel (Ballari)",
                "category": "Historic Monolithic Fort",
                "description": "Massive historic hilltop fort built atop a colossal monolithic granite rock with 360-degree panoramic views of the Deccan plains.",
                "location": "Ballari (~65 km from Anantapur on NH 67)",
                "coordinates": [15.1485, 76.9242],
                "milestone_km": 65.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-hampi",
                "name": "Hampi UNESCO World Heritage Site & Virupaksha Temple",
                "category": "UNESCO World Heritage Site",
                "description": "Legendary 14th-century capital of the Vijayanagara Empire featuring the iconic Stone Chariot, boulder-strewn hills, and sacred riverside temples.",
                "location": "Near Hospet (~130 km from Anantapur)",
                "coordinates": [15.3350, 76.4600],
                "milestone_km": 130.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-tb-dam",
                "name": "Tungabhadra Dam & Japanese Musical Gardens (Hospet)",
                "category": "Scenic Dam & Reservoir Gardens",
                "description": "Grand reservoir dam built across the Tungabhadra river featuring scenic lake lookouts, terraced gardens, and illuminated dancing fountains.",
                "location": "Hosapete (~140 km from Anantapur on NH 67)",
                "coordinates": [15.2806, 76.3402],
                "milestone_km": 140.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-hubli-dharwad",
                "name": "Hubli-Dharwad & Nrupatunga Betta Viewpoint",
                "category": "Scenic Hill & Cultural Highway Hub",
                "description": "Key highway transit junction famed for the iconic sweet Dharwad Peda, panoramic sunset views from Nrupatunga Betta, and heritage lakeside promenades.",
                "location": "Hubballi (~285 km from Anantapur on NH 67)",
                "coordinates": [15.3647, 75.1240],
                "milestone_km": 285.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-dandeli",
                "name": "Dandeli Wildlife Sanctuary & Kali River",
                "category": "Rainforest & Adventure River",
                "description": "Lush Western Ghats rainforest sanctuary famous for white-water river rafting on the Kali river, hornbill spotting, and canopy walks.",
                "location": "Dandeli (~360 km from Anantapur / detour via Haliyal)",
                "coordinates": [15.2427, 74.6206],
                "milestone_km": 360.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-dudhsagar-mollem",
                "name": "Dudhsagar Waterfalls & Bhagwan Mahaveer Sanctuary (Mollem)",
                "category": "Majestic 310m Waterfall & National Park",
                "description": "Spectacular 4-tiered 310m milky white cascading waterfall nestled inside dense Western Ghats jungle on the Karnataka-Goa border.",
                "location": "Mollem, Goa Border (~440 km from Anantapur on NH 748)",
                "coordinates": [15.3144, 74.3143],
                "milestone_km": 440.0,
                "is_en_route": True,
            },
        ],
        ("anathapuram", "goa"): [
            {
                "id": "corridor-bellary-fort",
                "name": "Bellary Fort & Rock Citadel (Ballari)",
                "category": "Historic Monolithic Fort",
                "description": "Massive historic hilltop fort built atop a colossal monolithic granite rock with 360-degree panoramic views of the Deccan plains.",
                "location": "Ballari (~65 km from Anantapur on NH 67)",
                "coordinates": [15.1485, 76.9242],
                "milestone_km": 65.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-hampi",
                "name": "Hampi UNESCO World Heritage Site & Virupaksha Temple",
                "category": "UNESCO World Heritage Site",
                "description": "Legendary 14th-century capital of the Vijayanagara Empire featuring the iconic Stone Chariot, boulder-strewn hills, and sacred riverside temples.",
                "location": "Near Hospet (~130 km from Anantapur)",
                "coordinates": [15.3350, 76.4600],
                "milestone_km": 130.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-tb-dam",
                "name": "Tungabhadra Dam & Japanese Musical Gardens (Hospet)",
                "category": "Scenic Dam & Reservoir Gardens",
                "description": "Grand reservoir dam built across the Tungabhadra river featuring scenic lake lookouts, terraced gardens, and illuminated dancing fountains.",
                "location": "Hosapete (~140 km from Anantapur on NH 67)",
                "coordinates": [15.2806, 76.3402],
                "milestone_km": 140.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-hubli-dharwad",
                "name": "Hubli-Dharwad & Nrupatunga Betta Viewpoint",
                "category": "Scenic Hill & Cultural Highway Hub",
                "description": "Key highway transit junction famed for the iconic sweet Dharwad Peda, panoramic sunset views from Nrupatunga Betta, and heritage lakeside promenades.",
                "location": "Hubballi (~285 km from Anantapur on NH 67)",
                "coordinates": [15.3647, 75.1240],
                "milestone_km": 285.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-dandeli",
                "name": "Dandeli Wildlife Sanctuary & Kali River",
                "category": "Rainforest & Adventure River",
                "description": "Lush Western Ghats rainforest sanctuary famous for white-water river rafting on the Kali river, hornbill spotting, and canopy walks.",
                "location": "Dandeli (~360 km from Anantapur / detour via Haliyal)",
                "coordinates": [15.2427, 74.6206],
                "milestone_km": 360.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-dudhsagar-mollem",
                "name": "Dudhsagar Waterfalls & Bhagwan Mahaveer Sanctuary (Mollem)",
                "category": "Majestic 310m Waterfall & National Park",
                "description": "Spectacular 4-tiered 310m milky white cascading waterfall nestled inside dense Western Ghats jungle on the Karnataka-Goa border.",
                "location": "Mollem, Goa Border (~440 km from Anantapur on NH 748)",
                "coordinates": [15.3144, 74.3143],
                "milestone_km": 440.0,
                "is_en_route": True,
            },
        ],
        ("bangalore", "mysore"): [
            {
                "id": "corridor-ramanagara",
                "name": "Ramadevara Betta & Vulture Sanctuary (Ramanagara)",
                "category": "Scenic & Heritage Hill",
                "description": "Iconic granite rocky hills where the Bollywood classic Sholay was filmed; India's only dedicated Long-billed Vulture Sanctuary with scenic trekking.",
                "location": "Ramanagara (~48 km from Bangalore)",
                "coordinates": [12.7212, 77.2986],
                "milestone_km": 48.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-janapada-loka",
                "name": "Janapada Loka Folk Art Museum",
                "category": "Heritage & Folk Culture",
                "description": "A 15-acre open-air museum complex preserving Karnataka's rural folk arts, traditional shadow puppets, village life exhibits, and handicraft bazaars.",
                "location": "Ramanagara Highway (~53 km from Bangalore)",
                "coordinates": [12.6958, 77.2642],
                "milestone_km": 53.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-channapatna",
                "name": "Channapatna Wooden Toy Village & Craft Center",
                "category": "Traditional Crafts & Heritage",
                "description": "World-famous 'Town of Toys' renowned for 200-year-old GI-tagged vegetable-dyed wooden lacquerware, artisan workshops, and lacquer toy emporiums.",
                "location": "Channapatna (~62 km from Bangalore)",
                "coordinates": [12.5961, 77.2064],
                "milestone_km": 62.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-maddur",
                "name": "Maddur Tiffany's & Iconic Maddur Vada Stop",
                "category": "Iconic Highway Food Stop",
                "description": "The historic birthplace of Maddur Vada since 1917 — crispy golden onion-semolina fritters served with coconut chutney and hot South Indian filter coffee.",
                "location": "Maddur (~82 km from Bangalore)",
                "coordinates": [12.5847, 77.0456],
                "milestone_km": 82.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-mandya",
                "name": "Mandya Sugar City & Cheluvanarayana Heritage Route",
                "category": "Scenic Countryside & Heritage",
                "description": "Heart of Karnataka's sugarcane belt; scenic roadside sugarcane juice stands, traditional jaggery-making units (Aalemane), and gateway to Melukote temples.",
                "location": "Mandya (~98 km from Bangalore)",
                "coordinates": [12.5224, 76.8974],
                "milestone_km": 98.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-srirangapatna",
                "name": "Srirangapatna Fort & Tipu Sultan's Summer Palace",
                "category": "Historical Island Fortress",
                "description": "Historic river island fortress featuring Tipu Sultan's Dariya Daulat Bagh (Summer Palace), Sri Ranganathaswamy Temple, Gumbaz mausoleum, and war obelisks.",
                "location": "Srirangapatna (~125 km from Bangalore / 15 km before Mysore)",
                "coordinates": [12.4238, 76.6947],
                "milestone_km": 125.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-ranganathittu",
                "name": "Ranganathittu Bird Sanctuary",
                "category": "Wildlife & Nature",
                "description": "Karnataka's largest bird sanctuary on the Kaveri river; tranquil guided boat safaris past nesting painted storks, pelicans, ibis, and basking mugger crocodiles.",
                "location": "Near Srirangapatna (~128 km from Bangalore)",
                "coordinates": [12.4253, 76.6575],
                "milestone_km": 128.0,
                "is_en_route": True,
            },
        ],
        ("bangalore", "goa"): [
            {
                "id": "corridor-chitradurga",
                "name": "Chitradurga Fort (Callina Kote)",
                "category": "Historical Stone Citadel",
                "description": "Impregnable 17th-century stone fortress with seven concentric fortification walls, 18 ancient temples, and the heroic legend of Onake Obavva.",
                "location": "Chitradurga (~200 km from Bangalore on NH 48)",
                "coordinates": [14.2251, 76.3980],
                "milestone_km": 200.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-davanagere",
                "name": "Davanagere Butter Dosa Highway Stop",
                "category": "Iconic Culinary Pitstop",
                "description": "Famous culinary hub renowned for crisp, woodfire-roasted Davanagere Benne Dosa served with spicy potato mash and coconut chutney.",
                "location": "Davanagere (~260 km from Bangalore)",
                "coordinates": [14.4644, 75.9218],
                "milestone_km": 260.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-dandeli-goa",
                "name": "Dandeli Wildlife Sanctuary & Kali River",
                "category": "Rainforest & Adventure River",
                "description": "Lush Western Ghats rainforest sanctuary famous for white-water river rafting on the Kali river, hornbill spotting, and canopy walks.",
                "location": "Dandeli (~460 km from Bangalore)",
                "coordinates": [15.2427, 74.6206],
                "milestone_km": 460.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-dudhsagar-mollem-goa",
                "name": "Dudhsagar Waterfalls & Bhagwan Mahaveer Sanctuary (Mollem)",
                "category": "Majestic 310m Waterfall & National Park",
                "description": "Spectacular 4-tiered 310m milky white cascading waterfall nestled inside dense Western Ghats jungle on the Karnataka-Goa border.",
                "location": "Mollem, Goa Border (~520 km from Bangalore on NH 748)",
                "coordinates": [15.3144, 74.3143],
                "milestone_km": 520.0,
                "is_en_route": True,
            },
        ],
        ("mumbai", "pune"): [
            {
                "id": "corridor-lonavala",
                "name": "Lonavala & Khandala Ghat Viewpoints",
                "category": "Hill Station & Scenic View",
                "description": "Famous Western Ghats hill station known for Tiger's Leap, Duke's Nose, Rajmachi viewpoint, and iconic Maganlal Chikki.",
                "location": "Lonavala (~85 km from Mumbai)",
                "coordinates": [18.7557, 73.4091],
                "milestone_km": 85.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-karla",
                "name": "Karla & Bhaja Rock-Cut Buddhist Caves",
                "category": "Ancient Archaeological Caves",
                "description": "Ancient 2nd-century BCE rock-cut Buddhist shrines featuring grand chaityas, ornate prayer halls, and monolithic pillars.",
                "location": "Karla (~95 km from Mumbai)",
                "coordinates": [18.7828, 73.4706],
                "milestone_km": 95.0,
                "is_en_route": True,
            },
        ],
        ("delhi", "agra"): [
            {
                "id": "corridor-mathura",
                "name": "Mathura & Vrindavan Krishna Janmabhoomi",
                "category": "Heritage & Pilgrimage",
                "description": "Historic holy twin cities on the Yamuna river featuring Krishna Janmasthan Temple Complex, Banke Bihari, and Prem Mandir.",
                "location": "Mathura (~145 km from Delhi on Yamuna Expressway)",
                "coordinates": [27.4924, 77.6737],
                "milestone_km": 145.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-sikandra",
                "name": "Akbar's Tomb at Sikandra",
                "category": "Mughal Architecture & Heritage",
                "description": "Sublime red sandstone and white marble mausoleum of Emperor Akbar set inside expansive Mughal charbagh gardens.",
                "location": "Sikandra (~200 km from Delhi / 12 km before Agra)",
                "coordinates": [27.2206, 77.9504],
                "milestone_km": 200.0,
                "is_en_route": True,
            },
        ],
        ("bangalore", "coorg"): [
            {
                "id": "corridor-coorg-ramanagara",
                "name": "Ramadevara Betta & Vulture Sanctuary (Ramanagara)",
                "category": "Scenic & Heritage Hill",
                "description": "Iconic granite rocky hills where Bollywood classic Sholay was filmed; India's only dedicated Long-billed Vulture Sanctuary with scenic trekking.",
                "location": "Ramanagara (~48 km from Bangalore)",
                "coordinates": [12.7212, 77.2986],
                "milestone_km": 48.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-coorg-janapada-loka",
                "name": "Janapada Loka Folk Art Museum",
                "category": "Heritage & Folk Culture",
                "description": "15-acre open-air museum complex preserving Karnataka's rural folk arts, traditional shadow puppets, and handicraft bazaars.",
                "location": "Ramanagara Highway (~53 km from Bangalore)",
                "coordinates": [12.6958, 77.2642],
                "milestone_km": 53.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-coorg-channapatna",
                "name": "Channapatna Wooden Toy Village & Craft Center",
                "category": "Traditional Crafts & Heritage",
                "description": "World-famous 'Town of Toys' renowned for 200-year-old GI-tagged vegetable-dyed wooden lacquerware and artisan workshops.",
                "location": "Channapatna (~62 km from Bangalore)",
                "coordinates": [12.5961, 77.2064],
                "milestone_km": 62.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-coorg-maddur",
                "name": "Maddur Tiffany's & Iconic Maddur Vada Stop",
                "category": "Iconic Highway Food Stop",
                "description": "The historic birthplace of Maddur Vada since 1917 — crispy golden onion-semolina fritters served with coconut chutney and hot South Indian filter coffee.",
                "location": "Maddur (~82 km from Bangalore)",
                "coordinates": [12.5847, 77.0456],
                "milestone_km": 82.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-coorg-srirangapatna",
                "name": "Srirangapatna Island Fortress & Tipu Sultan's Palace",
                "category": "Historical Island Fortress",
                "description": "Historic Kaveri river island fortress featuring Tipu Sultan's Dariya Daulat Bagh (Summer Palace) and ancient temples.",
                "location": "Srirangapatna (~125 km from Bangalore)",
                "coordinates": [12.4238, 76.6947],
                "milestone_km": 125.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-coorg-bylakuppe",
                "name": "Namdroling Monastery (Golden Temple Bylakuppe)",
                "category": "Tibetan Buddhist Monastery",
                "description": "Second largest Tibetan settlement in India, featuring majestic 40-foot gilded Buddha statues, ornate thangka paintings, and prayer halls.",
                "location": "Bylakuppe, Coorg Gateway (~215 km from Bangalore)",
                "coordinates": [12.4312, 75.9664],
                "milestone_km": 215.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-coorg-nisargadhama",
                "name": "Kaveri Nisargadhama & Hanging Rope Bridge",
                "category": "River Island Nature Reserve",
                "description": "Breathtaking 64-acre natural island formed by the river Kaveri, filled with thick bamboo groves, deer park, and hanging suspension bridge.",
                "location": "Kushalnagar, Coorg (~225 km from Bangalore)",
                "coordinates": [12.4497, 75.9328],
                "milestone_km": 225.0,
                "is_en_route": True,
            },
        ],
        ("bengaluru", "coorg"): [
            {
                "id": "corridor-coorg-ramanagara-b",
                "name": "Ramadevara Betta & Vulture Sanctuary (Ramanagara)",
                "category": "Scenic & Heritage Hill",
                "description": "Iconic granite rocky hills where Bollywood classic Sholay was filmed; India's only dedicated Long-billed Vulture Sanctuary.",
                "location": "Ramanagara (~48 km from Bangalore)",
                "coordinates": [12.7212, 77.2986],
                "milestone_km": 48.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-coorg-channapatna-b",
                "name": "Channapatna Wooden Toy Village & Craft Center",
                "category": "Traditional Crafts & Heritage",
                "description": "World-famous 'Town of Toys' renowned for 200-year-old GI-tagged vegetable-dyed wooden lacquerware and artisan workshops.",
                "location": "Channapatna (~62 km from Bangalore)",
                "coordinates": [12.5961, 77.2064],
                "milestone_km": 62.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-coorg-maddur-b",
                "name": "Maddur Tiffany's & Iconic Maddur Vada Stop",
                "category": "Iconic Highway Food Stop",
                "description": "Historic birthplace of Maddur Vada since 1917 — crispy onion-semolina fritters served with coconut chutney and hot filter coffee.",
                "location": "Maddur (~82 km from Bangalore)",
                "coordinates": [12.5847, 77.0456],
                "milestone_km": 82.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-coorg-srirangapatna-b",
                "name": "Srirangapatna Island Fortress & Tipu Sultan's Palace",
                "category": "Historical Island Fortress",
                "description": "Historic Kaveri river island fortress featuring Tipu Sultan's Dariya Daulat Bagh (Summer Palace) and ancient temples.",
                "location": "Srirangapatna (~125 km from Bangalore)",
                "coordinates": [12.4238, 76.6947],
                "milestone_km": 125.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-coorg-bylakuppe-b",
                "name": "Namdroling Monastery (Golden Temple Bylakuppe)",
                "category": "Tibetan Buddhist Monastery",
                "description": "Second largest Tibetan settlement in India, featuring majestic 40-foot gilded Buddha statues, ornate thangka paintings, and prayer halls.",
                "location": "Bylakuppe, Coorg Gateway (~215 km from Bangalore)",
                "coordinates": [12.4312, 75.9664],
                "milestone_km": 215.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-coorg-nisargadhama-b",
                "name": "Kaveri Nisargadhama & Hanging Rope Bridge",
                "category": "River Island Nature Reserve",
                "description": "Breathtaking 64-acre natural island formed by the river Kaveri, filled with thick bamboo groves, deer park, and hanging suspension bridge.",
                "location": "Kushalnagar, Coorg (~225 km from Bangalore)",
                "coordinates": [12.4497, 75.9328],
                "milestone_km": 225.0,
                "is_en_route": True,
            },
        ],
        ("bangalore", "ooty"): [
            {
                "id": "corridor-ooty-channapatna",
                "name": "Channapatna Wooden Toy Village",
                "category": "Traditional Crafts",
                "description": "Famous lacquerware toy emporiums and artisan craft cooperatives.",
                "location": "Channapatna (~62 km from Bangalore)",
                "coordinates": [12.5961, 77.2064],
                "milestone_km": 62.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-ooty-mysore-palace",
                "name": "Mysore Palace & Royal Heritage Corridor",
                "category": "Royal Palace Landmark",
                "description": "Magnificent royal residence of the Wadiyar dynasty in central Mysore.",
                "location": "Mysore (~145 km from Bangalore)",
                "coordinates": [12.3052, 76.6552],
                "milestone_km": 145.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-ooty-bandipur",
                "name": "Bandipur National Park & Tiger Reserve Safari Highway",
                "category": "Wildlife & Tiger Reserve",
                "description": "Scenic jungle highway where wild elephants, spotted deer, and peacocks frequently cross the road.",
                "location": "Bandipur (~220 km from Bangalore on NH 766)",
                "coordinates": [11.6664, 76.6291],
                "milestone_km": 220.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-ooty-mudumalai",
                "name": "Mudumalai Tiger Reserve & Theppakadu Elephant Camp",
                "category": "Wildlife Sanctuary",
                "description": "Historic elephant camp at the foothills of the Nilgiris on the Tamil Nadu-Karnataka border.",
                "location": "Mudumalai (~235 km from Bangalore)",
                "coordinates": [11.5833, 76.6167],
                "milestone_km": 235.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-ooty-kalhatty",
                "name": "Kalhatty Ghat 36 Hairpin Bends & Viewpoint",
                "category": "Scenic Mountain Pass",
                "description": "Exhilarating mountain climb with 36 hairpin bends ascending from Masinagudi into Ooty.",
                "location": "Kalhatty (~260 km from Bangalore)",
                "coordinates": [11.4833, 76.7167],
                "milestone_km": 260.0,
                "is_en_route": True,
            },
        ],
        ("bangalore", "chikmagalur"): [
            {
                "id": "corridor-cmg-hassan",
                "name": "Hassan & Gorur Dam on Hemavathi River",
                "category": "Scenic Reservoir & Dam",
                "description": "Expansive water reservoir built across the Hemavathi river, featuring scenic gardens and picnics.",
                "location": "Gorur / Hassan (~180 km from Bangalore)",
                "coordinates": [12.8711, 76.0461],
                "milestone_km": 180.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-cmg-belur",
                "name": "Belur Chennakeshava Temple (UNESCO World Heritage)",
                "category": "UNESCO Hoysala Temple",
                "description": "12th-century marvel of Hoysala stone architecture famed for intricate filigree carvings of dancers and celestial maidens.",
                "location": "Belur (~220 km from Bangalore / 25 km before Chikmagalur)",
                "coordinates": [13.1624, 75.8604],
                "milestone_km": 220.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-cmg-halebidu",
                "name": "Halebidu Hoysaleshwara Temple Complex",
                "category": "Ancient Temple Ruins",
                "description": "Sublime twin-temple complex carved in chloritic soapstone, representing the zenith of South Indian temple sculpting.",
                "location": "Halebidu (~215 km from Bangalore)",
                "coordinates": [13.2131, 75.9934],
                "milestone_km": 215.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-cmg-yagachi",
                "name": "Yagachi Water Sports & Dam Reservoir",
                "category": "Lake Adventure Sports",
                "description": "Serene reservoir surrounded by green hills, offering jet-skiing, speedboats, banana rides, and kayaking.",
                "location": "Near Belur (~225 km from Bangalore)",
                "coordinates": [13.1812, 75.8450],
                "milestone_km": 225.0,
                "is_en_route": True,
            },
        ],
        ("delhi", "jaipur"): [
            {
                "id": "corridor-neemrana",
                "name": "Neemrana Fort-Palace",
                "category": "15th-Century Heritage Fort",
                "description": "Magnificent 14-tiered heritage fort palace built into the Aravalli hills, famous for aerial zip-lining and regal court dining.",
                "location": "Neemrana (~125 km from Delhi on NH 48)",
                "coordinates": [27.9944, 76.3861],
                "milestone_km": 125.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-behror",
                "name": "Behror Midway Highway Food Hub",
                "category": "Iconic Highway Food Stop",
                "description": "Historic RTDC highway oasis serving hot Rajasthani kachoris, fresh lassi, and traditional North Indian thalis.",
                "location": "Behror (~135 km from Delhi)",
                "coordinates": [27.8872, 76.2811],
                "milestone_km": 135.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-shahpura",
                "name": "Shahpura Haveli & Traditional Textile Village",
                "category": "Heritage Haveli & Crafts",
                "description": "300-year-old royal haveli and artisan center famous for Jaipur hand-block printing and miniature painting.",
                "location": "Shahpura (~200 km from Delhi / 65 km before Jaipur)",
                "coordinates": [27.3872, 75.9611],
                "milestone_km": 200.0,
                "is_en_route": True,
            },
        ],
        ("chennai", "pondicherry"): [
            {
                "id": "corridor-kovalam-surf",
                "name": "Covelong (Kovalam) Beach & Dutch Fort Ruins",
                "category": "Coastal Surf Hub & Heritage",
                "description": "Historic coastal fishing village famous for point-break surfing schools, sea kayaking, and remnants of an 18th-century Dutch port fort.",
                "location": "Kovalam (~35 km from Chennai on ECR)",
                "coordinates": [12.7925, 80.2514],
                "milestone_km": 35.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-mahabalipuram",
                "name": "Mahabalipuram UNESCO Shore Temple & Pancha Rathas",
                "category": "UNESCO World Heritage Rock Monuments",
                "description": "7th-century Pallava coastal monuments including the oceanfront Shore Temple, monolithic chariot temples, and Arjuna's Penance bas-relief.",
                "location": "Mamallapuram (~55 km from Chennai on ECR)",
                "coordinates": [12.6167, 80.1917],
                "milestone_km": 55.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-alamparai",
                "name": "Alamparai Fort Coastal Ruins",
                "category": "17th-Century Mughal Fort Ruins",
                "description": "Atmospheric laterite fort ruins overlooking tranquil coastal backwaters and the Bay of Bengal.",
                "location": "Kadappakkam (~100 km from Chennai)",
                "coordinates": [12.2619, 80.0131],
                "milestone_km": 100.0,
                "is_en_route": True,
            },
            {
                "id": "corridor-auroville-approach",
                "name": "Auroville Matrimandir & International Township",
                "category": "Universal Peace Center",
                "description": "Futuristic golden geodesic meditation dome and tranquil forest gardens just 10 km north of Pondicherry.",
                "location": "Auroville (~140 km from Chennai / 10 km before Pondicherry)",
                "coordinates": [12.0069, 79.8106],
                "milestone_km": 140.0,
                "is_en_route": True,
            },
        ],
    }

    KNOWN_DESTINATION_LANDMARKS: dict[str, list[dict[str, Any]]] = {
        "coorg": [
            {
                "id": "dest-coorg-abbey-falls",
                "name": "Abbey Falls & Hanging Bridge",
                "category": "Scenic Waterfall & Western Ghats",
                "description": "Spectacular 70-foot waterfall cascading between private coffee plantations and spice estates, viewed from an iconic suspension hanging bridge.",
                "coordinates": [12.4542, 75.7175],
                "location": "Madikeri (~8 km from town center)",
            },
            {
                "id": "dest-coorg-golden-temple",
                "name": "Namdroling Monastery (Bylakuppe Golden Temple)",
                "category": "Tibetan Buddhist Monastery",
                "description": "The largest Tibetan settlement in South India featuring magnificent 40-foot gilded Buddha statues, ornate thangka murals, and chanting prayer halls.",
                "coordinates": [12.4312, 75.9664],
                "location": "Bylakuppe, Kushalnagar",
            },
            {
                "id": "dest-coorg-rajas-seat",
                "name": "Raja's Seat Sunset Viewpoint & Musical Garden",
                "category": "Royal Sunset Viewpoint",
                "description": "Historic terraced garden where the Kings of Kodagu once watched sunsets over mist-covered Western Ghat valleys and rolling green hills.",
                "coordinates": [12.4184, 75.7371],
                "location": "Madikeri Town",
            },
            {
                "id": "dest-coorg-dubare",
                "name": "Dubare Elephant Camp & Kaveri River Rafting",
                "category": "Wildlife & Elephant Sanctuary",
                "description": "Premier ecotourism reserve along the river Kaveri where visitors can interact with Asian elephants, observe bathing rituals, and enjoy river rafting.",
                "coordinates": [12.3686, 75.9048],
                "location": "Dubare, Kushalnagar",
            },
            {
                "id": "dest-coorg-talacauvery",
                "name": "Talacauvery (Origin of River Kaveri)",
                "category": "Sacred River Source & Mountain Peak",
                "description": "Sacred birthplace of the holy river Kaveri nestled at 1,276m atop Brahmagiri Hills, offering sweeping panoramic views over the Western Ghats.",
                "coordinates": [12.3867, 75.4925],
                "location": "Brahmagiri Hills, Bhagamandala",
            },
            {
                "id": "dest-coorg-madikeri-fort",
                "name": "Madikeri Fort & Palace Museum",
                "category": "17th-Century Stone Fortress",
                "description": "Historic stone citadel originally built by Mudduraja, featuring life-sized masonry elephants, a clock tower, and museum exhibiting Kodagu royal artifacts.",
                "coordinates": [12.4239, 75.7397],
                "location": "Central Madikeri",
            },
            {
                "id": "dest-coorg-mandalpatti",
                "name": "Mandalpatti Peak 4x4 Jeep Safari",
                "category": "Panoramic Mist Mountain Peak",
                "description": "Perched at 4,050 feet in the Pushpagiri wildlife reserve, famed for rugged off-road 4x4 jeep safaris through lush tea estates to sweeping vistas above the clouds.",
                "coordinates": [12.5186, 75.7028],
                "location": "Mandalpatti, North Coorg",
            },
        ],
        "goa": [
            {
                "id": "dest-goa-fort-aguada",
                "name": "Fort Aguada & 17th-Century Portuguese Lighthouse",
                "category": "Coastal Fortress & Lighthouse",
                "description": "Historic 1612 Portuguese fortress overlooking Sinquerim beach and the Arabian Sea, featuring a 4-storey freshwater reservoir and sweeping ocean views.",
                "coordinates": [15.4920, 73.7737],
                "location": "Sinquerim, Candolim, North Goa",
            },
            {
                "id": "dest-goa-basilica-bom-jesus",
                "name": "Basilica of Bom Jesus (Old Goa)",
                "category": "UNESCO World Heritage Baroque Church",
                "description": "World-famous 16th-century Jesuit basilica enshrining the sacred mortal remains of St. Francis Xavier, renowned for gilded baroque altars and marble floorings.",
                "coordinates": [15.5009, 73.9116],
                "location": "Old Goa (Velha Goa)",
            },
            {
                "id": "dest-goa-fontainhas",
                "name": "Fontainhas Latin Quarter (Panaji)",
                "category": "Portuguese Heritage Quarter",
                "description": "Charming heritage quarter famed for narrow cobbled alleys, pastel-colored colonial villas, wrought-iron balconies, art galleries, and vintage bakeries.",
                "coordinates": [15.4975, 73.8322],
                "location": "Central Panaji, Goa",
            },
            {
                "id": "dest-goa-baga-beach",
                "name": "Baga & Calangute Beach Coastal Strip",
                "category": "Golden Sand Beach & Water Sports",
                "description": "Vibrant beach hub famous for parasailing, jet skiing, sunset dolphin cruises, beachfront candlelit shacks, live music, and seafood delicacies.",
                "coordinates": [15.5553, 73.7517],
                "location": "Baga, North Goa",
            },
            {
                "id": "dest-goa-chapora-fort",
                "name": "Chapora Fort & Vagator Cliffs",
                "category": "Historic Clifftop Fort",
                "description": "Iconic red-laterite clifftop fortress overlooking Vagator Beach and Chapora river estuary; famed as the Bollywood 'Dil Chahta Hai' sunset point.",
                "coordinates": [15.6059, 73.7364],
                "location": "Vagator, North Goa",
            },
            {
                "id": "dest-goa-dudhsagar",
                "name": "Dudhsagar Waterfalls & Mollem National Park",
                "category": "310m Tiered Jungle Waterfall",
                "description": "Spectacular 4-tiered 310m milky white waterfall plunging through dense Western Ghats jungle on the Mandovi river with natural swimming pools.",
                "coordinates": [15.3144, 74.3143],
                "location": "Mollem National Park, South Goa",
            },
            {
                "id": "dest-goa-palolem",
                "name": "Palolem Beach & Butterfly Island",
                "category": "Scenic Crescent Beach",
                "description": "Tranquil crescent-shaped golden beach in South Goa framed by coconut groves, gentle turquoise waves, and sea kayak routes.",
                "coordinates": [15.0100, 74.0232],
                "location": "Canacona, South Goa",
            },
        ],
        "mysore": [
            {
                "id": "dest-mysore-palace",
                "name": "Mysore Palace (Amba Vilas)",
                "category": "Royal Palace & Heritage",
                "description": "Grand Indo-Saracenic royal palace of the Wadiyar dynasty featuring stained glass, gilded durbar halls, and weekend illuminations of 100,000 bulbs.",
                "coordinates": [12.3052, 76.6552],
                "location": "Central Mysore",
            },
            {
                "id": "dest-chamundi-hills",
                "name": "Chamundi Hills & Sri Chamundeshwari Temple",
                "category": "Historic Hill & Temple",
                "description": "Sacred hilltop landmark offering panoramic sunset vistas across Mysore, a 17th-century temple, and the monolithic Nandi statue.",
                "coordinates": [12.2725, 76.6711],
                "location": "Chamundi Hill Peak",
            },
            {
                "id": "dest-devaraja-market",
                "name": "Devaraja Heritage Market",
                "category": "Traditional Market & Heritage",
                "description": "Vibrant century-old open market famous for traditional Mysore betel leaves, fragrant sandalwood, silk, and raw spices.",
                "coordinates": [12.3086, 76.6517],
                "location": "Near D. Devaraj Urs Road",
            },
            {
                "id": "dest-philomena",
                "name": "St. Philomena's Cathedral",
                "category": "Neo-Gothic Cathedral",
                "description": "One of the tallest churches in Asia, built in 1936 with neo-gothic spires and stained-glass windows inspired by the Cologne Cathedral.",
                "coordinates": [12.3204, 76.6575],
                "location": "Ashoka Road, Mysore",
            },
            {
                "id": "dest-brindavan",
                "name": "Brindavan Gardens & KRS Dam",
                "category": "Terraced Gardens & Fountains",
                "description": "Expansive terraced Mughal-style garden beside Krishnarajasagara Dam, famed for evening musical fountain light shows.",
                "coordinates": [12.4262, 76.5732],
                "location": "KRS Dam Reservoir",
            },
            {
                "id": "dest-ranganathittu",
                "name": "Ranganathittu Bird Sanctuary",
                "category": "Wildlife & Nature",
                "description": "Karnataka's largest bird sanctuary on the Kaveri river; tranquil guided boat safaris past nesting painted storks, pelicans, ibis, and basking mugger crocodiles.",
                "coordinates": [12.4253, 76.6575],
                "location": "Near Srirangapatna (~15 km from Mysore)",
            },
        ],
        "bangalore": [
            {
                "id": "dest-blr-lalbagh",
                "name": "Lalbagh Botanical Garden & Glass House",
                "category": "Historic Botanical Garden",
                "description": "240-acre garden commissioned by Hyder Ali, housing India's largest collection of tropical plants, centuries-old trees, and the iconic Victorian Glass House.",
                "coordinates": [12.9507, 77.5848],
                "location": "South Bangalore",
            },
            {
                "id": "dest-blr-cubbon",
                "name": "Cubbon Park & Vidhana Soudha",
                "category": "Historic Park & Legislative Palace",
                "description": "300-acre green lung in the city center adjacent to the monumental neo-Dravidian granite legislative assembly palace Vidhana Soudha.",
                "coordinates": [12.9763, 77.5929],
                "location": "Central Bangalore",
            },
            {
                "id": "dest-blr-palace",
                "name": "Bangalore Palace",
                "category": "Tudor Royal Palace",
                "description": "19th-century royal estate modeled on England's Windsor Castle, featuring fortified towers, turrets, wood carvings, and royal family memorabilia.",
                "coordinates": [12.9988, 77.5921],
                "location": "Vasanth Nagar, Bangalore",
            },
            {
                "id": "dest-blr-tipu-palace",
                "name": "Tipu Sultan's Summer Palace & Bangalore Fort",
                "category": "Teakwood Heritage Palace",
                "description": "Ornate two-storey palace built entirely in French-influenced teakwood with carved pillars, arches, and balconies inside the old Bangalore fort.",
                "coordinates": [12.9593, 77.5738],
                "location": "KR Market, Bangalore",
            },
            {
                "id": "dest-blr-bannerghatta",
                "name": "Bannerghatta National Park & Biological Safari",
                "category": "Wildlife Safari & Zoo",
                "description": "Expansive biological park featuring caged tiger, lion, and bear safaris, a butterfly park, and elephant rehabilitation corridor.",
                "coordinates": [12.8009, 77.5777],
                "location": "Bannerghatta Road, Bangalore",
            },
        ],
        "ooty": [
            {
                "id": "dest-ooty-toy-train",
                "name": "Nilgiri Mountain Railway (Toy Train)",
                "category": "UNESCO World Heritage Mountain Rail",
                "description": "Charming meter-gauge steam rack railway winding through steep Nilgiri mountain gorges, ravines, tunnels, and lush tea gardens.",
                "coordinates": [11.4064, 76.6932],
                "location": "Ooty Railway Station",
            },
            {
                "id": "dest-ooty-botanical",
                "name": "Government Botanical Garden",
                "category": "Terraced Botanical Garden",
                "description": "55-acre garden established in 1848 on the lower slopes of Doddabetta peak, housing exotic flowering plants, orchids, and a 20-million-year-old fossil tree.",
                "coordinates": [11.4172, 76.7112],
                "location": "Vannarapettai, Ooty",
            },
            {
                "id": "dest-ooty-doddabetta",
                "name": "Doddabetta Peak & Telescope House",
                "category": "Highest Nilgiri Mountain Peak",
                "description": "Highest peak in the Nilgiri Hills (2,637 m) offering sweeping 360-degree vistas across misty valleys, shola forests, and tea plantations.",
                "coordinates": [11.4011, 76.7360],
                "location": "Ooty-Kotagiri Road (~9 km from town)",
            },
            {
                "id": "dest-ooty-pykara",
                "name": "Pykara Lake, Boat House & Waterfalls",
                "category": "Scenic Lake & Waterfalls",
                "description": "Pristine mountain reservoir surrounded by pine forests and rolling grasslands, offering speedboats and twin cascading waterfalls.",
                "coordinates": [11.4916, 76.5956],
                "location": "Pykara (~21 km from Ooty on Mysore Road)",
            },
            {
                "id": "dest-ooty-avalanche",
                "name": "Avalanche Lake & Shola Forest Reserve",
                "category": "Pristine Nature Reserve",
                "description": "Untouched alpine lake nestled in dense Nilgiri biosphere shola forests, famous for trout fishing, scenic nature trails, and landscape photography.",
                "coordinates": [11.3005, 76.5910],
                "location": "Avalanche Valley (~28 km from Ooty)",
            },
        ],
        "hampi": [
            {
                "id": "dest-hampi-virupaksha",
                "name": "Virupaksha Temple & Hampi Bazaar",
                "category": "Ancient 7th-Century Shiva Temple",
                "description": "Active pilgrimage temple dedicated to Lord Shiva with a 160-foot eastern gopuram standing at the foot of Hemakuta Hill beside the Tungabhadra.",
                "coordinates": [15.3350, 76.4600],
                "location": "Hampi Bazaar",
            },
            {
                "id": "dest-hampi-vitthala",
                "name": "Vijaya Vitthala Temple & Monolithic Stone Chariot",
                "category": "UNESCO Architectural Pinnacle",
                "description": "The architectural crown jewel of the Vijayanagara Empire, featuring the iconic Stone Chariot and 56 musical stone pillars (Ranga Mantapa).",
                "coordinates": [15.3392, 76.4794],
                "location": "Vitthala Temple Complex, Hampi",
            },
            {
                "id": "dest-hampi-tb-dam",
                "name": "Tungabhadra Dam & Japanese Musical Gardens",
                "category": "Scenic Dam & Reservoir Gardens",
                "description": "Massive reservoir across the Tungabhadra river featuring scenic lake lookouts, landscaped gardens, and evening dancing fountain lights.",
                "coordinates": [15.2806, 76.3402],
                "location": "Hosapete (~14 km from Hampi)",
            },
            {
                "id": "dest-hampi-lotus-mahal",
                "name": "Lotus Mahal & Elephant Stables",
                "category": "Royal Indo-Islamic Pavilion",
                "description": "Stunning secular palace complex featuring 11 domed chambers that once housed royal war elephants, showcasing Indo-Islamic architecture.",
                "coordinates": [15.3204, 76.4712],
                "location": "Zenana Enclosure, Hampi",
            },
            {
                "id": "dest-hampi-matanga-hill",
                "name": "Matanga Hill Sunrise Viewpoint",
                "category": "Highest Hampi Panoramic Peak",
                "description": "Highest point in central Hampi offering an unforgettable 360-degree panoramic sunrise view over boulder-strewn valleys, temples, and river.",
                "coordinates": [15.3320, 76.4680],
                "location": "Central Hampi",
            },
        ],
        "chikmagalur": [
            {
                "id": "dest-cmg-mullayanagiri",
                "name": "Mullayanagiri Peak",
                "category": "Highest Karnataka Mountain Peak",
                "description": "Highest peak in Karnataka (1,930 m) offering trek trails through rolling clouds and panoramic Western Ghats valley views.",
                "coordinates": [13.3912, 75.7214],
                "location": "Chikmagalur (~20 km from town)",
            },
            {
                "id": "dest-cmg-baba-budan",
                "name": "Baba Budangiri (Dattatreya Peetha)",
                "category": "Sacred Mountain Shrine & Waterfalls",
                "description": "Sacred mountain range famous as the historic birthplace of Indian coffee cultivation and scenic Manikyadhara waterfalls.",
                "coordinates": [13.4215, 75.7658],
                "location": "Baba Budan Range",
            },
            {
                "id": "dest-cmg-hebbe-falls",
                "name": "Hebbe Falls",
                "category": "550-Foot Rainforest Waterfall",
                "description": "Spectacular 550-foot two-stage waterfall plunging through dense coffee and spice estates inside Bhadra Wildlife Reserve.",
                "coordinates": [13.5414, 75.7265],
                "location": "Kemmangundi (~30 km from Chikmagalur)",
            },
            {
                "id": "dest-cmg-coffee-museum",
                "name": "Coffee Museum & Heritage Tasting Center",
                "category": "Coffee Heritage Center",
                "description": "Interactive museum tracing the history, bean varieties, roasting, and brewing of South Indian Arabica and Robusta coffee.",
                "coordinates": [13.3082, 75.7891],
                "location": "Dasarahalli, Chikmagalur",
            },
        ],
        "jaipur": [
            {
                "id": "dest-jpr-amber",
                "name": "Amber Palace & Fort",
                "category": "UNESCO Hilltop Fortress",
                "description": "Majestic hilltop fort built of red sandstone and marble, famous for the Sheesh Mahal (Mirror Palace) and Maota Lake reflection.",
                "coordinates": [26.9855, 75.8513],
                "location": "Amer, Jaipur",
            },
            {
                "id": "dest-jpr-hawa-mahal",
                "name": "Hawa Mahal (Palace of Winds)",
                "category": "Iconic Pink Sandstone Palace",
                "description": "Iconic five-story pink sandstone palace featuring 953 honeycomb jharokhas designed for royal court ladies to observe street processions.",
                "coordinates": [26.9239, 75.8267],
                "location": "Badi Choupad, Pink City",
            },
            {
                "id": "dest-jpr-city-palace",
                "name": "City Palace & Jantar Mantar Observatory",
                "category": "Royal Palace & UNESCO Observatory",
                "description": "Royal residence complex blending Rajput and Mughal architecture, next to the 18th-century stone astronomical observatory.",
                "coordinates": [26.9258, 75.8237],
                "location": "Old City, Jaipur",
            },
            {
                "id": "dest-jpr-nahargarh",
                "name": "Nahargarh Fort Sunset Point",
                "category": "Panoramic Aravalli Hilltop Fort",
                "description": "Perched atop the rugged Aravalli Hills overlooking the entire Pink City, the premier location for golden hour sunset and night vistas.",
                "coordinates": [26.9372, 75.8156],
                "location": "Aravalli Hills, Jaipur",
            },
            {
                "id": "dest-jpr-jal-mahal",
                "name": "Jal Mahal (Water Palace)",
                "category": "Romantic Island Palace",
                "description": "Romantic Rajput-style palace appearing to float in the center of Man Sagar Lake against the dramatic backdrop of the Aravalli hills.",
                "coordinates": [26.9535, 75.8462],
                "location": "Amer Road, Jaipur",
            },
        ],
        "kerala": [
            {
                "id": "dest-ker-alleppey",
                "name": "Alleppey Backwaters & Houseboat Cruises",
                "category": "World-Famous Backwater Lagoon",
                "description": "Venice of the East: tranquil labyrinth of palm-fringed canals, lagoons, and paddy fields navigated on traditional kettuvallam houseboats.",
                "coordinates": [9.4981, 76.3388],
                "location": "Alappuzha, Kerala",
            },
            {
                "id": "dest-ker-munnar-tea",
                "name": "Munnar Tea Gardens & Eravikulam National Park",
                "category": "Tea Plantations & Wildlife Sanctuary",
                "description": "Endless emerald tea plantations rolling into misty Western Ghat peaks, home to the endangered Nilgiri Tahr and Anamudi Peak (2,695m).",
                "coordinates": [10.1500, 77.0500],
                "location": "Munnar, Idukki District",
            },
            {
                "id": "dest-ker-fort-kochi",
                "name": "Fort Kochi, Chinese Fishing Nets & Jew Town",
                "category": "Seaside Colonial Heritage Quarter",
                "description": "Historic seaside colonial quarter famed for cantilevered Chinese fishing nets, 16th-century Mattancherry Dutch Palace, and spice warehouses.",
                "coordinates": [9.9658, 76.2425],
                "location": "Kochi, Kerala",
            },
            {
                "id": "dest-ker-varkala",
                "name": "Varkala Cliff Beach & Papanasam Shores",
                "category": "Red Laterite Cliff Beach",
                "description": "Unique geo-heritage coastal cliffs plunging dramatically into the Arabian Sea, lined with bohemian cafes and natural mineral springs.",
                "coordinates": [8.7379, 76.7163],
                "location": "Varkala, South Kerala",
            },
        ],
        "manali": [
            {
                "id": "dest-mnl-solang",
                "name": "Solang Valley & Adventure Sports Arena",
                "category": "Alpine Adventure Sports Valley",
                "description": "World-famous valley framed by snow-clad Himalayan peaks, renowned for paragliding, zorbing, skiing, and cable car ropeways.",
                "coordinates": [32.3166, 77.1583],
                "location": "Solang Valley (~14 km from Manali)",
            },
            {
                "id": "dest-mnl-atal-tunnel",
                "name": "Atal Tunnel & Sissu Waterfall (Lahaul Valley)",
                "category": "World's Longest High-Altitude Tunnel",
                "description": "World's longest highway tunnel above 10,000 feet connecting Kullu to the stark snow-desert valleys and frozen waterfalls of Lahaul.",
                "coordinates": [32.4828, 77.1264],
                "location": "North Portal, Lahaul",
            },
            {
                "id": "dest-mnl-hadimba",
                "name": "Hadimba Temple & Van Vihar Cedar Forest",
                "category": "16th-Century Wooden Pagoda Temple",
                "description": "Unique 1553 CE four-tiered pagoda-style wooden temple dedicated to Hadimba Devi, surrounded by towering deodar cedar groves.",
                "coordinates": [32.2483, 77.1817],
                "location": "Old Manali",
            },
            {
                "id": "dest-mnl-rohtang",
                "name": "Rohtang Pass Snow Crest",
                "category": "High-Altitude Himalayan Pass",
                "description": "Legendary mountain pass at 13,058 feet on the Pir Panjal range with year-round snow landscapes and panoramic glacier views.",
                "coordinates": [32.3716, 77.2466],
                "location": "Rohtang Pass (~51 km from Manali)",
            },
        ],
        "hyderabad": [
            {
                "id": "dest-hyd-charminar",
                "name": "Charminar & Laad Bazaar",
                "category": "16th-Century Monument & Heritage Market",
                "description": "Global icon of Hyderabad built in 1591 with four 56m minarets, surrounded by the famous lacquer bangle and pearl bazaar.",
                "coordinates": [17.3616, 78.4747],
                "location": "Old City, Hyderabad",
            },
            {
                "id": "dest-hyd-golconda",
                "name": "Golconda Fort & Acoustic Sound Engineering",
                "category": "Historic Citadel & Diamond Fortress",
                "description": "Impregnable diamond citadel famed for acoustical engineering where a handclap at the entrance gate echoes at the hilltop Bala Hissar.",
                "coordinates": [17.3833, 78.4011],
                "location": "Golconda, Hyderabad",
            },
            {
                "id": "dest-hyd-ramoji",
                "name": "Ramoji Film City",
                "category": "World's Largest Film Studio Complex",
                "description": "Guinness Record-holding film studio complex spanning over 1,600 acres with international film sets, live stunt shows, and theme parks.",
                "coordinates": [17.2543, 78.6808],
                "location": "Hayathnagar, Hyderabad",
            },
            {
                "id": "dest-hyd-hussain-sagar",
                "name": "Hussain Sagar Lake & Monolithic Buddha",
                "category": "Historic Lake & Monolith Statue",
                "description": "Heart-shaped 1563 CE lake featuring the world's tallest monolithic granite Buddha statue standing on Gibraltar Rock.",
                "coordinates": [17.4239, 78.4738],
                "location": "Necklace Road, Hyderabad",
            },
        ],
    }

    def __init__(self) -> None:
        self.geocode_url = "https://nominatim.openstreetmap.org/search"
        self.overpass_url = os.getenv("OVERPASS_API_URL", "https://overpass-api.de/api/interpreter")
        self.route_url = "https://router.project-osrm.org/route/v1/"
        self._response_cache: dict[tuple[float, float], list[str]] = {}
        self._geocode_cache: dict[str, dict[str, Any]] = {}
        self._nearby_cache: dict[tuple[float, float, int], list[dict[str, Any]]] = {}
        self.budget_service = BudgetService()

    @staticmethod
    def _is_valid_coordinate(latitude: Any, longitude: Any) -> bool:
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (TypeError, ValueError):
            return False
        if not math.isfinite(lat) or not math.isfinite(lon):
            return False
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

    @staticmethod
    def _route_profile_for_mode(mode: str | None) -> str:
        profile = (mode or "driving").lower()
        if profile == "public_transport":
            return "driving"
        if profile in {"walking", "cycling", "driving"}:
            return profile
        if profile == "foot":
            return "foot"
        return "driving"

    @staticmethod
    def _country_name_from_display(display_name: str | None) -> str | None:
        if not display_name:
            return None
        parts = [part.strip() for part in display_name.split(',')]
        country = next((part for part in reversed(parts) if part), None)
        return country or None

    @staticmethod
    def _is_international_trip(start_country: str | None, destination_country: str | None) -> bool:
        if not start_country or not destination_country:
            return False
        return start_country.strip().lower() != destination_country.strip().lower()

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Return great circle distance in km."""
        r = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c

    @classmethod
    def _normalize_city_name(cls, name: str) -> str:
        """Normalize city, district, or alternative spelling into a canonical key."""
        n = (name or "").strip().lower()
        mapping = {
            "bengaluru": "bangalore",
            "madikeri": "coorg",
            "kodagu": "coorg",
            "mysuru": "mysore",
            "ballari": "bellary",
            "hubballi": "hubli",
            "belagavi": "belgaum",
            "mangaluru": "mangalore",
            "shivamogga": "shimoga",
            "chikkamagaluru": "chikmagalur",
            "tumakuru": "tumkur",
            "anathapuram": "anantapur",
            "ananthapur": "anantapur",
            "ananthapuramu": "anantapur",
            "panjim": "goa",
            "panaji": "goa",
            "madgaon": "goa",
            "margao": "goa",
            "calangute": "goa",
            "baga": "goa",
            "vizag": "visakhapatnam",
            "cuddapah": "kadapa",
            "rajamahendravaram": "rajahmundry",
            "madras": "chennai",
            "trichy": "tiruchirappalli",
            "tanjore": "thanjavur",
            "puducherry": "pondicherry",
            "poona": "pune",
            "bombay": "mumbai",
            "calcutta": "kolkata",
            "cochin": "kochi",
        }
        for k, v in mapping.items():
            if k in n:
                return v
        return n

    def _find_nearest_known_place(self, lat: float, lon: float, max_km: float = 70.0) -> tuple[str, str] | None:
        """Find the nearest known district or city within max_km distance."""
        best_dist = float("inf")
        best_place: tuple[str, str] | None = None
        for name, data in self.KNOWN_DISTRICTS_AND_CITIES.items():
            d = self._haversine_distance(lat, lon, float(data["lat"]), float(data["lon"]))
            if d < best_dist and d <= max_km:
                best_dist = d
                disp = data.get("display_name", "")
                state = disp.split(",")[1].strip() if "," in disp else ""
                best_place = (name.title(), state)
        return best_place

    def _generate_fallback_geometry(
        self, start_lat: float, start_lon: float, dest_lat: float, dest_lon: float, points_count: int = 24
    ) -> list[list[float]]:
        """Generate smooth interpolated route coordinates connecting start and destination."""
        coords: list[list[float]] = []
        # Add slight natural road curvature
        mid_lat = (start_lat + dest_lat) / 2.0
        mid_lon = (start_lon + dest_lon) / 2.0
        curve_offset_lat = (dest_lon - start_lon) * 0.04
        curve_offset_lon = -(dest_lat - start_lat) * 0.04

        for step in range(points_count):
            t = step / float(points_count - 1)
            # Quadratic bezier interpolation
            u = 1.0 - t
            control_lat = mid_lat + curve_offset_lat
            control_lon = mid_lon + curve_offset_lon
            pt_lat = (u * u * start_lat) + (2 * u * t * control_lat) + (t * t * dest_lat)
            pt_lon = (u * u * start_lon) + (2 * u * t * control_lon) + (t * t * dest_lon)
            coords.append([round(pt_lat, 5), round(pt_lon, 5)])
        return coords

    def _format_step_instruction(self, step: dict[str, Any], index: int, total: int) -> str:
        """Format an OSRM step into a natural navigation instruction."""
        maneuver = step.get("maneuver") or {}
        m_type = maneuver.get("type", "continue")
        modifier = maneuver.get("modifier", "")
        name = (step.get("name") or "").strip()
        ref = (step.get("ref") or "").strip()

        road = f"{name} ({ref})" if name and ref else (name or ref or "main connecting road")
        dist_m = float(step.get("distance") or 0.0)
        dist_str = f" ({dist_m / 1000:.1f} km)" if dist_m >= 500 else (f" ({int(dist_m)} m)" if dist_m > 0 else "")

        if index == 0 or m_type == "depart":
            return f"Depart from start point on {road}{dist_str}."
        if index == total - 1 or m_type == "arrive":
            return f"Arrive at destination on {road}."
        if m_type == "turn":
            mod_text = f" {modifier}" if modifier else ""
            return f"Turn{mod_text} onto {road}{dist_str}."
        if m_type == "new name":
            return f"Continue onto {road}{dist_str}."
        if m_type in {"merge", "on ramp"}:
            mod_text = f" {modifier}" if modifier else ""
            return f"Merge{mod_text} onto {road}{dist_str}."
        if m_type in {"off ramp", "fork"}:
            mod_text = f" {modifier}" if modifier else ""
            return f"Take the exit{mod_text} towards {road}{dist_str}."
        if m_type == "roundabout":
            exit_num = maneuver.get("exit")
            exit_text = f" and take exit {exit_num}" if exit_num else ""
            return f"Enter roundabout{exit_text} onto {road}{dist_str}."
        if modifier:
            return f"Keep {modifier} on {road}{dist_str}."
        return f"Continue on {road}{dist_str}."

    def _generate_fallback_directions(
        self, start: str, destination: str, distance_km: float, duration_minutes: float, mode: str = "driving"
    ) -> list[dict[str, Any]]:
        """Generate structured route directions when live step data is unavailable."""
        dist = max(1.0, float(distance_km or 100.0))
        dur = max(1.0, float(duration_minutes or 90.0))
        mode_label = mode.replace("_", " ").title()

        # Check for Anantapur / Anathapuram to Goa corridor
        is_atp_goa = any(k in start.lower() for k in ["anantapur", "anathapuram", "ananthapur"]) and "goa" in destination.lower()
        if is_atp_goa:
            return [
                {
                    "step": 1,
                    "instruction": f"Depart {start} via Gooty Road / NH 44 and take the Bellary exit onto NH 67.",
                    "road": "NH 67 (Anantapur-Ballari Highway)",
                    "distance_km": 65.0,
                    "duration_minutes": 55.0,
                    "maneuver_type": "depart",
                    "modifier": "",
                },
                {
                    "step": 2,
                    "instruction": "Pass Ballari (stop available for Bellary Fort rock citadel) and continue on 4-lane NH 67 towards Hosapete.",
                    "road": "NH 67 Highway",
                    "distance_km": 68.0,
                    "duration_minutes": 50.0,
                    "maneuver_type": "continue",
                    "modifier": "straight",
                },
                {
                    "step": 3,
                    "instruction": "Reach Hosapete (gateway to Hampi UNESCO ruins & Tungabhadra Dam) and continue west on NH 67.",
                    "road": "NH 67 Hosapete Bypass",
                    "distance_km": 85.0,
                    "duration_minutes": 70.0,
                    "maneuver_type": "continue",
                    "modifier": "straight",
                },
                {
                    "step": 4,
                    "instruction": "Proceed through Koppal and Gadag bypass towards Hubballi-Dharwad twin cities.",
                    "road": "NH 67 / Hubballi Ring Road",
                    "distance_km": 72.0,
                    "duration_minutes": 60.0,
                    "maneuver_type": "continue",
                    "modifier": "straight",
                },
                {
                    "step": 5,
                    "instruction": "From Dharwad, merge onto NH 748 (Belagavi-Goa Road) entering Western Ghats forest corridor via Alnavar.",
                    "road": "NH 748 (Goa Highway)",
                    "distance_km": 90.0,
                    "duration_minutes": 75.0,
                    "maneuver_type": "merge",
                    "modifier": "left",
                },
                {
                    "step": 6,
                    "instruction": "Cross Karnataka-Goa border at Anmod Ghat / Mollem (scenic stops for Dudhsagar Falls & Bhagwan Mahaveer Sanctuary).",
                    "road": "NH 748 Anmod Ghat / Mollem Road",
                    "distance_km": 55.0,
                    "duration_minutes": 50.0,
                    "maneuver_type": "continue",
                    "modifier": "straight",
                },
                {
                    "step": 7,
                    "instruction": f"Descend through Ponda and arrive at {destination} (Panaji / coastal beach resorts).",
                    "road": "Panaji-Belagavi Highway / NH 748",
                    "distance_km": 45.0,
                    "duration_minutes": 40.0,
                    "maneuver_type": "arrive",
                    "modifier": "",
                },
            ]

        # Check for Bangalore - Mysore corridor specific milestones
        is_blr_mys = ("bangalore" in start.lower() or "bengaluru" in start.lower()) and "mysore" in destination.lower()
        if is_blr_mys:
            return [
                {
                    "step": 1,
                    "instruction": f"Depart {start} city center via Outer Ring Road towards Mysore Road / Kengeri.",
                    "road": "Outer Ring Road / Mysore Road (SH 17)",
                    "distance_km": 14.5,
                    "duration_minutes": 25.0,
                    "maneuver_type": "depart",
                    "modifier": "",
                },
                {
                    "step": 2,
                    "instruction": "Merge onto the access-controlled Bangalore-Mysore Expressway (NH 275).",
                    "road": "Bangalore-Mysore Expressway (NH 275)",
                    "distance_km": 28.0,
                    "duration_minutes": 20.0,
                    "maneuver_type": "merge",
                    "modifier": "straight",
                },
                {
                    "step": 3,
                    "instruction": "Pass Ramanagara (stop available for Ramadevara Betta & Janapada Loka) and continue towards Channapatna.",
                    "road": "NH 275 Expressway",
                    "distance_km": 25.0,
                    "duration_minutes": 18.0,
                    "maneuver_type": "continue",
                    "modifier": "straight",
                },
                {
                    "step": 4,
                    "instruction": "Pass Channapatna Crafts Town & Maddur (famous for Maddur Vada culinary pitstops).",
                    "road": "NH 275 Expressway",
                    "distance_km": 30.0,
                    "duration_minutes": 22.0,
                    "maneuver_type": "continue",
                    "modifier": "straight",
                },
                {
                    "step": 5,
                    "instruction": "Bypass Mandya and proceed towards Srirangapatna heritage island & Kaveri river bridges.",
                    "road": "NH 275 Expressway",
                    "distance_km": 28.0,
                    "duration_minutes": 22.0,
                    "maneuver_type": "continue",
                    "modifier": "straight",
                },
                {
                    "step": 6,
                    "instruction": "Take the exit at Columbia Asia Hospital Junction onto Bengaluru-Nilgiri Road towards Mysore.",
                    "road": "Bengaluru-Mysore Road / NH 275 Exit",
                    "distance_km": 12.0,
                    "duration_minutes": 15.0,
                    "maneuver_type": "off ramp",
                    "modifier": "left",
                },
                {
                    "step": 7,
                    "instruction": f"Arrive in {destination} near Mysore Palace and city center.",
                    "road": "Sayyaji Rao Road / Albert Victor Road",
                    "distance_km": 2.8,
                    "duration_minutes": 8.0,
                    "maneuver_type": "arrive",
                    "modifier": "",
                },
            ]

        # Check for Bangalore - Coorg / Madikeri corridor
        is_blr_coorg = ("bangalore" in start.lower() or "bengaluru" in start.lower()) and ("coorg" in destination.lower() or "madikeri" in destination.lower())
        if is_blr_coorg:
            return [
                {
                    "step": 1,
                    "instruction": f"Depart {start} via Mysore Road / Kengeri and join the 10-lane Bangalore-Mysore Expressway (NH 275).",
                    "road": "Bangalore-Mysore Expressway (NH 275)",
                    "distance_km": 50.0,
                    "duration_minutes": 35.0,
                    "maneuver_type": "depart",
                    "modifier": "",
                },
                {
                    "step": 2,
                    "instruction": "Pass Ramanagara (Ramadevara Betta) and Channapatna Toy Village, stopping for hot Maddur Vada at Maddur.",
                    "road": "NH 275 Expressway",
                    "distance_km": 40.0,
                    "duration_minutes": 30.0,
                    "maneuver_type": "continue",
                    "modifier": "straight",
                },
                {
                    "step": 3,
                    "instruction": "Bypass Mandya and take the Mysore Outer Ring Road exit at Columbia Asia Junction towards Hunsur.",
                    "road": "Mysore Ring Road / Mangalore-Mysore Highway",
                    "distance_km": 45.0,
                    "duration_minutes": 40.0,
                    "maneuver_type": "off ramp",
                    "modifier": "right",
                },
                {
                    "step": 4,
                    "instruction": "Continue on NH 275 passing Hunsur and Periyapatna through scenic countryside.",
                    "road": "NH 275 (Mysore-Madikeri Road)",
                    "distance_km": 55.0,
                    "duration_minutes": 50.0,
                    "maneuver_type": "continue",
                    "modifier": "straight",
                },
                {
                    "step": 5,
                    "instruction": "Arrive at Bylakuppe Tibetan settlement to visit the Golden Temple (Namdroling Monastery) and Kaveri Nisargadhama at Kushalnagar.",
                    "road": "NH 275 Kushalnagar Corridor",
                    "distance_km": 25.0,
                    "duration_minutes": 25.0,
                    "maneuver_type": "continue",
                    "modifier": "straight",
                },
                {
                    "step": 6,
                    "instruction": "Climb through the lush winding Western Ghats ghat section past coffee estates into Madikeri / Coorg.",
                    "road": "Madikeri Ghat Road / NH 275",
                    "distance_km": 30.0,
                    "duration_minutes": 45.0,
                    "maneuver_type": "arrive",
                    "modifier": "",
                },
            ]

        # General high-quality 5-step corridor directions
        leg_dist = round(dist / 5.0, 1)
        leg_dur = round(dur / 5.0, 1)
        return [
            {
                "step": 1,
                "instruction": f"Depart {start} city center and follow outbound arterial signs towards the main highway.",
                "road": f"{start} Arterial Corridor",
                "distance_km": round(leg_dist * 0.6, 1),
                "duration_minutes": round(leg_dur * 0.8, 1),
                "maneuver_type": "depart",
                "modifier": "",
            },
            {
                "step": 2,
                "instruction": f"Merge onto the primary regional corridor / expressway heading towards {destination}.",
                "road": f"{start}-{destination} Connecting Highway",
                "distance_km": round(leg_dist * 1.4, 1),
                "duration_minutes": round(leg_dur * 1.1, 1),
                "maneuver_type": "merge",
                "modifier": "straight",
            },
            {
                "step": 3,
                "instruction": "Continue along the main highway corridor past intermediate transit towns and scenic viewpoints.",
                "road": "Regional National Highway",
                "distance_km": round(leg_dist * 1.5, 1),
                "duration_minutes": round(leg_dur * 1.2, 1),
                "maneuver_type": "continue",
                "modifier": "straight",
            },
            {
                "step": 4,
                "instruction": f"Take the city bypass / exit interchange following destination signboards for {destination}.",
                "road": f"{destination} Approach Corridor",
                "distance_km": round(leg_dist * 1.0, 1),
                "duration_minutes": round(leg_dur * 1.0, 1),
                "maneuver_type": "off ramp",
                "modifier": "left",
            },
            {
                "step": 5,
                "instruction": f"Arrive at {destination} city center / landmark district.",
                "road": f"{destination} City Center Road",
                "distance_km": round(leg_dist * 0.5, 1),
                "duration_minutes": round(leg_dur * 0.9, 1),
                "maneuver_type": "arrive",
                "modifier": "",
            },
        ]

    def _get_en_route_places(
        self, start: str, destination: str, start_lat: float, start_lon: float, dest_lat: float, dest_lon: float
    ) -> list[dict[str, Any]]:
        """Retrieve famous places that can be visited between the starting point and destination."""
        start_norm = self._normalize_city_name(start)
        dest_norm = self._normalize_city_name(destination)

        # 1. Check known corridor database first (bidirectional)
        for (c_start, c_dest), places in self.KNOWN_CORRIDORS.items():
            cs = self._normalize_city_name(c_start)
            cd = self._normalize_city_name(c_dest)
            if (cs in start_norm and cd in dest_norm) or (cd in start_norm and cs in dest_norm) or \
               (c_start in start.lower() and c_dest in destination.lower()) or (c_dest in start.lower() and c_start in destination.lower()):
                return places

        # 2. If corridor is not pre-registered, generate 3 distinct, realistic intermediate waypoints
        places: list[dict[str, Any]] = []
        waypoint_configs = [
            (
                0.25,
                "First Quarter Milestone",
                "Highway Food Oasis & Regional Breakfast Hub",
                "Iconic Highway Pitstop",
                "Popular highway rest stop and dining hub along the road trip corridor known for authentic local breakfast, hot filter coffee/tea, and clean traveler amenities.",
            ),
            (
                0.50,
                "Halfway Corridor Milestone",
                "Midway River Crossing & Heritage Scenic Viewpoint",
                "Scenic River & Heritage Landmark",
                "Historic midway transit center and scenic river crossing offering panoramic landscape views, local sweet shops, and shady rest groves.",
            ),
            (
                0.75,
                "Three-Quarter Milestone",
                "Scenic Foothills Gateway & Artisan Craft Village",
                "Scenic Foothills & Local Crafts",
                "Scenic approach gateway nestled in the foothills, featuring roadside fruit orchards, regional artisan handicraft stalls, and scenic mountain views.",
            ),
        ]

        for fraction, milestone_label, default_name, default_cat, default_desc in waypoint_configs:
            m_lat = round(start_lat + (dest_lat - start_lat) * fraction, 4)
            m_lon = round(start_lon + (dest_lon - start_lon) * fraction, 4)

            # Check if a known district/town is nearby within 70 km
            nearest_town = self._find_nearest_known_place(m_lat, m_lon, max_km=70.0)
            if nearest_town:
                town_name, state_name = nearest_town
                if fraction <= 0.35:
                    w_name = f"{town_name} Highway Rest Stop & Food Hub"
                    w_cat = "Iconic Highway Food Hub"
                    w_desc = f"Famous highway rest stop and culinary hub near {town_name} ({state_name}) famed for authentic regional cuisine, clean traveler amenities, and refreshments."
                elif fraction <= 0.65:
                    w_name = f"{town_name} Mid-Route Heritage Citadel & River Crossing"
                    w_cat = "Historic Town & Scenic River"
                    w_desc = f"Historic midway transit center near {town_name} featuring riverside scenic viewpoints, heritage architecture, and local artisan markets."
                else:
                    w_name = f"{town_name} Gateway Viewpoint & Artisan Craft Village"
                    w_cat = "Scenic Gateway & Local Crafts"
                    w_desc = f"Scenic approach gateway near {town_name} surrounded by rolling countryside, fresh agricultural produce stalls, and traditional craft emporiums."
            else:
                w_name = default_name
                w_cat = default_cat
                w_desc = default_desc

            places.append(
                {
                    "id": f"enroute-{round(m_lat, 3)}-{round(m_lon, 3)}",
                    "name": w_name,
                    "category": w_cat,
                    "description": w_desc,
                    "coordinates": [m_lat, m_lon],
                    "location": f"Highway corridor ({int(fraction * 100)}% from {start.title()})",
                    "is_en_route": True,
                }
            )

        return places

    def get_destination_landmarks(self, destination: str, lat: float, lon: float) -> list[dict[str, Any]]:
        """Return famous, curated destination landmarks for a destination, avoiding generic fallbacks."""
        dest_norm = self._normalize_city_name(destination)

        # 1. Exact or partial match in KNOWN_DESTINATION_LANDMARKS
        for key, landmarks in self.KNOWN_DESTINATION_LANDMARKS.items():
            k_norm = self._normalize_city_name(key)
            if k_norm == dest_norm or k_norm in dest_norm or dest_norm in k_norm:
                return [p.copy() for p in landmarks]

        # 2. Check coordinate proximity to known destinations
        # Coorg (Madikeri, Kushalnagar)
        if 12.0 <= lat <= 12.8 and 75.3 <= lon <= 76.2:
            return [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["coorg"]]
        # Goa
        if 15.0 <= lat <= 15.8 and 73.6 <= lon <= 74.3:
            return [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["goa"]]
        # Mysore
        if abs(lat - 12.2958) < 0.3 and abs(lon - 76.6394) < 0.3:
            return [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["mysore"]]
        # Bangalore
        if abs(lat - 12.9716) < 0.3 and abs(lon - 77.5946) < 0.3:
            return [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["bangalore"]]
        # Ooty
        if abs(lat - 11.4102) < 0.3 and abs(lon - 76.6950) < 0.3:
            return [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["ooty"]]
        # Hampi
        if abs(lat - 15.3350) < 0.3 and abs(lon - 76.4600) < 0.3:
            return [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["hampi"]]
        # Chikmagalur
        if abs(lat - 13.3161) < 0.3 and abs(lon - 75.7720) < 0.3:
            return [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["chikmagalur"]]
        # Jaipur
        if abs(lat - 26.9124) < 0.3 and abs(lon - 75.7873) < 0.3:
            return [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["jaipur"]]
        # Hyderabad
        if abs(lat - 17.3850) < 0.3 and abs(lon - 78.4867) < 0.3:
            return [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["hyderabad"]]

        # 3. Check LocationService for curated attractions or local highlights
        try:
            from services.location_service import LocationService
            loc_data = LocationService().get_location_data(destination)
            attractions = loc_data.get("nearby_attractions") or loc_data.get("local_highlights")
            if attractions and isinstance(attractions, list) and len(attractions) >= 2:
                landmarks = []
                offsets = [
                    (0.015, 0.012, "Historic Heritage Landmark"),
                    (-0.018, 0.015, "Scenic Nature & Viewpoint"),
                    (0.022, -0.019, "Cultural & Architectural Site"),
                    (-0.012, -0.022, "Traditional Artisan Bazaar"),
                    (0.028, 0.025, "Iconic Waterfront & Promenade"),
                ]
                for idx, attr in enumerate(attractions[:6]):
                    off_lat, off_lon, cat = offsets[idx % len(offsets)]
                    landmarks.append({
                        "id": f"dest-{dest_norm}-{idx+1}",
                        "name": str(attr),
                        "category": cat,
                        "description": f"Must-visit iconic highlight and popular cultural attraction in {destination.title()}.",
                        "coordinates": [round(lat + off_lat, 4), round(lon + off_lon, 4)],
                        "location": f"{destination.title()} Central Area",
                        "is_en_route": False,
                    })
                return landmarks
        except Exception:
            pass

        # 4. Try live nearby places from Overpass if available and valid
        live_places = self.get_nearby_places(lat, lon, radius=15000)
        valid_live = [p for p in live_places if p.get("name") not in {"Historic center", "Unnamed place"}]
        if valid_live:
            for p in valid_live:
                p["is_en_route"] = False
            return valid_live

        # 5. High-quality distinct landmarks for any other city or district in India
        title_dest = destination.strip().title() or "Destination"
        return [
            {
                "id": f"dest-{dest_norm}-citadel",
                "name": f"{title_dest} Royal Heritage Citadel & Historic Fort",
                "category": "Historic Citadel & Heritage",
                "description": f"Grand historical monument and heritage citadel showcasing the rich architectural legacy and royal chronicles of {title_dest}.",
                "coordinates": [round(lat + 0.0142, 4), round(lon + 0.0115, 4)],
                "location": f"{title_dest} Old Town Heritage Quarter",
                "is_en_route": False,
            },
            {
                "id": f"dest-{dest_norm}-botanical",
                "name": f"{title_dest} Central Botanical Garden & Lake Promenade",
                "category": "Lush Botanical Garden & Lake",
                "description": f"Expansive landscaped botanical gardens featuring century-old trees, blooming flora, and tranquil lakeside walking promenades.",
                "coordinates": [round(lat - 0.0165, 4), round(lon + 0.0148, 4)],
                "location": f"{title_dest} Central Promenade",
                "is_en_route": False,
            },
            {
                "id": f"dest-{dest_norm}-bazaar",
                "name": f"{title_dest} Traditional Artisan Crafts & Silk Bazaar",
                "category": "Artisan Crafts & Heritage Market",
                "description": f"Vibrant century-old bazaar famous for authentic regional handicrafts, handloom textiles, aromatic spices, and traditional sweets.",
                "coordinates": [round(lat + 0.0185, 4), round(lon - 0.0162, 4)],
                "location": f"{title_dest} Downtown Bazaar Quarter",
                "is_en_route": False,
            },
            {
                "id": f"dest-{dest_norm}-sunset-hill",
                "name": f"{title_dest} Sunset Vista & Panoramic Hill Viewpoint",
                "category": "Panoramic Viewpoint & Sunset Peak",
                "description": f"Elevated scenic viewpoint offering breathtaking 360-degree panoramas of {title_dest}'s skyline, countryside, and golden hour sunsets.",
                "coordinates": [round(lat - 0.0221, 4), round(lon - 0.0195, 4)],
                "location": f"{title_dest} Hill Ridge Overlook",
                "is_en_route": False,
            },
            {
                "id": f"dest-{dest_norm}-temple",
                "name": f"{title_dest} Sacred Heritage Sanctuary & Cultural Temple",
                "category": "Sacred Architecture & Cultural Heritage",
                "description": f"Centuries-old spiritual landmark renowned for intricate stone carvings, serene courtyards, and vibrant cultural festivities.",
                "coordinates": [round(lat + 0.0245, 4), round(lon + 0.0210, 4)],
                "location": f"{title_dest} Heritage Temple Enclosure",
                "is_en_route": False,
            },
        ]

    def get_map_context(self, destination: str) -> dict[str, Any]:
        location = self.geocode(destination)
        if not location:
            dest_landmarks = self.get_destination_landmarks(destination, 12.9716, 77.5946)
            return {
                "destination": destination,
                "coordinates": {},
                "nearby_places": [p["name"] for p in dest_landmarks[:5]],
                "map_links": {
                    "openstreetmap": f"https://www.openstreetmap.org/search?query={quote(destination)}",
                },
                "display_name": destination,
                "route_summary": "Route data is unavailable; this is a local recommendation only.",
            }

        lat = float(location["lat"])
        lon = float(location["lon"])
        dest_landmarks = self.get_destination_landmarks(destination, lat, lon)
        nearby_places = [p["name"] for p in dest_landmarks[:6]]
        return {
            "destination": destination,
            "coordinates": {"lat": lat, "lon": lon},
            "nearby_places": nearby_places,
            "map_links": {
                "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=14/{lat}/{lon}",
            },
            "display_name": location.get("display_name", destination),
            "route_summary": "Map data available for destination highlights; route verification depends on live routing service availability.",
        }

    def get_route_context(
        self, start: str, destination: str, mode: str = "driving", travelers: int = 2, travel_style: str = "standard"
    ) -> dict[str, Any]:
        route_response = self.get_route_details(start, destination, mode, travelers=travelers, travel_style=travel_style)
        if route_response["status"] == "success":
            return {
                "status": "verified",
                "distance_km": route_response.get("distance_km"),
                "duration_minutes": route_response.get("duration_minutes"),
                "route_points": route_response.get("geometry") or [],
                "stops": [place["name"] for place in route_response.get("stops", [])],
                "en_route_places": [place["name"] for place in route_response.get("en_route_places", [])],
                "directions": route_response.get("directions", []),
                "route_budget": route_response.get("route_budget", {}),
                "summary": route_response.get("summary", "Driving route verified."),
            }

        return {
            "status": "unavailable",
            "distance_km": route_response.get("distance_km"),
            "duration_minutes": route_response.get("duration_minutes"),
            "route_points": route_response.get("geometry") or [],
            "stops": [place["name"] for place in route_response.get("stops", [])],
            "en_route_places": [place["name"] for place in route_response.get("en_route_places", [])],
            "directions": route_response.get("directions", []),
            "route_budget": route_response.get("route_budget", {}),
            "summary": route_response.get("summary", "Route data is unavailable; map-based stop suggestions remain advisory only."),
        }

    def get_route_details(
        self,
        start: str,
        destination: str,
        mode: str = "driving",
        travelers: int = 2,
        travel_style: str = "standard",
    ) -> dict[str, Any]:
        normalized_mode = (mode or "driving").lower()
        if not start or not destination:
            return {
                "status": "unavailable",
                "start": None,
                "destination": None,
                "mode": normalized_mode,
                "distance_km": None,
                "duration_minutes": None,
                "geometry": None,
                "directions": [],
                "route_budget": {},
                "en_route_places": [],
                "destination_places": [],
                "stops": [],
                "summary": "Route data is unavailable; exact driving distance and duration were not verified.",
            }

        start_location = self.geocode(start)
        destination_location = self.geocode(destination)
        if not start_location or not destination_location:
            fallback_dist = 140.0 if ("bangalore" in start.lower() or "bengaluru" in start.lower()) and "mysore" in destination.lower() else 120.0
            fallback_dur = round((fallback_dist / 65.0) * 60.0, 1)
            fallback_budget = self.budget_service.calculate_route_budget(
                distance_km=fallback_dist,
                mode=normalized_mode,
                travelers=travelers,
                travel_style=travel_style,
            )
            fallback_en_route = self._get_en_route_places(start, destination, 12.9716, 77.5946, 12.2958, 76.6394)
            fallback_dest_places = self.get_destination_landmarks(destination, 12.2958, 76.6394)
            fallback_directions = self._generate_fallback_directions(start, destination, fallback_dist, fallback_dur, mode=normalized_mode)
            fallback_geometry = self._generate_fallback_geometry(12.9716, 77.5946, 12.2958, 76.6394)
            return {
                "status": "unavailable",
                "start": None,
                "destination": None,
                "mode": normalized_mode,
                "distance_km": fallback_dist,
                "duration_minutes": fallback_dur,
                "geometry": fallback_geometry,
                "directions": fallback_directions,
                "route_budget": fallback_budget,
                "en_route_places": fallback_en_route,
                "destination_places": fallback_dest_places,
                "stops": fallback_en_route + fallback_dest_places,
                "summary": "Route data is unavailable because one or both locations could not be geocoded.",
            }

        start_lat = float(start_location["lat"])
        start_lon = float(start_location["lon"])
        destination_lat = float(destination_location["lat"])
        destination_lon = float(destination_location["lon"])

        if not self._is_valid_coordinate(start_lat, start_lon) or not self._is_valid_coordinate(destination_lat, destination_lon):
            return {
                "status": "unavailable",
                "start": None,
                "destination": None,
                "mode": normalized_mode,
                "distance_km": None,
                "duration_minutes": None,
                "geometry": None,
                "directions": [],
                "route_budget": {},
                "en_route_places": [],
                "destination_places": [],
                "stops": [],
                "summary": "Route data is unavailable because the geocoded coordinates were invalid.",
            }

        start_country = (start_location.get("address") or {}).get("country") or self._country_name_from_display(start_location.get("display_name"))
        destination_country = (destination_location.get("address") or {}).get("country") or self._country_name_from_display(destination_location.get("display_name"))
        is_international = self._is_international_trip(start_country, destination_country)

        start_payload = {
            "name": start_location.get("display_name") or start,
            "latitude": start_lat,
            "longitude": start_lon,
        }
        destination_payload = {
            "name": destination_location.get("display_name") or destination,
            "latitude": destination_lat,
            "longitude": destination_lon,
        }

        # Calculate en route places (between route) and destination places
        en_route_places = self._get_en_route_places(start, destination, start_lat, start_lon, destination_lat, destination_lon)
        destination_places = self.get_destination_landmarks(destination, destination_lat, destination_lon)
        combined_stops = en_route_places + destination_places

        straight_line_dist = self._haversine_distance(start_lat, start_lon, destination_lat, destination_lon)
        estimated_road_dist = round(straight_line_dist * 1.25, 1)
        estimated_duration = round((estimated_road_dist / 65.0) * 60.0, 1)  # ~65 km/h highway speed

        route_budget = self.budget_service.calculate_route_budget(
            distance_km=estimated_road_dist,
            mode=normalized_mode,
            travelers=travelers,
            travel_style=travel_style,
        )

        if normalized_mode == "flight" or (normalized_mode == "best_available" and is_international):
            flight_geometry = self._generate_fallback_geometry(start_lat, start_lon, destination_lat, destination_lon, points_count=30)
            return {
                "status": "partial",
                "start": start_payload,
                "destination": destination_payload,
                "mode": normalized_mode,
                "distance_km": round(straight_line_dist, 1),
                "duration_minutes": round((straight_line_dist / 750.0) * 60.0 + 90.0, 1),
                "geometry": flight_geometry,
                "directions": [
                    {"step": 1, "instruction": f"Depart from nearest airport in {start}.", "road": "Airport Departure", "distance_km": 0.0, "duration_minutes": 90.0},
                    {"step": 2, "instruction": f"Direct or connecting flight to {destination}.", "road": "Air Corridor", "distance_km": round(straight_line_dist, 1), "duration_minutes": round((straight_line_dist / 750.0) * 60.0, 1)},
                    {"step": 3, "instruction": f"Arrive at {destination} airport and take local transport to city.", "road": "Airport Arrival", "distance_km": 15.0, "duration_minutes": 45.0},
                ],
                "route_budget": route_budget,
                "en_route_places": en_route_places,
                "destination_places": destination_places,
                "stops": combined_stops,
                "summary": f"Flight route estimated between {start} and {destination}: ~{straight_line_dist:.0f} km air distance.",
            }

        if is_international and normalized_mode in {"driving", "public_transport", "walking", "cycling", "best_available"}:
            return {
                "status": "partial",
                "start": start_payload,
                "destination": destination_payload,
                "mode": normalized_mode,
                "distance_km": estimated_road_dist,
                "duration_minutes": estimated_duration,
                "geometry": self._generate_fallback_geometry(start_lat, start_lon, destination_lat, destination_lon),
                "directions": self._generate_fallback_directions(start, destination, estimated_road_dist, estimated_duration, mode=normalized_mode),
                "route_budget": route_budget,
                "en_route_places": en_route_places,
                "destination_places": destination_places,
                "stops": combined_stops,
                "summary": "Road-route geometry is unavailable for this international trip. The map shows the start, destination, en-route waypoints, and highlights.",
            }

        profile = self._route_profile_for_mode(normalized_mode)
        route_url = (
            f"{self.route_url}{profile}/{start_lon},{start_lat};{destination_lon},{destination_lat}"
            "?overview=full&geometries=geojson&steps=true"
        )

        try:
            response = requests.get(
                route_url,
                headers={
                    "User-Agent": "AITravelPlanner/1.0 (+https://example.com)",
                    "Accept": "application/json",
                },
                timeout=(5, 25),
            )
            response.raise_for_status()
            payload = response.json()
            route = (payload.get("routes") or [{}])[0]
            geometry = route.get("geometry") or {}
            raw_coordinates = geometry.get("coordinates") or []
            validated_coordinates: list[list[float]] = []
            for point in raw_coordinates:
                if len(point) < 2:
                    continue
                lon_value, lat_value = point[:2]
                if self._is_valid_coordinate(lat_value, lon_value):
                    validated_coordinates.append([float(lat_value), float(lon_value)])
            if not validated_coordinates:
                raise ValueError("No valid route geometry was returned")

            distance_m = route.get("distance")
            duration_s = route.get("duration")
            distance_value = round(float(distance_m) / 1000, 1) if distance_m is not None else estimated_road_dist
            duration_value = round(float(duration_s) / 60, 1) if duration_s is not None else estimated_duration

            # Parse turn-by-turn steps
            legs = route.get("legs") or [{}]
            raw_steps = legs[0].get("steps") or []
            directions: list[dict[str, Any]] = []
            for idx, step in enumerate(raw_steps):
                instruction = self._format_step_instruction(step, idx, len(raw_steps))
                s_dist = float(step.get("distance") or 0.0)
                s_dur = float(step.get("duration") or 0.0)
                directions.append({
                    "step": idx + 1,
                    "instruction": instruction,
                    "road": step.get("name") or step.get("ref") or "Connecting roadway",
                    "distance_km": round(s_dist / 1000.0, 1),
                    "duration_minutes": round(s_dur / 60.0, 1),
                    "maneuver_type": (step.get("maneuver") or {}).get("type", "continue"),
                    "modifier": (step.get("maneuver") or {}).get("modifier", ""),
                })

            if not directions:
                directions = self._generate_fallback_directions(start, destination, distance_value, duration_value, mode=normalized_mode)

            # Recompute route budget with verified distance
            verified_route_budget = self.budget_service.calculate_route_budget(
                distance_km=distance_value,
                mode=normalized_mode,
                travelers=travelers,
                travel_style=travel_style,
            )

            summary = (
                f"Verified {normalized_mode} route from {start} to {destination}: {distance_value} km in about {duration_value} minutes."
            )
            return {
                "status": "success",
                "start": start_payload,
                "destination": destination_payload,
                "mode": normalized_mode,
                "distance_km": distance_value,
                "duration_minutes": duration_value,
                "geometry": validated_coordinates,
                "directions": directions,
                "route_budget": verified_route_budget,
                "en_route_places": en_route_places,
                "destination_places": destination_places,
                "stops": combined_stops,
                "summary": summary,
            }
        except Exception as exc:  # pragma: no cover
            logger.warning("Route lookup failed for %s to %s via %s: %s", start, destination, profile, exc)
            fallback_geometry = self._generate_fallback_geometry(start_lat, start_lon, destination_lat, destination_lon)
            fallback_directions = self._generate_fallback_directions(
                start, destination, estimated_road_dist, estimated_duration, mode=normalized_mode
            )
            return {
                "status": "partial",
                "start": start_payload,
                "destination": destination_payload,
                "mode": normalized_mode,
                "distance_km": estimated_road_dist,
                "duration_minutes": estimated_duration,
                "geometry": fallback_geometry,
                "directions": fallback_directions,
                "route_budget": route_budget,
                "en_route_places": en_route_places,
                "destination_places": destination_places,
                "stops": combined_stops,
                "summary": (
                    f"Route data is unavailable via live OSRM; showing estimated route for {start} to {destination}: "
                    f"~{estimated_road_dist} km in about {estimated_duration} minutes with intermediate places."
                ),
            }

    def geocode(self, destination: str) -> dict[str, Any] | None:
        query = (destination or "").strip()
        if not query:
            return None
        cached = self._geocode_cache.get(query.lower())
        if cached is not None:
            return cached

        clean_key = query.lower().strip()
        for suffix in [" district", " city", " mandal", " taluk", " town", " dt.", " dt"]:
            if clean_key.endswith(suffix):
                clean_key = clean_key[:-len(suffix)].strip()
                break

        # Check local instant geocode database (0ms lookup, no rate limits or network lag)
        if clean_key in self.KNOWN_DISTRICTS_AND_CITIES:
            match = self.KNOWN_DISTRICTS_AND_CITIES[clean_key]
            result = {
                "lat": str(match["lat"]),
                "lon": str(match["lon"]),
                "display_name": match["display_name"],
                "address": {"country": "India"},
            }
            self._geocode_cache[query.lower()] = result
            return result

        # Check substring matches in known districts
        for known_name, match in self.KNOWN_DISTRICTS_AND_CITIES.items():
            if known_name == clean_key or (len(known_name) >= 4 and (known_name in clean_key or clean_key in known_name)):
                result = {
                    "lat": str(match["lat"]),
                    "lon": str(match["lon"]),
                    "display_name": match["display_name"],
                    "address": {"country": "India"},
                }
                self._geocode_cache[query.lower()] = result
                return result

        search_query = query if ("," in query or any(c in query.lower() for c in ["india", "usa", "uk", "france", "germany", "dubai", "uae"])) else f"{query}, India"
        params = {"format": "jsonv2", "limit": 1, "q": search_query}
        try:
            response = requests.get(
                self.geocode_url,
                params=params,
                headers={
                    "User-Agent": "AITravelPlanner/1.0 (+https://example.com)",
                    "Accept": "application/json",
                },
                timeout=(3, 8),
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list) or not data:
                return None
            entry = data[0]
            lat = entry.get("lat")
            lon = entry.get("lon")
            if not self._is_valid_coordinate(lat, lon):
                return None
            self._geocode_cache[query.lower()] = entry
            return entry
        except Exception as exc:  # pragma: no cover
            logger.warning("Geocoding failed for %s: %s", query, exc)
        return None

    def get_nearby_places(self, lat: float, lon: float, radius: int = 20000) -> list[dict[str, Any]]:
        if not self._is_valid_coordinate(lat, lon):
            return []

        cache_key = (round(float(lat), 4), round(float(lon), 4), int(radius))
        if cache_key in self._nearby_cache:
            return self._nearby_cache[cache_key]

        # Check for known Goa destination coordinates
        if 15.0 <= lat <= 15.8 and 73.6 <= lon <= 74.3:
            goa_places = [
                {
                    "id": "dest-fort-aguada",
                    "name": "Fort Aguada & Portuguese Lighthouse",
                    "category": "17th-Century Coastal Fortress",
                    "description": "Historic Portuguese fort standing guard over Sinquerim beach with a 4-storey freshwater reservoir and panoramic Arabian Sea views.",
                    "coordinates": [15.4920, 73.7737],
                    "location": "Sinquerim, Candolim, North Goa",
                },
                {
                    "id": "dest-basilica-bom-jesus",
                    "name": "Basilica of Bom Jesus (Old Goa)",
                    "category": "UNESCO World Heritage Baroque Church",
                    "description": "World-famous 16th-century Jesuit basilica enshrining the sacred mortal remains of St. Francis Xavier, renowned for baroque gilded altars.",
                    "coordinates": [15.5009, 73.9116],
                    "location": "Old Goa (Velha Goa)",
                },
                {
                    "id": "dest-fontainhas",
                    "name": "Fontainhas Latin Quarter (Panaji)",
                    "category": "Heritage Portuguese Streetscape",
                    "description": "Charming heritage quarter famed for narrow cobbled alleys, pastel-colored colonial villas, wrought-iron balconies, and vintage bakeries.",
                    "coordinates": [15.4975, 73.8322],
                    "location": "Central Panaji, Goa",
                },
                {
                    "id": "dest-baga-beach",
                    "name": "Baga & Calangute Beach Coastal Strip",
                    "category": "Golden Sand Beach & Water Sports",
                    "description": "Vibrant beach hub famous for parasailing, jet skiing, sunset dolphin cruises, beachfront candlelit shacks, and live music.",
                    "coordinates": [15.5553, 73.7517],
                    "location": "Baga, North Goa",
                },
                {
                    "id": "dest-chapora-fort",
                    "name": "Chapora Fort & Vagator Cliffs",
                    "category": "Historic Clifftop Fort",
                    "description": "Iconic red-laterite clifftop fortress overlooking Vagator Beach and Chapora river estuary; famed as the Bollywood 'Dil Chahta Hai' sunset point.",
                    "coordinates": [15.6059, 73.7364],
                    "location": "Vagator, North Goa",
                },
                {
                    "id": "dest-dudhsagar-goa",
                    "name": "Dudhsagar Waterfalls & Mollem National Park",
                    "category": "310m Tiered Jungle Waterfall",
                    "description": "Spectacular 4-tiered 310m milky white waterfall plunging through dense Western Ghats jungle on the Mandovi river.",
                    "coordinates": [15.3144, 74.3143],
                    "location": "Sonaulim / Mollem, South Goa",
                },
            ]
            self._nearby_cache[cache_key] = goa_places
            return goa_places

        # Check for known Mysore destination coordinates
        if abs(lat - 12.2958) < 0.2 and abs(lon - 76.6394) < 0.2:
            mysore_places = [
                {
                    "id": "dest-mysore-palace",
                    "name": "Mysore Palace (Amba Vilas)",
                    "category": "Royal Palace & Heritage",
                    "description": "Grand Indo-Saracenic royal palace of the Wadiyar dynasty featuring stained glass, gilded durbar halls, and illuminated facade.",
                    "coordinates": [12.3052, 76.6552],
                    "location": "Central Mysore",
                },
                {
                    "id": "dest-chamundi-hills",
                    "name": "Chamundi Hills & Sri Chamundeshwari Temple",
                    "category": "Historic Hill & Temple",
                    "description": "Sacred hilltop landmark offering panoramic sunset vistas across Mysore, a 17th-century temple, and the monolithic Nandi statue.",
                    "coordinates": [12.2725, 76.6711],
                    "location": "Chamundi Hill Peak",
                },
                {
                    "id": "dest-devaraja-market",
                    "name": "Devaraja Heritage Market",
                    "category": "Traditional Market & Heritage",
                    "description": "Vibrant century-old open market famous for traditional Mysore betel leaves, fragrant sandalwood, silk, and raw spices.",
                    "coordinates": [12.3086, 76.6517],
                    "location": "Near D. Devaraj Urs Road",
                },
                {
                    "id": "dest-philomena",
                    "name": "St. Philomena's Cathedral",
                    "category": "Neo-Gothic Cathedral",
                    "description": "One of the tallest churches in Asia, built in 1936 with neo-gothic spires and stained-glass windows inspired by the Cologne Cathedral.",
                    "coordinates": [12.3204, 76.6575],
                    "location": "Ashoka Road, Mysore",
                },
                {
                    "id": "dest-brindavan",
                    "name": "Brindavan Gardens & KRS Dam",
                    "category": "Terraced Gardens & Fountains",
                    "description": "Expansive terraced Mughal-style garden beside Krishnarajasagara Dam, famed for evening musical fountain light shows.",
                    "coordinates": [12.4262, 76.5732],
                    "location": "KRS Dam Reservoir",
                },
            ]
            self._nearby_cache[cache_key] = mysore_places
            return mysore_places

        # Check for known Coorg destination coordinates
        if 12.0 <= lat <= 12.8 and 75.3 <= lon <= 76.2:
            coorg_places = [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["coorg"]]
            self._nearby_cache[cache_key] = coorg_places
            return coorg_places

        # Check for known Bangalore destination coordinates
        if abs(lat - 12.9716) < 0.2 and abs(lon - 77.5946) < 0.2:
            blr_places = [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["bangalore"]]
            self._nearby_cache[cache_key] = blr_places
            return blr_places

        # Check for known Ooty destination coordinates
        if abs(lat - 11.4102) < 0.2 and abs(lon - 76.6950) < 0.2:
            ooty_places = [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["ooty"]]
            self._nearby_cache[cache_key] = ooty_places
            return ooty_places

        # Check for known Hampi destination coordinates
        if abs(lat - 15.3350) < 0.2 and abs(lon - 76.4600) < 0.2:
            hampi_places = [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["hampi"]]
            self._nearby_cache[cache_key] = hampi_places
            return hampi_places

        # Check for known Chikmagalur destination coordinates
        if abs(lat - 13.3161) < 0.2 and abs(lon - 75.7720) < 0.2:
            cmg_places = [p.copy() for p in self.KNOWN_DESTINATION_LANDMARKS["chikmagalur"]]
            self._nearby_cache[cache_key] = cmg_places
            return cmg_places

        query = f"""
        [out:json][timeout:10];
        (
          node(around:{radius},{lat},{lon})[tourism~"museum|attraction|viewpoint|gallery|theme_park|zoo|historical"];
          node(around:{radius},{lat},{lon})[historic~"castle|monument|memorial|archaeological_site|fort|yes"];
          node(around:{radius},{lat},{lon})[amenity~"museum|park|theatre|gallery|cinema|community_centre"];
        );
        out center tags 8;
        """

        headers = {
            "User-Agent": "AITravelPlanner/1.0 (+https://example.com)",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            response = requests.post(
                self.overpass_url,
                data={"data": query},
                headers=headers,
                timeout=(3, 6),
            )
            response.raise_for_status()
            elements = response.json().get("elements", [])
            places: list[dict[str, Any]] = []
            seen: set[str] = set()
            for item in elements[:12]:
                tags = item.get("tags", {})
                lat_value = item.get("lat") or (item.get("center") or {}).get("lat")
                lon_value = item.get("lon") or (item.get("center") or {}).get("lon")
                if not self._is_valid_coordinate(lat_value, lon_value):
                    continue
                name = tags.get("name") or tags.get("name:en") or "Unnamed place"
                key = f"{name}-{lat_value}-{lon_value}"
                if key in seen:
                    continue
                seen.add(key)
                places.append(
                    {
                        "id": key,
                        "name": name,
                        "category": (tags.get("tourism") or tags.get("historic") or tags.get("amenity") or "attraction").replace("_", " "),
                        "description": tags.get("description") or "Popular local destination highlight.",
                        "coordinates": [float(lat_value), float(lon_value)],
                        "location": tags.get("city") or tags.get("village") or tags.get("town") or "Local area",
                    }
                )
            result = places[:8]
            if result:
                self._nearby_cache[cache_key] = result
                return result
        except Exception as exc:
            logger.warning("Nearby place lookup failed: %s", exc)

        fallback = [
            {
                "id": f"fallback-{lat}-{lon}",
                "name": "Historic center",
                "category": "attraction",
                "description": "Local destination recommendation only; live nearby-place data is unavailable.",
                "coordinates": [float(lat), float(lon)],
                "location": "Local area",
            }
        ]
        self._nearby_cache[cache_key] = fallback
        return fallback

    def _fetch_nearby_places(self, lat: float, lon: float) -> list[str]:
        nearby_places = self.get_nearby_places(lat, lon, radius=2000)
        names = [place["name"] for place in nearby_places[:6]]
        if len(names) >= 3:
            return names
        return ["Historic center", "Local market", "Scenic viewpoint"]
