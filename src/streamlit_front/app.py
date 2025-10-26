# streamlit/app.py
"""Point d'entrée principal de l'application TravelTips"""

import streamlit as st
from config import APP_TITLE, APP_ICON, PAGE_LAYOUT
from services.api_client import api_client
from components.search_bar import search_bar

# Configuration de la page
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=PAGE_LAYOUT,
    initial_sidebar_state="expanded",
)

# Sidebar
with st.sidebar:
    search_term = search_bar(
        placeholder="Rechercher un pays par nom (min. 4 caractères)...",
        default_value="",
    )

# Page d'accueil par défaut
st.title(f"{APP_ICON} {APP_TITLE}")
st.markdown("---")

st.write("## Bienvenue sur TravelTips !")
st.write("Explorez les informations sur les pays du monde entier.")

# Vérification de l'état de l'API
with st.spinner("Vérification de la connexion à l'API..."):
    health = api_client.health_check()

    if health:
        st.success("✅ API connectée")
    else:
        st.error("❌ Impossible de se connecter à l'API")
        st.info("Assurez-vous que le backend FastAPI est lancé")

# Navigation
st.markdown("---")
st.write("### 📍 Navigation")
st.write("Utilisez la barre latérale pour accéder aux différentes pages :")
st.write("- 🏠 **Accueil** : Page principale")
st.write("- 🌍 **Pays** : Affichage des informations des pays")
st.write("- 🔎 **Recherche** : Actualisations de la page Pays")

# Statistiques rapides
st.markdown("---")
st.write("### 📊 Statistiques")

col1, col2, col3 = st.columns(3)

with col1:
    with st.spinner("Chargement..."):
        countries = api_client.get_all_countries(limit=500)
        if countries:
            st.metric("Pays disponibles", len(countries))
        else:
            st.metric("Pays disponibles", "N/A")

with col2:
    st.metric("Fonctionnalités", "5+")

with col3:
    st.metric("Langues", "Multi")
