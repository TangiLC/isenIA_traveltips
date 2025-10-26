# streamlit/components/monnaie.py
"""Composant pour afficher les monnaies d'un pays"""

import streamlit as st
from typing import Dict


def monnaie_component(country_data: Dict):
    """
    Composant pour afficher les monnaies utilisées dans un pays

    Args:
        country_data: Données du pays contenant currencies (CurrencyInfo)
    """
    currencies = country_data.get("currencies", [])

    if not currencies:
        st.info("Aucune information monétaire disponible pour ce pays")
        return

    st.subheader(f"💰 Monnaie(s) ({len(currencies)})")

    for i, currency in enumerate(currencies):
        iso4217 = currency.get("iso4217", "N/A")
        name = currency.get("name", "N/A")
        symbol = currency.get("symbol", "N/A")

        with st.container():
            # En-tête de la monnaie
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.write(f"### {symbol} {name}")

            with col2:
                st.metric("Code ISO", iso4217)

            with col3:
                st.metric("Symbole", symbol)

            # Informations détaillées dans un expander
            with st.expander("ℹ️ Détails et informations"):
                info_col1, info_col2 = st.columns(2)

                with info_col1:
                    st.write("**Informations**")
                    st.write(f"- Nom complet : {name}")
                    st.write(f"- Code ISO 4217 : {iso4217}")
                    st.write(f"- Symbole : {symbol}")

                with info_col2:
                    st.write("**Qu'est-ce que le code ISO 4217 ?**")
                    st.write(
                        """Le code ISO 4217 est un standard international définissant les codes à trois lettres 
        pour les devises.\nLes deux premières lettres représentent généralement le code pays (ISO 3166), 
        et la troisième lettre représente la première lettre du nom de la devise."""
                    )

                # Note informative
                st.info(
                    "**Taux de change :** Ce site ne donne pas les taux en temps réél. "
                )

            # Séparateur entre les monnaies
            if i < len(currencies) - 1:
                st.markdown("---")

    # Avertissement si plusieurs monnaies
    if len(currencies) > 1:
        st.markdown("---")
        st.warning(
            "⚠️ **Attention :** Ce pays utilise plusieurs monnaies. "
            "Renseignez-vous sur celle acceptée dans votre région de destination "
            "avant votre voyage."
        )
