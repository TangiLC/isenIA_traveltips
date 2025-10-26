# streamlit/components/elec.py
"""Composant pour afficher les informations électriques d'un pays"""

import streamlit as st
from typing import Dict
from pathlib import Path
from services.api_client import api_client

base = Path(__file__).parent.parent.parent
img_path = base / "static" / "assets" / "elec"


def elec_component(country_data: Dict):
    """
    Composant pour afficher les informations électriques (voltage, fréquence, prises)

    Args:
        country_data: Données du pays contenant electricity (ElectricityInfo)
    """
    electricity_list = country_data.get("electricity", [])

    if not electricity_list:
        st.info("Aucune information électrique disponible pour ce pays")
        return

    st.subheader("⚡ Informations électriques")

    # Récupérer voltage et fréquence (identiques pour toutes les prises normalement)
    first_elec = electricity_list[0] if electricity_list else {}
    voltage = first_elec.get("voltage", "N/A")
    frequency = first_elec.get("frequency", "N/A")

    # Afficher les infos générales
    col1, col2 = st.columns(2)

    with col1:
        st.metric("⚡ Voltage", voltage)

    with col2:
        st.metric("🔌 Fréquence", frequency)

    st.markdown("---")

    # Afficher les types de prises
    st.write("### 🔌 Types de prises")

    # Afficher en grille
    cols = st.columns(min(len(electricity_list), 4))

    for i, elec_info in enumerate(electricity_list):
        with cols[i % 4]:
            plug_type = elec_info.get("plug_type", "N/A")
            plug_png = elec_info.get("plug_png", "")
            sock_png = elec_info.get("sock_png", "")
            countries = (
                api_client.get_countries_by_plug_type(plug_type)
                if plug_type != "N/A"
                else []
            )

            st.write(f"**Type {plug_type}**")

            # --- Images en ligne 50/50 ---
            col_img_plug, col_img_sock = st.columns(2)

            with col_img_plug:
                if plug_png:
                    plug_path = f"{img_path}/{plug_png}"
                    try:
                        st.image(
                            plug_path,
                            caption=f"Prise {plug_type}",
                            use_container_width=True,
                        )
                    except Exception:
                        st.caption(f"Prise {plug_type}")
                else:
                    st.caption(f"Prise {plug_type}")

            with col_img_sock:
                if sock_png:
                    sock_path = f"{img_path}/{sock_png}"
                    try:
                        st.image(
                            sock_path,
                            caption=f"Socket {plug_type}",
                            use_container_width=True,
                        )
                    except Exception:
                        st.caption(f"Socket {plug_type}")
                else:
                    st.caption(f"Socket {plug_type}")

            # --- Pays utilisant ce type de prise ---
            count = len(countries or [])
            display_countries = countries[:10] if count > 6 else countries

            if count == 0:
                st.caption("Aucun pays trouvé pour ce type de prise.")
            elif count == 1:
                st.caption("Ce type de prise n'est utilisé que dans ce pays :")
            elif count < 6:
                st.caption(
                    f"Ce type de prise est utilisé dans les {count} pays suivants :"
                )
            else:
                st.caption(f"Ce type de prise est utilisé dans {count} pays, dont :")

            # Pile de boutons (remplace l'affichage JSON)
            if display_countries:
                for c in display_countries:
                    code = c.get("iso3166a2", "N/A")
                    name = c.get("name_fr") or c.get("name_en") or code
                    label = f"{code} — {name}"
                    if st.button(
                        label,
                        key=f"country_{plug_type}_{code}",
                        use_container_width=True,
                    ):
                        st.query_params["alpha2"] = code
                        st.rerun()
    # Information additionnelle
    st.markdown("---")
    st.info(
        "💡 **Conseil voyage :** Vérifiez toujours la compatibilité de vos appareils "
        "et prévoyez un adaptateur universel si nécessaire."
    )
