import re
import unicodedata
from datetime import datetime
from typing import Tuple, List
import pandas as pd


class ETLUtils:
    """Classe utilitaire regroupant les méthodes communes aux différents ETL"""

    # ========== NORMALISATION ET SIMILARITÉ DE TEXTE ==========
    # Méthodes issues de etl_villes.py

    @staticmethod
    def normalize(s: str) -> str:
        """
        Normalise une chaîne : supprime accents, minuscules, sans ponctuation.

        Args:
            s: Chaîne à normaliser

        Returns:
            Chaîne normalisée
        """
        if s is None:
            return ""
        # Décomposition unicode pour séparer caractères et accents
        s = unicodedata.normalize("NFD", s)
        # Supprime les marques diacritiques (accents)
        s = "".join(char for char in s if unicodedata.category(char) != "Mn")
        s = s.lower()
        # Supprime la ponctuation
        s = re.sub(r"[^\w\s]", "", s)
        # Normalise les espaces
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @staticmethod
    def levenshtein(a: str, b: str) -> int:
        """
        Calcule la distance de Levenshtein entre deux chaînes.

        Args:
            a: Première chaîne
            b: Deuxième chaîne

        Returns:
            Distance de Levenshtein (nombre d'opérations)

        """
        if a == b:
            return 0
        if len(a) < len(b):
            a, b = b, a
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cost = 0 if ca == cb else 1
                cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
            prev = cur
        return prev[-1]

    @staticmethod
    def similarity(a: str, b: str) -> float:
        """
        Calcule la similarité entre deux chaînes (0.0 à 1.0).
        Utilise la distance de Levenshtein normalisée.

        Args:
            a: Première chaîne
            b: Deuxième chaîne

        Returns:
            Score de similarité (1.0 = identique, 0.0 = totalement différent)

        """
        a_n = ETLUtils.normalize(a)
        b_n = ETLUtils.normalize(b)
        if not a_n and not b_n:
            return 1.0
        dist = ETLUtils.levenshtein(a_n, b_n)
        max_len = max(len(a_n), len(b_n))
        if max_len == 0:
            return 1.0
        return 1.0 - dist / max_len

    # ========== MANIPULATION DE CHAÎNES ==========

    @staticmethod
    def strip_parentheses(text: str) -> str:
        """
        Supprime toutes les portions entre parenthèses et normalise les espaces.
        Méthode issue de elec_scrap2.py

        Args:
            text: Texte à nettoyer

        Returns:
            Texte sans parenthèses, espaces normalisés

        """
        if not text:
            return ""
        # Supprime tout ce qui est entre parenthèses
        s = re.sub(r"\s*\([^)]*\)", "", text)
        # Normalise les espaces autour des slashes
        s = re.sub(r"\s*/\s*", " / ", s)
        # Condense les espaces multiples
        s = re.sub(r"\s{2,}", " ", s).strip()
        return s

    @staticmethod
    def escape_string(s: str) -> str:
        """
        Échappe les caractères spéciaux pour MySQL.
        Méthode issue de etl_villes.py

        Args:
            s: Chaîne à échapper

        Returns:
            Chaîne échappée pour MySQL

        """
        if s is None:
            return ""
        return s.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')

    @staticmethod
    def split_csv_field(s: str) -> List[str]:
        """
        Découpe un champ CSV contenant des valeurs séparées par des virgules.
        Méthode issue de etl_countries.py

        Args:
            s: Chaîne contenant des valeurs séparées par des virgules

        Returns:
            Liste des valeurs nettoyées (sans espaces, sans valeurs vides)

        """
        if not s:
            return []
        return [x.strip() for x in s.split(",") if x.strip()]

    # ========== CONVERSIONS DE DATES ==========
    # Méthodes issues de etl_meteo.py

    @staticmethod
    def to_date(s: str, format: str = "%Y-%m-%d") -> datetime.date:
        """
        Convertit une chaîne en objet date.

        Args:
            s: Chaîne représentant une date
            format: Format de la date (par défaut ISO: YYYY-MM-DD)

        Returns:
            Objet datetime.date

        """
        return datetime.strptime(s, format).date()

    @staticmethod
    def iso_week_key(d: pd.Timestamp) -> Tuple[int, int]:
        """
        Extrait l'année et le numéro de semaine ISO d'un timestamp.

        Args:
            d: Timestamp pandas

        Returns:
            Tuple (année_iso, semaine_iso)

        """
        iso = d.isocalendar()
        return (iso.year, iso.week)

    # ========== PARSING DE DONNÉES ==========

    @staticmethod
    def parse_lat_lng(latlng_str: str) -> Tuple[str, str]:
        """
        Parse une chaîne "latitude,longitude" en tuple.
        Méthode issue de etl_countries.py

        Args:
            latlng_str: Chaîne au format "lat,lng" (ex: "48.85,2.35")

        Returns:
            Tuple (latitude, longitude) sous forme de strings
            Retourne ("", "") si parsing impossible

        """
        if not latlng_str:
            return ("", "")
        parts = [p.strip() for p in latlng_str.split(",")]
        if len(parts) >= 2:
            return (parts[0], parts[1])
        return ("", "")

    # ========== EXTRACTION DE PATTERNS ==========

    @staticmethod
    def suffix_from_title(title: str) -> str:
        """
        Extrait le suffixe d'un titre (dernier caractère alphanumérique).
        Méthode issue de etl_elec1.py

        Utilisé pour extraire le type de prise depuis "Plug type A" -> "A"

        Args:
            title: Titre à analyser

        Returns:
            Dernier caractère alphanumérique ou "X" si non trouvé

        """
        clean = re.sub(r"[^A-Za-z0-9 ]", "", title or "").strip()
        return clean[-1] if clean else "X"

    # ========== HTML/TEXT PROCESSING ==========
    # Méthode issue de etl_elec1.py

    @staticmethod
    def pre_note_html(html_content: str) -> str:
        """
        Retourne le contenu HTML avant la mention "(note" (insensible à la casse).
        Utilisé pour nettoyer les extraits HTML contenant des notes de bas de page.

        Args:
            html_content: Contenu HTML à nettoyer

        Returns:
            HTML avant "(note", ou HTML complet si pas de note trouvée

        """
        if not html_content:
            return ""
        # Coupe dès '(note' pour exclure tout ce qui suit
        parts = re.split(r"\(note", html_content, flags=re.IGNORECASE)
        return parts[0] if parts else html_content

    # ========== VALIDATION ==========

    @staticmethod
    def is_valid_iso3(code: str) -> bool:
        """
        Vérifie si une chaîne est un code ISO 639-2 valide (3 lettres).

        Args:
            code: Code à valider

        Returns:
            True si code valide (3 lettres exactement)

        """
        if not code or not isinstance(code, str):
            return False
        return bool(re.fullmatch(r"[A-Za-z]{3}", code.strip()))

    @staticmethod
    def is_valid_iso2(code: str) -> bool:
        """
        Vérifie si une chaîne est un code ISO 3166-1 alpha-2 valide (2 lettres).

        Args:
            code: Code à valider

        Returns:
            True si code valide (2 lettres exactement)

        """
        if not code or not isinstance(code, str):
            return False
        return bool(re.fullmatch(r"[A-Za-z]{2}", code.strip()))
