from typing import Iterable, List, Tuple, Optional, Dict, Any
from connexion.mysql_connect import MySQLConnection
import unicodedata
import json


class CountryRepository:
    """Repository pour Pays et tables de liaison"""

    # --- UTILITAIRES --------------------------------------------------------
    @staticmethod
    def _normalize_string(text: str) -> str:
        """Normalise une chaîne : minuscules, sans accents"""
        text = text.lower().strip()
        text = "".join(
            c
            for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        return text

    # --- PAYS - LECTURE -----------------------------------------------------
    @staticmethod
    def get_by_alpha2(iso2: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un pays par son code ISO alpha-2 avec toutes ses relations enrichies
        Utilise JSON_ARRAYAGG pour agréger les objets complets
        """
        iso2 = iso2.lower().strip()

        # Requête principale avec les données de base
        query_base = """
            SELECT 
                p.iso3166a2, 
                p.iso3166a3, 
                p.name_en, 
                p.name_fr, 
                p.name_local, 
                p.lat, 
                p.lng
            FROM Pays p
            WHERE p.iso3166a2 = %s
        """

        result = MySQLConnection.execute_query(query_base, (iso2,))

        if not result:
            return None

        pays = result[0]

        # Récupérer les langues avec leurs informations complètes
        langues_query = """
            SELECT 
                l.iso639_2,
                l.name_en,
                l.name_fr,
                l.name_local,
                f.branche_en as famille_en,
                f.branche_fr as famille_fr
            FROM Pays_Langues pl
            INNER JOIN Langues l ON pl.iso639_2 = l.iso639_2
            LEFT JOIN Familles f ON l.famille_id = f.id
            WHERE pl.country_iso3166a2 = %s
            ORDER BY l.name_en
        """
        langues = MySQLConnection.execute_query(langues_query, (iso2,))
        pays["langues"] = langues if langues else []

        # Récupérer les monnaies avec leurs informations complètes
        currencies_query = """
            SELECT 
                m.iso4217,
                m.name,
                m.symbol
            FROM Pays_Monnaies pm
            INNER JOIN Monnaies m ON pm.currency_iso4217 = m.iso4217
            WHERE pm.country_iso3166a2 = %s
            ORDER BY m.iso4217
        """
        currencies = MySQLConnection.execute_query(currencies_query, (iso2,))
        pays["currencies"] = currencies if currencies else []

        # Récupérer les pays frontaliers (sans récursivité)
        # La table Pays_Borders stocke les relations dans un seul sens (ordre alphabétique)
        # pour éviter les doublons symétriques (ex: fr→de existe, mais pas de→fr)
        #
        # Logique de la requête :
        # - On joint la table Pays deux fois (p1 et p2) pour récupérer les infos des deux côtés
        # - Le pays recherché (%s) peut être soit dans 'country_iso3166a2', soit dans 'border_iso3166a2'
        # - Le CASE détermine quel pays voisin retourner (recherche dans les deux colonnes de la relation) :
        #   * Si pays recherché = country → retourner border (p2)
        #   * Si pays recherché = border  → retourner country (p1)
        # - Résultat : liste des pays frontaliers avec leurs noms (iso, en, fr, local)
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
            ORDER BY name_en
        """
        borders = MySQLConnection.execute_query(
            borders_query, (iso2, iso2, iso2, iso2, iso2, iso2)
        )
        pays["borders"] = borders if borders else []

        # Récupérer l'électricité avec les informations complètes
        elec_query = """
            SELECT 
                e.plug_type,
                e.plug_png,
                e.sock_png,
                pe.voltage,
                pe.frequency
            FROM Pays_Electricite pe
            INNER JOIN Electricite e ON pe.plug_type = e.plug_type
            WHERE pe.country_iso3166a2 = %s
            ORDER BY e.plug_type
        """
        electricity = MySQLConnection.execute_query(elec_query, (iso2,))
        pays["electricity"] = electricity if electricity else []

        return pays

    @staticmethod
    def get_by_alpha2_optimized(iso2: str) -> Optional[Dict[str, Any]]:
        """
        VERSION OPTIMISÉE avec JSON_ARRAYAGG (MySQL 5.7.22+)
        Une seule requête avec tous les objets agrégés en JSON
        """
        iso2 = iso2.lower().strip()

        # Note: JSON_ARRAYAGG nécessite MySQL 5.7.22+ ou MariaDB 10.5+
        # Si version inférieure, utiliser get_by_alpha2() classique
        query = """
            SELECT 
                p.iso3166a2, 
                p.iso3166a3, 
                p.name_en, 
                p.name_fr, 
                p.name_local, 
                p.lat, 
                p.lng,
                (
                    SELECT JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'iso639_2', l.iso639_2,
                            'name_en', l.name_en,
                            'name_fr', l.name_fr,
                            'name_local', l.name_local,
                            'famille_en', f.branche_en,
                            'famille_fr', f.branche_fr
                        )
                    )
                    FROM Pays_Langues pl
                    INNER JOIN Langues l ON pl.iso639_2 = l.iso639_2
                    LEFT JOIN Familles f ON l.famille_id = f.id
                    WHERE pl.country_iso3166a2 = p.iso3166a2
                ) as langues_json,
                (
                    SELECT JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'iso4217', m.iso4217,
                            'name', m.name,
                            'symbol', m.symbol
                        )
                    )
                    FROM Pays_Monnaies pm
                    INNER JOIN Monnaies m ON pm.currency_iso4217 = m.iso4217
                    WHERE pm.country_iso3166a2 = p.iso3166a2
                ) as currencies_json,
                (
                    SELECT JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'plug_type', e.plug_type,
                            'plug_png', e.plug_png,
                            'sock_png', e.sock_png,
                            'voltage', pe.voltage,
                            'frequency', pe.frequency
                        )
                    )
                    FROM Pays_Electricite pe
                    INNER JOIN Electricite e ON pe.plug_type = e.plug_type
                    WHERE pe.country_iso3166a2 = p.iso3166a2
                ) as electricity_json
            FROM Pays p
            WHERE p.iso3166a2 = %s
        """

        result = MySQLConnection.execute_query(query, (iso2,))

        if not result:
            return None

        pays = result[0]

        # Parser les JSON (si NULL, mettre liste vide)
        pays["langues"] = (
            json.loads(pays["langues_json"]) if pays["langues_json"] else []
        )
        pays["currencies"] = (
            json.loads(pays["currencies_json"]) if pays["currencies_json"] else []
        )
        pays["electricity"] = (
            json.loads(pays["electricity_json"]) if pays["electricity_json"] else []
        )

        # Supprimer les champs JSON temporaires
        del pays["langues_json"]
        del pays["currencies_json"]
        del pays["electricity_json"]

        # Récupérer les frontières (requête séparée car logique complexe)
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
            ORDER BY name_en
        """
        borders = MySQLConnection.execute_query(
            borders_query, (iso2, iso2, iso2, iso2, iso2, iso2)
        )
        pays["borders"] = borders if borders else []

        return pays

    @staticmethod
    def get_by_name(name: str) -> List[Dict[str, Any]]:
        """
        Recherche des pays par nom (name_en, name_fr, name_local)
        Recherche insensible à la casse et aux accents
        """
        normalized = CountryRepository._normalize_string(name)
        search_pattern = f"%{normalized}%"

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
