# streamlit/pages/accueil.py
"""Page d'accueil de l'application"""

import streamlit as st
import sys
import os

# Ajouter le dossier parent au path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import APP_TITLE, APP_ICON, PAGE_LAYOUT, PAGES_CONFIG
from services.api_client import api_client
from components.search_bar import search_bar

# Configuration de la page
st.set_page_config(
    page_title=f"{APP_TITLE} - Accueil",
    page_icon=PAGES_CONFIG["accueil"]["icon"],
    layout=PAGE_LAYOUT,
)

# Sidebar
with st.sidebar:
    search_term = search_bar(
        placeholder="Rechercher un pays par nom (min. 4 caractères)...",
        default_value="",
    )

# En-tête
st.title(f"{PAGES_CONFIG['accueil']['icon']} {PAGES_CONFIG['accueil']['title']}")
st.markdown("---")

# Contenu principal
st.write("## Bienvenue sur TravelTips")
st.write(
    """
Cette application vous permet d'explorer les informations détaillées 
sur les pays du monde entier.
"""
)

# Section fonctionnalités
st.markdown("---")
st.write("### Fonctionnalités")

col1, col2, col3 = st.columns(3)

with col1:
    st.write("**🌍 Exploration des pays**")
    st.write(" - Recherche par nom complet ou partiel")
    st.write(" - Informations détaillées")
    st.write(" - Pays frontaliers")

    st.write("**🌤️ Données météo**")
    st.write("   - Relevés annuels températures et précipitations (par 15j)")
    st.write("   - Historique disponible")

with col2:
    st.write("**💬 Conversations**")
    st.write("   - Par langue")
    st.write("   - Support multilingue")

    st.write("**📊 Visualisations**")
    st.write("   - Cartes interactives")
    st.write("   - Graphiques météo")

with col3:
    st.write("**⚡ Normes électriques**")
    st.write("   - Prises utilisées")
    st.write("   - Équivalents autres pays")

    st.write("**💵 Monnaie**")
    st.write("   - Monnaie en cours")

# Section quick start
st.markdown("---")
st.write("### ⚡ Quick Start")

quick_countries = ["FR", "US", "JP", "DE", "IT", "ES"]
cols = st.columns(len(quick_countries))

for i, code in enumerate(quick_countries):
    with cols[i]:
        if st.button(code, key=f"quick_{code}", use_container_width=True):
            st.switch_page("pages/pays.py")
            st.query_params["alpha2"] = code

# Footer
st.markdown("---")
st.caption("TravelTips API - 2025")
