# streamlit/components/header.py
"""Composant header réutilisable"""

import streamlit as st
from typing import Optional


def header_component(
    title: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
    show_divider: bool = True,
):
    """
    Composant header avec titre, sous-titre et icône

    Args:
        title: Titre principal
        subtitle: Sous-titre optionnel
        icon: Icône emoji optionnelle
        show_divider: Afficher une ligne de séparation
    """
    # TODO: Implémenter le composant header

    if icon:
        st.title(f"{icon} {title}")
    else:
        st.title(title)

    if subtitle:
        st.markdown(f"*{subtitle}*")

    if show_divider:
        st.markdown("---")
