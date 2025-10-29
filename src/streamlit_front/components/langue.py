# streamlit/components/langue.py
"""Composant pour afficher les langues parlées dans un pays"""

import streamlit as st
from typing import Dict
import sys
import os

# Ajouter le dossier parent au path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from services.api_client import api_client


def langue_component(country_data: Dict):
    """
    Composant pour afficher les langues parlées dans un pays
    et lien vers les conversations

    Args:
        country_data: Données du pays contenant langues (LangueInfo)
    """
    langues = country_data.get("langues", [])

    if not langues:
        st.info("Aucune information linguistique disponible pour ce pays")
        return

    st.subheader(f"💬 Langues ({len(langues)})")

    # Initialiser le state pour gérer l'affichage des conversations
    if "loaded_conversations" not in st.session_state:
        st.session_state.loaded_conversations = set()

    for langue in langues:
        iso639_2 = langue.get("iso639_2", "N/A")
        name_fr = langue.get("name_fr", "N/A")
        name_en = langue.get("name_en", "N/A")
        name_local = langue.get("name_local", "N/A")
        famille_fr = langue.get("famille_fr")
        famille_en = langue.get("famille_en")
        is_in_mongo = langue.get("is_in_mongo")

        with st.expander(f"{name_fr} ({iso639_2})"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Nom français :** {name_fr}")
                st.write(f"**Nom anglais :** {name_en}")
                st.write(f"**Nom local :** {name_local}")

            with col2:
                st.write(f"**Code ISO 639-2 :** {iso639_2}")

                if famille_fr:
                    st.write(f"**Famille (FR) :** {famille_fr}")
                if famille_en:
                    st.write(f"**Famille (EN) :** {famille_en}")

            # Section conversations
            st.markdown("---")
            st.write("**📚 Conversations disponibles**")

            if is_in_mongo:
                # Vérifier si les conversations sont déjà chargées
                is_loaded = iso639_2 in st.session_state.loaded_conversations

                col_btn1, col_btn2 = st.columns([1, 1])

                with col_btn1:
                    if not is_loaded:
                        if st.button(
                            f"Charger les conversations en {name_fr}",
                            key=f"load_conv_{iso639_2}",
                            use_container_width=True,
                        ):
                            st.session_state.loaded_conversations.add(iso639_2)
                            st.rerun()
                    else:
                        if st.button(
                            f"Masquer les conversations",
                            key=f"hide_conv_{iso639_2}",
                            use_container_width=True,
                        ):
                            st.session_state.loaded_conversations.discard(iso639_2)
                            st.rerun()

                # Afficher les conversations si chargées
                if is_loaded:
                    with st.spinner(f"Chargement des conversations en {name_fr}..."):
                        conversations = api_client.get_conversations_by_lang(iso639_2)

                        if conversations:
                            st.success("✅ Conversations trouvées")

                            conversation = conversations[0]
                            sentences = conversation.get("sentences", {})

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.subheader("Salutations")
                                st.write(
                                    f"*Bonjour* : {sentences.get('GREETING_INFORMAL', '—')}"
                                )
                                st.write(
                                    f"*Bonsoir* : {sentences.get('GREETING_EVENING', '—')}"
                                )
                                st.write(
                                    f"*Au revoir* : {sentences.get('GREETING_DEPARTURE', '—')}"
                                )
                                st.write(f"*Merci* : {sentences.get('THANKS', '—')}")
                                st.write(f"*SVP* : {sentences.get('PLEASE', '—')}")
                                st.write(
                                    f"*Je me nomme...* : {sentences.get('GIVE_OWN_NAME', '—')}"
                                )

                            with col2:
                                st.subheader("Nourriture")
                                st.write(
                                    f"*Repas de midi* : {sentences.get('MEAL_NOON', '—')}"
                                )
                                st.write(
                                    f"*Dîner* : {sentences.get('MEAL_EVENING', '—')}"
                                )
                                st.write(f"*Pain* : {sentences.get('BREAD', '—')}")
                                st.write(f"*Thé* : {sentences.get('TEA', '—')}")
                                st.write(f"*Café* : {sentences.get('COFFEE', '—')}")
                                st.write(f"*Bière* : {sentences.get('BEER', '—')}")

                            with col3:
                                st.subheader("Utilitaire")
                                st.write(
                                    f"*Toilettes* : {sentences.get('TOILET', '—')}"
                                )
                                st.write(
                                    f"*Téléphone portable* : {sentences.get('CELLPHONE', '—')}"
                                )
                                st.write(
                                    f"*Souhaite prendre une douche* : {sentences.get('NEED_SHOWER', '—')}"
                                )
                                st.write(
                                    f"*où acheter ...* : {sentences.get('LOCATION_X_Q', '—')}"
                                )
                                st.write(
                                    f"*Réseau internet* : {sentences.get('INTERNET_CONNECTION', '—')}"
                                )
                                st.write(
                                    f"*Batterie* : {sentences.get('BATTERY', '—')}"
                                )
                        else:
                            st.warning(f"Aucune conversation trouvée en {name_fr}")
            else:
                st.warning(f"Aucune conversation disponible en {name_fr}")
