# streamlit/components/ville.py
"""Composant pour afficher les villes d'un pays"""

import streamlit as st
from typing import Dict
import sys
import os
import pandas as pd
import pydeck as pdk
import altair as alt

# Ajouter le dossier parent au path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from services.api_client import api_client


def render_city_map(lat: float, lon: float, zoom: int = 9, height: int = 220):
    map_style = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    data = pd.DataFrame([{"lat": lat, "lon": lon}])
    view = pdk.ViewState(latitude=lat, longitude=lon, zoom=zoom, pitch=0, bearing=0)
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=data,
        get_position="[lon, lat]",
        get_radius=5000,
        radius_min_pixels=3,
        radius_max_pixels=30,
        get_fill_color="[200, 80,80, 100]",
        get_line_color="[0, 80, 200, 200]",
        pickable=False,
    )
    deck = pdk.Deck(layers=[layer], initial_view_state=view, map_style=map_style)
    st.pydeck_chart(deck, use_container_width=True, height=height)


def render_meteo_timeline(meteo_data):
    """
    Affiche un graphique combiné des températures et précipitations sur l'année.

    Args:
        meteo_data: Liste de dictionnaires contenant les données météo hebdomadaires
                   avec les clés: week_start_date, week_end_date, temperature_max_avg,
                   temperature_min_avg, precipitation_sum
    """
    # Vérifier si les données existent
    if not meteo_data:
        st.warning("Aucune donnée météo disponible")
        return

    # Créer le DataFrame
    df = pd.DataFrame(meteo_data)

    # Convertir les dates
    for c in ("week_start_date", "week_end_date"):
        df[c] = pd.to_datetime(df[c], errors="coerce")

    # Filtrer les lignes avec au moins une valeur non nulle
    df = df[
        df[["temperature_max_avg", "temperature_min_avg", "precipitation_sum"]]
        .notna()
        .any(axis=1)
    ].copy()

    if df.empty:
        st.warning("Données météo présentes mais toutes nulles")
        return

    # Calculer la date du milieu de la semaine pour un affichage plus précis
    df["date"] = (
        df["week_start_date"] + (df["week_end_date"] - df["week_start_date"]) / 2
    )

    # Formater les dates pour l'affichage dans les tooltips
    df["semaine"] = (
        df["week_start_date"].dt.strftime("%d/%m")
        + " - "
        + df["week_end_date"].dt.strftime("%d/%m/%Y")
    )

    # Préparer les données pour les températures (pivot long pour Altair)
    temp_df = df.melt(
        id_vars=["date", "semaine", "precipitation_sum", "week_start_date"],
        value_vars=["temperature_max_avg", "temperature_min_avg"],
        var_name="type",
        value_name="value",
    )

    # Ajouter un label lisible pour le type de température
    temp_df["temp_label"] = temp_df["type"].map(
        {"temperature_max_avg": "Temp. Max", "temperature_min_avg": "Temp. Min"}
    )

    # ===== LAYER 1: Histogramme des précipitations (barres bleues) =====
    bars = (
        alt.Chart(df)
        .mark_bar(opacity=0.7, color="#9ecae1")
        .encode(
            x=alt.X(
                "week_start_date:T",
                title="Météo annuelle",
                axis=alt.Axis(format="%b %Y"),
            ),
            y=alt.Y(
                "precipitation_sum:Q",
                title="Précipitations (mm)",
                axis=alt.Axis(orient="left"),
            ),
            tooltip=[
                alt.Tooltip("semaine:N", title="Semaine"),
                alt.Tooltip(
                    "precipitation_sum:Q", title="Précipitations (mm)", format=".1f"
                ),
            ],
        )
    )

    # ===== LAYER 2: Courbes des températures (lignes) =====
    lines = (
        alt.Chart(temp_df)
        .mark_line(point=False, strokeWidth=2.5)
        .encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("value:Q", title="Température (°C)", axis=alt.Axis(orient="right")),
            color=alt.Color(
                "type:N",
                title="Température",
                scale=alt.Scale(
                    domain=["temperature_max_avg", "temperature_min_avg"],
                    range=["#d62728", "#1f77b4"],
                ),
                legend=alt.Legend(
                    labelExpr="datum.value === 'temperature_max_avg' ? 'Max' : 'Min'",
                    orient="top-right",
                ),
            ),
            tooltip=[
                alt.Tooltip("semaine:N", title="Semaine"),
                alt.Tooltip("temp_label:N", title="Type"),
                alt.Tooltip("value:Q", title="Température (°C)", format=".1f"),
                alt.Tooltip(
                    "precipitation_sum:Q", title="Précipitations (mm)", format=".1f"
                ),
            ],
        )
    )

    # ===== LAYER 3: Points pour améliorer l'interactivité =====
    points = (
        alt.Chart(temp_df)
        .mark_circle(size=80, opacity=0.8)
        .encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("value:Q", axis=None),
            color=alt.Color(
                "type:N",
                scale=alt.Scale(
                    domain=["temperature_max_avg", "temperature_min_avg"],
                    range=["#d62728", "#1f77b4"],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("semaine:N", title="Semaine"),
                alt.Tooltip("temp_label:N", title="Type"),
                alt.Tooltip("value:Q", title="Température (°C)", format=".1f"),
                alt.Tooltip(
                    "precipitation_sum:Q", title="Précipitations (mm)", format=".1f"
                ),
            ],
        )
    )

    # ===== Assemblage final =====
    chart = (
        alt.layer(bars, lines, points)
        .resolve_scale(y="independent")  # Deux axes Y indépendants
        .properties(height=350, title="Évolution météo annuelle")
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(chart, use_container_width=True)


def ville_component(country_data: Dict):
    cities = country_data.get("cities", [])
    if not cities:
        st.info("Aucune ville disponible pour ce pays")
        return

    # État persistant pour les données météo et leur affichage
    if "meteo_cache" not in st.session_state:
        st.session_state.meteo_cache = {}
    if "meteo_visible" not in st.session_state:
        st.session_state.meteo_visible = set()

    def get_meteo_cached(geoname_id: int):
        """Charge les données météo une seule fois et les garde en cache"""
        if geoname_id not in st.session_state.meteo_cache:
            with st.spinner("Chargement météo..."):
                st.session_state.meteo_cache[geoname_id] = (
                    api_client.get_meteo_for_city(geoname_id)
                )
        return st.session_state.meteo_cache[geoname_id]

    def render_city_card(city: Dict, is_capital: bool = False):
        name = city.get("name_en", "N/A")
        geoname_id = city.get("geoname_id")
        tag = "🏢" if is_capital else ""
        bold = "**" if is_capital else ""

        # L'expander reste toujours ouvert s'il y a des données météo chargées
        has_meteo_data = geoname_id in st.session_state.meteo_cache
        expanded = has_meteo_data

        with st.expander(f"{bold}{name}{bold} {tag}", expanded=expanded):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Geoname ID:** {geoname_id or 'N/A'}")
                lat, lon = city.get("latitude"), city.get("longitude")
                if lat and lon:
                    render_city_map(lat, lon, zoom=7, height=250)
                    st.write(f"**Coordonnées:** {lat:.4f}, {lon:.4f}")

                if geoname_id:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("⛅ Voir météo", key=f"open_{geoname_id}"):
                            # Charger les données ET les rendre visibles
                            get_meteo_cached(geoname_id)
                            st.session_state.meteo_visible.add(geoname_id)
                    with c2:
                        if st.button("🔽 Fermer", key=f"close_{geoname_id}"):
                            # Masquer le graphique (mais garder les données en cache)
                            st.session_state.meteo_visible.discard(geoname_id)
                    with c3:
                        st.caption("by Open-Meteo.com")

            with col2:
                # Afficher la météo SI elle est visible
                if geoname_id and geoname_id in st.session_state.meteo_visible:
                    meteo_data = st.session_state.meteo_cache.get(geoname_id)
                    if meteo_data:
                        render_meteo_timeline(meteo_data)
                    else:
                        st.warning("Données météo non disponibles")

    st.subheader(f"Villes ({len(cities)})")

    # Séparer capitale et autres
    capital = [c for c in cities if c.get("is_capital", False)]
    other_cities = [c for c in cities if not c.get("is_capital", False)]

    # Ligne 1 : capitale seule (si présente)
    if capital:
        render_city_card(capital[0], is_capital=True)

    # Lignes suivantes : 2 villes par ligne
    for i in range(0, len(other_cities), 2):
        pair = other_cities[i : i + 2]
        cols = st.columns(2)
        with cols[0]:
            render_city_card(pair[0], is_capital=False)
        if len(pair) == 2:
            with cols[1]:
                render_city_card(pair[1], is_capital=False)
