# streamlit/config.py
"""Configuration globale de l'application Streamlit"""

import os
from typing import Dict

# Configuration API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = 10  # secondes

# Configuration de l'application
APP_TITLE = "TravelTips"
APP_ICON = "🌍"
PAGE_LAYOUT = "wide"

# Routes API
API_ROUTES: Dict[str, str] = {
    "countries_all": "/api/countries/",
    "country_by_id": "/api/countries/by_id/{alpha2}",
    "country_by_name": "/api/countries/by_name/{name}",
    "meteo": "/api/meteo/{geoname_id}",
    "conversations": "/api/conversations/by_lang/{lang_code}",
    "country_by_plug": "/api/electricite/{plug_type}/countries",
    "health": "/health",
}

# Configuration des pages
PAGES_CONFIG = {
    "accueil": {"title": "Accueil", "icon": "🏠"},
    "pays": {"title": "Pays", "icon": "🌍"},
}

# Cache TTL (Time To Live) en secondes
CACHE_TTL = 600  # 10 minutes
