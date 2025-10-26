# streamlit/services/api_client.py
"""Client pour les appels API vers le backend FastAPI"""

import requests
import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import date
import sys
import os

# Ajouter le dossier parent au path pour importer config
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import API_BASE_URL, API_ROUTES, API_TIMEOUT, CACHE_TTL


class TravelTipsAPI:
    """Client API pour TravelTips"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Méthode générique pour les requêtes HTTP"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(
                method=method,
                url=url,
                timeout=kwargs.pop("timeout", API_TIMEOUT),
                **kwargs,
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                st.warning("Aucune donnée trouvée")
                return None
            else:
                st.error(f"Erreur API ({response.status_code})")
                return None

        except requests.exceptions.ConnectionError:
            st.error("❌ Impossible de se connecter à l'API")
            return None
        except requests.exceptions.Timeout:
            st.error("⏱️ Timeout: le serveur met trop de temps à répondre")
            return None
        except Exception as e:
            st.error(f"Erreur inattendue: {str(e)}")
            return None

    # === COUNTRIES ===

    @st.cache_data(ttl=CACHE_TTL)
    def get_all_countries(
        _self, skip: int = 0, limit: int = 100
    ) -> Optional[List[Dict]]:
        """Liste tous les pays avec pagination"""
        endpoint = API_ROUTES["countries_all"]
        return _self._make_request(
            "GET", endpoint, params={"skip": skip, "limit": limit}
        )

    @st.cache_data(ttl=CACHE_TTL)
    def get_country_by_id(_self, alpha2: str) -> Optional[Dict]:
        """Récupère un pays par son code ISO alpha-2"""
        endpoint = API_ROUTES["country_by_id"].format(alpha2=alpha2)
        return _self._make_request("GET", endpoint)

    @st.cache_data(ttl=CACHE_TTL)
    def search_countries_by_name(_self, name: str) -> Optional[List[Dict]]:
        """Recherche des pays par nom (min 4 caractères)"""
        if len(name) < 4:
            st.warning("Le nom doit contenir au moins 4 caractères")
            return None
        endpoint = API_ROUTES["country_by_name"].format(name=name)
        return _self._make_request("GET", endpoint)

    # === MÉTÉO ===

    @st.cache_data(ttl=CACHE_TTL)
    def get_meteo_for_city(
        _self,
        geoname_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Optional[List[Dict]]:
        """Récupère les données météo hebdomadaires pour une ville"""
        endpoint = API_ROUTES["meteo"].format(geoname_id=geoname_id)
        params = {}

        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        return _self._make_request("GET", endpoint, params=params)

    # === CONVERSATIONS ===

    @st.cache_data()
    def get_conversations_by_lang(
        _self, lang_code: str, limit: int = 100
    ) -> Optional[List[Dict]]:
        """Récupère les conversations par code langue (ISO 639-2)"""
        if len(lang_code) != 3:
            st.warning(
                "Le code langue doit contenir exactement 3 caractères (ISO 639-2)"
            )
            return None
        endpoint = API_ROUTES["conversations"].format(lang_code=lang_code)
        return _self._make_request("GET", endpoint, params={"limit": limit})

    # === ÉLECTRICITÉ ===

    @st.cache_data(ttl=CACHE_TTL)
    def get_countries_by_plug_type(_self, plug_type: str) -> Optional[List[Dict]]:
        endpoint = API_ROUTES["country_by_plug"].format(plug_type=plug_type)
        return _self._make_request("GET", endpoint)

    # === HEALTH ===

    def health_check(_self) -> Optional[Dict]:
        """Vérifie l'état de l'API"""
        endpoint = API_ROUTES["health"]
        return _self._make_request("GET", endpoint)


# Instance globale du client API
api_client = TravelTipsAPI()
