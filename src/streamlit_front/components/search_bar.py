# streamlit/components/search_bar.py
"""Composant barre de recherche réutilisable"""

import streamlit as st
from typing import Optional, Callable


def search_bar(
    placeholder: str = "Rechercher...",
    default_value: str = "",
    button_label: str = "🔍",
    on_search: Optional[Callable[[str], None]] = None,
    min_length: int = 0,
) -> str:
    """
    Composant barre de recherche avec bouton

    Args:
        placeholder: Texte du placeholder
        default_value: Valeur par défaut
        button_label: Label du bouton de recherche
        on_search: Callback appelé lors de la recherche
        min_length: Longueur minimale pour déclencher la recherche

    Returns:
        str: Terme de recherche
    """
    row1 = st.container()
    row2 = st.container()

    with row1:
        search_term = st.text_input(
            "search",
            value=default_value,
            placeholder=placeholder,
            label_visibility="collapsed",
            key="search_input",
        )

    with row2:
        search_clicked = st.button(
            button_label, use_container_width=True, key="search_button"
        )

    # Déclencher la recherche si callback fourni
    if on_search and (search_clicked or search_term):
        if min_length == 0 or len(search_term) >= min_length:
            on_search(search_term)

    # Afficher un warning si longueur minimale non atteinte
    if min_length > 0 and search_term and len(search_term) < min_length:
        st.warning(f"Veuillez entrer au moins {min_length} caractères")

    return search_term
