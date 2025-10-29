# streamlit/pages/pays.py
"""Page de consultation et recherche des pays"""

import streamlit as st
import sys
import os
from pathlib import Path

# Ajouter le dossier parent au path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import APP_TITLE, PAGE_LAYOUT, PAGES_CONFIG
from services.api_client import api_client
from components.search_bar import search_bar

# Configuration de la page
st.set_page_config(
    page_title=f"{APP_TITLE} - Pays",
    page_icon=PAGES_CONFIG["pays"]["icon"],
    layout=PAGE_LAYOUT,
)

# CSS personnalisé pour agrandir les onglets
st.markdown(
    """
<style>
    /* Agrandir les onglets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
    }
    
    .stTabs [data-baseweb="tab"] div {
        font-size: 1.8rem !important;
        font-weight: 600;
        border-radius: 8px 8px 0 0;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(151, 166, 195, 0.15);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(28, 131, 225, 0.1);
    }
</style>
""",
    unsafe_allow_html=True,
)

# Récupérer le pays et l'onglet depuis l'URL
query_params = st.query_params
alpha2 = query_params.get("alpha2", "FR")
current_tab = query_params.get("tab", "carte")  # Valeur par défaut : "carte"

# Mapping des noms d'onglets
TAB_MAPPING = {
    "carte": 0,
    "villes": 1,
    "electricite": 2,
    "langues": 3,
    "monnaies": 4,
}

# Sidebar
with st.sidebar:
    search_term = search_bar(
        placeholder="Rechercher un pays par nom (min. 4 caractères)...",
        default_value="",
    )

    # Si recherche par nom
    if search_term and len(search_term) >= 4:
        st.subheader(f"Résultats pour : {search_term}")

        with st.spinner("Recherche en cours..."):
            results = api_client.search_countries_by_name(search_term)

            if results:
                st.write(f"**{len(results)} pays trouvé(s)**")

                for country in results:
                    with st.expander(
                        f"{country.get('name_fr', country.get('name_en', 'N/A'))} ({country.get('iso3166a2', 'N/A')})"
                    ):
                        st.write(f"**Code ISO:** {country.get('iso3166a2', 'N/A')}")
                        st.write(f"**Nom anglais:** {country.get('name_en', 'N/A')}")
                        if st.button(
                            "Voir détails", key=f"view_{country.get('iso3166a2')}"
                        ):
                            st.query_params.update(
                                {
                                    "alpha2": country.get("iso3166a2"),
                                    "tab": current_tab,  # Conserver l'onglet actuel
                                }
                            )
                            st.rerun()
            else:
                st.info("Aucun pays trouvé")

# En-tête
st.title(f"{PAGES_CONFIG['pays']['icon']} {PAGES_CONFIG['pays']['title']}")
st.markdown("---")

# Affichage du pays sélectionné
st.subheader(f"Détails : {alpha2}")

with st.spinner("Chargement des données..."):
    country_data = api_client.get_country_by_id(alpha2)

    if country_data:
        # Informations générales avec drapeau
        col_name, col_flag = st.columns([0.8, 0.2])

        with col_name:
            st.write(
                f"### {country_data.get('name_fr', country_data.get('name_en', 'N/A'))}"
            )

        with col_flag:
            # Charger le drapeau
            base = Path(__file__).parent.parent.parent
            img_path = base / "static" / "assets" / "flags48" / f"{alpha2}.png"

            if img_path.exists():
                st.image(str(img_path), width=96)
            else:
                st.caption(f"🏳️ {alpha2}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Code ISO", country_data.get("iso3166a2", "N/A"))
        with col2:
            st.metric("Code alpha-3", country_data.get("iso3166a3", "N/A"))
        with col3:
            st.metric("Nom anglais", country_data.get("name_en", "N/A"))
        with col4:
            st.metric("Nom local", country_data.get("name_local", "N/A"))

        # Sections détaillées avec composants
        st.markdown("---")

        # Définir les noms des onglets
        tab_names = [
            "🗺️ Carte",
            "🏙️ Villes",
            "⚡ Électricité",
            "💬 Langues",
            "💰 Monnaies",
        ]

        # Déterminer l'onglet par défaut depuis l'URL
        default_index = TAB_MAPPING.get(current_tab, 0)

        # Créer les onglets
        tabs = st.tabs(tab_names)

        # Fonction helper pour mettre à jour l'URL
        def update_tab_in_url(tab_key: str):
            """Met à jour le paramètre 'tab' dans l'URL sans rerun"""
            st.query_params.update({"alpha2": alpha2, "tab": tab_key})

        with tabs[0]:
            from components.map import map_component

            map_component(country_data)
            if current_tab != "carte":
                update_tab_in_url("carte")

        with tabs[1]:
            from components.ville import ville_component

            ville_component(country_data)
            if current_tab != "villes":
                update_tab_in_url("villes")

        with tabs[2]:
            from components.elec import elec_component

            elec_component(country_data)
            if current_tab != "electricite":
                update_tab_in_url("electricite")

        with tabs[3]:
            from components.langue import langue_component

            langue_component(country_data)
            if current_tab != "langues":
                update_tab_in_url("langues")

        with tabs[4]:
            from components.monnaie import monnaie_component

            monnaie_component(country_data)
            if current_tab != "monnaies":
                update_tab_in_url("monnaies")

        # Raccourci
        st.caption("Raccourcis")

        quick_countries = ["FR", "US", "JP", "DE", "IT", "ES", "KR"]

        cols = st.columns(len(quick_countries))
        for i, code in enumerate(quick_countries):
            with cols[i]:
                if st.button(code, key=f"footer_{code}", use_container_width=True):
                    st.query_params.update(
                        {
                            "alpha2": code,
                            "tab": current_tab,  # Conserver l'onglet actuel
                        }
                    )
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.error(f"❌ Impossible de charger les données pour le pays {alpha2}")
