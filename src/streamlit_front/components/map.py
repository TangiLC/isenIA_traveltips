# streamlit/components/map.py
"""Composant carte interactive"""

from typing import Dict, List
import streamlit as st
import pandas as pd
import pydeck as pdk


def map_component(country_data: Dict, zoom: int = 5, show_quick: bool = True):
    """
    Affiche une carte unique (villes principales) sur 3/4 de la largeur
    et une colonne de navigation (1/4) listant les pays frontaliers
    et, optionnellement, des boutons de pays rapides.
    """

    # Prépare villes principales
    cities: List[Dict] = country_data.get("cities", []) or []
    rows = []
    for c in cities:
        lat, lon = c.get("latitude"), c.get("longitude")
        if lat is None or lon is None:
            continue
        is_capital = bool(c.get("is_capital", False))
        # Couleur contour différente pour capitale
        line_color = [20, 110, 240, 200] if not is_capital else [240, 120, 20, 230]
        rows.append(
            {
                "lat": float(lat),
                "lon": float(lon),
                "name": c.get("name_en", "N/A"),
                "is_capital": is_capital,
                "line_color": line_color,
                "radius_m": 4000 if not is_capital else 6000,
            }
        )

    # Prépare pays frontaliers
    borders: List[Dict] = country_data.get("borders", []) or []

    # Mise en page 3/4 - 1/4
    left, right = st.columns([3, 1], vertical_alignment="top")

    # Colonne gauche: carte unique
    with left:
        if not rows:
            st.warning("Aucune ville principale avec coordonnées disponibles")
        else:
            df = pd.DataFrame(rows)
            view = pdk.ViewState(
                latitude=float(df["lat"].mean()),
                longitude=float(df["lon"].mean()),
                zoom=float(zoom),
                pitch=0,
                bearing=0,
            )

            # Marqueurs: remplissage transparent, contour coloré
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[lon, lat]",
                stroked=True,
                filled=True,
                get_fill_color="[0,0,200,90]",
                get_line_color="line_color",
                get_radius="radius_m",
                radius_min_pixels=3,
                radius_max_pixels=40,
                pickable=True,
            )

            # Fond open-source (pas de token requis)
            map_style = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"

            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view,
                map_style=map_style,
                tooltip={"text": "{name}"},
            )

            st.subheader("Villes principales")
            st.pydeck_chart(deck, use_container_width=True, height=480)

    # Colonne droite: navigation
    with right:

        st.caption("Pays frontaliers")

        if not borders:
            st.write("Aucun pays frontalier")
        else:
            # Une seule colonne de boutons empilés
            for b in borders:
                code = b.get("iso3166a2", "N/A")
                name = b.get("name_fr") or b.get("name_en") or code
                if st.button(
                    f"{code} — {name}", key=f"border_{code}", use_container_width=True
                ):
                    st.query_params["alpha2"] = code
                    st.rerun()
