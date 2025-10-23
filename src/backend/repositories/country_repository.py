from typing import Iterable, List, Tuple, Optional, Dict, Any
from connexion.mysql_connect import MySQLConnection
import unicodedata


class CountryRepository:
    """Repository pour Pays et tables de liaison"""

    # --- UTILITAIRES --------------------------------------------------------
    @staticmethod
    def _normalize_string(text: str) -> str:
        """Normalise une chaîne : minuscules, sans accents"""
        text = text.lower().strip()
        # Retirer les accents
        text = "".join(
            c
            for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        return text

    # --- PAYS - LECTURE -----------------------------------------------------
    @staticmethod
    def get_by_alpha2(iso2: str) -> Optional[Dict[str, Any]]:
        """Récupère un pays par son code ISO alpha-2 avec toutes ses relations"""
        iso2 = iso2.lower().strip()

        query = """
            SELECT 
                p.iso3166a2, p.iso3166a3, p.name_en, p.name_fr, p.name_local, 
                p.lat, p.lng
            FROM Pays p
            WHERE p.iso3166a2 = %s
        """
        result = MySQLConnection.execute_query(query, (iso2,))
        if not result:
            return None

        pays = result[0]

        # Récupérer les langues
        langues_query = """
            SELECT iso639_2 FROM Pays_Langues 
            WHERE country_iso3166a2 = %s
        """
        langues = MySQLConnection.execute_query(langues_query, (iso2,))
        pays["langues"] = [l["iso639_2"] for l in langues] if langues else []

        # Récupérer les monnaies
        currencies_query = """
            SELECT currency_iso4217 FROM Pays_Monnaies 
            WHERE country_iso3166a2 = %s
        """
        currencies = MySQLConnection.execute_query(currencies_query, (iso2,))
        pays["currencies"] = (
            [c["currency_iso4217"] for c in currencies] if currencies else []
        )

        # Récupérer les frontières (sans récursivité)
        borders_query = """
            SELECT 
                CASE 
                    WHEN pb.country_iso3166a2 = %s THEN p2.iso3166a2
                    ELSE p1.iso3166a2
                END as iso3166a2,
                CASE 
                    WHEN pb.country_iso3166a2 = %s THEN p2.name_en
                    ELSE p1.name_en
                END as name_en,
                CASE 
                    WHEN pb.country_iso3166a2 = %s THEN p2.name_fr
                    ELSE p1.name_fr
                END as name_fr,
                CASE 
                    WHEN pb.country_iso3166a2 = %s THEN p2.name_local
                    ELSE p1.name_local
                END as name_local
            FROM Pays_Borders pb
            LEFT JOIN Pays p1 ON pb.country_iso3166a2 = p1.iso3166a2
            LEFT JOIN Pays p2 ON pb.border_iso3166a2 = p2.iso3166a2
            WHERE pb.country_iso3166a2 = %s OR pb.border_iso3166a2 = %s
        """
        borders = MySQLConnection.execute_query(
            borders_query, (iso2, iso2, iso2, iso2, iso2, iso2)
        )
        pays["borders"] = borders if borders else []

        # Récupérer l'électricité (types, voltage, frequency)
        elec_query = """
            SELECT plug_type, voltage, frequency 
            FROM Pays_Electricite 
            WHERE country_iso3166a2 = %s
        """
        elec = MySQLConnection.execute_query(elec_query, (iso2,))

        if elec:
            pays["electricity_types"] = [e["plug_type"] for e in elec]
            pays["voltage"] = elec[0].get("voltage")
            pays["frequency"] = elec[0].get("frequency")
        else:
            pays["electricity_types"] = []
            pays["voltage"] = None
            pays["frequency"] = None

        return pays

    @staticmethod
    def get_by_name(name: str) -> List[Dict[str, Any]]:
        """
        Recherche des pays par nom (name_en, name_fr, name_local)
        Recherche insensible à la casse et aux accents
        """
        normalized = CountryRepository._normalize_string(name)
        search_pattern = f"%{normalized}%"

        # Recherche avec LOWER et pattern matching
        query = """
            SELECT DISTINCT
                p.iso3166a2, p.iso3166a3, p.name_en, p.name_fr, p.name_local,
                p.lat, p.lng
            FROM Pays p
            WHERE LOWER(p.name_en) LIKE %s
               OR LOWER(p.name_fr) LIKE %s
               OR LOWER(p.name_local) LIKE %s
            ORDER BY p.name_en
        """
        results = MySQLConnection.execute_query(
            query, (search_pattern, search_pattern, search_pattern)
        )

        if not results:
            return []

        # Pour chaque pays trouvé, récupérer ses relations complètes
        countries = []
        for row in results:
            country = CountryRepository.get_by_alpha2(row["iso3166a2"])
            if country:
                countries.append(country)

        return countries

    @staticmethod
    def get_all(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Liste tous les pays avec pagination (sans les relations pour performance)"""
        query = """
            SELECT iso3166a2, iso3166a3, name_en, name_fr, name_local, lat, lng
            FROM Pays
            ORDER BY name_en
            LIMIT %s OFFSET %s
        """
        return MySQLConnection.execute_query(query, (limit, skip)) or []

    # --- PAYS - ECRITURE ----------------------------------------------------
    @staticmethod
    def upsert_pays(
        iso2: str,
        iso3: str,
        name_en: str,
        name_fr: str,
        name_local: str,
        lat: str,
        lng: str,
    ) -> int:
        """Insert ou update un pays"""
        lat_val = float(lat) if lat not in ("", None) else None
        lng_val = float(lng) if lng not in ("", None) else None
        query = """
            REPLACE INTO Pays (iso3166a2, iso3166a3, name_en, name_fr, name_local, lat, lng)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return MySQLConnection.execute_update(
            query, (iso2, iso3, name_en, name_fr, name_local, lat_val, lng_val)
        )

    @staticmethod
    def delete_pays(iso2: str) -> bool:
        """Supprime un pays (cascade sur les tables de liaison)"""
        iso2 = iso2.lower().strip()
        query = "DELETE FROM Pays WHERE iso3166a2 = %s"
        affected = MySQLConnection.execute_update(query, (iso2,))
        return affected > 0

    @staticmethod
    def update_pays(iso2: str, data: Dict[str, Any]) -> bool:
        """Met à jour les champs d'un pays"""
        iso2 = iso2.lower().strip()

        # Construire dynamiquement la requête UPDATE
        fields = []
        values = []

        for key, value in data.items():
            if key in ["iso3166a3", "name_en", "name_fr", "name_local", "lat", "lng"]:
                fields.append(f"{key} = %s")
                values.append(value)

        if not fields:
            return False

        values.append(iso2)
        query = f"UPDATE Pays SET {', '.join(fields)} WHERE iso3166a2 = %s"
        affected = MySQLConnection.execute_update(query, tuple(values))
        return affected > 0

    # --- RELATIONS - SUPPRESSION AVANT REINSERTION -------------------------
    @staticmethod
    def delete_relations(iso2: str):
        """Supprime toutes les relations d'un pays avant réinsertion"""
        iso2 = iso2.lower().strip()

        MySQLConnection.execute_update(
            "DELETE FROM Pays_Langues WHERE country_iso3166a2 = %s", (iso2,)
        )
        MySQLConnection.execute_update(
            "DELETE FROM Pays_Monnaies WHERE country_iso3166a2 = %s", (iso2,)
        )
        MySQLConnection.execute_update(
            "DELETE FROM Pays_Borders WHERE country_iso3166a2 = %s OR border_iso3166a2 = %s",
            (iso2, iso2),
        )
        MySQLConnection.execute_update(
            "DELETE FROM Pays_Electricite WHERE country_iso3166a2 = %s", (iso2,)
        )

    # --- LANGUES ------------------------------------------------------------
    @staticmethod
    def insert_langues(country_iso2: str, iso639_list: Iterable[str]) -> int:
        rows: List[Tuple[str, str]] = []
        for code in iso639_list:
            code = code.strip()
            if not code:
                continue
            rows.append((country_iso2, code))
        if not rows:
            return 0
        query = """
            INSERT IGNORE INTO Pays_Langues (country_iso3166a2, iso639_2)
            VALUES (%s, %s)
        """
        return MySQLConnection.execute_update(query, rows)

    # --- MONNAIES -----------------------------------------------------------
    @staticmethod
    def insert_monnaies(country_iso2: str, iso4217_list: Iterable[str]) -> int:
        rows: List[Tuple[str, str]] = []
        for code in iso4217_list:
            code = code.strip().upper()
            if not code:
                continue
            rows.append((country_iso2, code))
        if not rows:
            return 0
        query = """
            INSERT IGNORE INTO Pays_Monnaies (country_iso3166a2, currency_iso4217)
            VALUES (%s, %s)
        """
        return MySQLConnection.execute_update(query, rows)

    # --- FRONTIÈRES ---------------------------------------------------------
    @staticmethod
    def insert_borders(country_iso2: str, borders_iso2_list: Iterable[str]) -> int:
        """
        Règles:
          - Interdire doubles fr/fr
          - Insérer uniquement dans l'ordre alphabétique pour éviter la symétrie (a,b) avec a < b
        """
        rows: List[Tuple[str, str]] = []
        seen = set()
        c = country_iso2.lower()

        for b in borders_iso2_list:
            b = (b or "").strip().lower()
            if not b:
                continue
            if b == c:
                continue
            a1, b1 = sorted([c, b])
            key = (a1, b1)
            if key in seen:
                continue
            seen.add(key)
            rows.append((a1, b1))

        if not rows:
            return 0

        query = """
            INSERT IGNORE INTO Pays_Borders (country_iso3166a2, border_iso3166a2)
            VALUES (%s, %s)
        """
        return MySQLConnection.execute_update(query, rows)

    # --- ÉLECTRICITÉ --------------------------------------------------------
    @staticmethod
    def insert_electricite(
        country_iso2: str, plug_types: Iterable[str], voltage: str, frequency: str
    ) -> int:
        """
        INSÈRE dans Pays_Electricite uniquement si le type de prise existe déjà dans Electricite (FK RESTRICT).
        'plug_types' vient d'une chaîne 'C,F' → split et trim.
        """
        rows: List[Tuple[str, str, str, str]] = []
        v = (voltage or "").strip() or None
        f = (frequency or "").strip() or None
        for plug in plug_types:
            t = (plug or "").strip().upper()
            if not t:
                continue
            rows.append((country_iso2, t, v, f))
        if not rows:
            return 0
        query = """
            INSERT IGNORE INTO Pays_Electricite (country_iso3166a2, plug_type, voltage, frequency)
            VALUES (%s, %s, %s, %s)
        """
        return MySQLConnection.execute_update(query, rows)
