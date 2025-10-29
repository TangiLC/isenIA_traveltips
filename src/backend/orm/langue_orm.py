from typing import List, Optional, Dict, Any
from connexion.mysql_connect import MySQLConnection


class LangueRepository:
    """Repository pour la gestion des langues en base de données"""

    @staticmethod
    def find_by_iso639_2(iso639_2: str) -> Optional[Dict[str, Any]]:
        """Recherche une langue par son code ISO 639-2

        Args:
            iso639_2: Code ISO 639-2 (3 caractères)

        Returns:
            Dictionnaire avec les données de la langue et sa famille, ou None
        """
        query = """
            SELECT 
                l.iso639_2,
                l.name_en,
                l.name_fr,
                l.name_local,
                l.is_in_mongo,
                f.branche_en,
                f.branche_fr
            FROM Langues l
            LEFT JOIN Familles f ON l.famille_id = f.id
            WHERE l.iso639_2 = %s
        """
        result = MySQLConnection.execute_query(query, (iso639_2,))
        return result[0] if result else None

    @staticmethod
    def find_by_name(search_term: str) -> List[Dict[str, Any]]:
        """Recherche des langues par nom (name_en, name_fr ou name_local)

        Args:
            search_term: Terme de recherche (insensible à la casse)

        Returns:
            Liste de langues correspondantes
        """
        query = """
            SELECT 
                l.iso639_2,
                l.name_en,
                l.name_fr,
                l.name_local,
                l.is_in_mongo,
                f.branche_en,
                f.branche_fr
            FROM Langues l
            LEFT JOIN Familles f ON l.famille_id = f.id
            WHERE LOWER(l.name_en) LIKE LOWER(%s)
               OR LOWER(l.name_fr) LIKE LOWER(%s)
               OR LOWER(l.name_local) LIKE LOWER(%s)
        """
        search_pattern = f"%{search_term}%"
        return MySQLConnection.execute_query(
            query, (search_pattern, search_pattern, search_pattern)
        )

    @staticmethod
    def find_by_famille(branche: str) -> List[Dict[str, Any]]:
        """Recherche des langues par famille linguistique (pattern)

        Args:
            branche_en: Nom de la branche en anglais

        Returns:
            Liste des langues de cette famille
        """
        query = """
            SELECT 
                l.iso639_2,
                l.name_en,
                l.name_fr,
                l.name_local,
                l.is_in_mongo,
                f.branche_en,
                f.branche_fr
            FROM Langues l
            INNER JOIN Familles f ON l.famille_id = f.id
            WHERE LOWER(f.branche_en) LIKE LOWER (%s)
               OR LOWER(f.branche_fr) LIKE LOWER(%s)
        """
        search_pattern = f"%{branche}%"
        return MySQLConnection.execute_query(query, (search_pattern, search_pattern))

    @staticmethod
    def get_famille_id_by_branche(branche_en: str) -> Optional[int]:
        """Récupère l'ID d'une famille par son nom de branche

        Args:
            branche_en: Nom de la branche en anglais

        Returns:
            ID de la famille ou None
        """
        query = """
                SELECT id FROM Familles
                WHERE LOWER(branche_en) LIKE LOWER (%s)
                OR LOWER(branche_fr) LIKE LOWER(%s)
                """
        result = MySQLConnection.execute_query(query, (branche_en, branche_en))
        return result[0]["id"] if result else None

    @staticmethod
    def create_or_replace(
        iso639_2: str,
        name_en: str,
        name_fr: str,
        name_local: str,
        branche_en: Optional[str] = None,
        is_in_mongo: bool = False,
    ) -> int:
        """Crée ou remplace une langue (REPLACE INTO)

        Args:
            iso639_2: Code ISO 639-2
            name_en: Nom en anglais
            name_fr: Nom en français
            name_local: Nom local
            branche_en: Nom de la famille (optionnel)
            is_in_mongo: Présence dans MongoDB (défaut: False)

        Returns:
            Nombre de lignes affectées
        """
        famille_id = None
        if branche_en:
            famille_id = LangueRepository.get_famille_id_by_branche(branche_en)

        query = """
            REPLACE INTO Langues 
            (iso639_2, name_en, name_fr, name_local, famille_id, is_in_mongo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return MySQLConnection.execute_update(
            query, (iso639_2, name_en, name_fr, name_local, famille_id, is_in_mongo)
        )

    @staticmethod
    def create_or_replace_batch(langues: List[Dict[str, Any]]) -> int:
        """Insertion/remplacement en masse de langues

        Args:
            langues: Liste de dictionnaires contenant les données des langues

        Returns:
            Nombre total de lignes insérées/remplacées
        """
        total_inserted = 0

        for langue in langues:
            famille_id = None
            if langue.get("branche_en"):
                famille_id = LangueRepository.get_famille_id_by_branche(
                    langue["branche_en"]
                )

            query = """
                REPLACE INTO Langues 
                (iso639_2, name_en, name_fr, name_local, famille_id, is_in_mongo)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            rowcount = MySQLConnection.execute_update(
                query,
                (
                    langue["iso639_2"],
                    langue["name_en"],
                    langue["name_fr"],
                    langue["name_local"],
                    famille_id,
                    langue.get("is_in_mongo", False),
                ),
            )
            total_inserted += rowcount

        return total_inserted

    @staticmethod
    def update_partial(iso639_2: str, updates: Dict[str, Any]) -> int:
        """Mise à jour partielle d'une langue

        Args:
            iso639_2: Code ISO 639-2 de la langue à modifier
            updates: Dictionnaire des champs à mettre à jour (peut inclure 'famille_id', 'is_in_mongo')

        Returns:
            Nombre de lignes modifiées
        """
        # Champs autorisés pour la mise à jour
        allowed_fields = {
            "name_en",
            "name_fr",
            "name_local",
            "famille_id",
            "is_in_mongo",
        }
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not filtered_updates:
            return 0

        # Construction de la clause SET
        set_clause = ", ".join(f"{key} = %s" for key in filtered_updates)
        values = list(filtered_updates.values()) + [iso639_2]

        query = f"UPDATE Langues SET {set_clause} WHERE iso639_2 = %s"
        return MySQLConnection.execute_update(query, tuple(values))

    @staticmethod
    def delete(iso639_2: str) -> int:
        """Supprime une langue par son code ISO

        Args:
            iso639_2: Code ISO 639-2

        Returns:
            Nombre de lignes supprimées
        """
        query = "DELETE FROM Langues WHERE iso639_2 = %s"
        return MySQLConnection.execute_update(query, (iso639_2,))

    @staticmethod
    def insert_ignore(
        iso639_2: str,
        name_en: str,
        name_fr: str,
        name_local: str,
        branche_en: Optional[str] = None,
        is_in_mongo: bool = False,
    ) -> int:
        """Insère une langue uniquement si elle n'existe pas (INSERT IGNORE)

        Args:
            iso639_2: Code ISO 639-2
            name_en: Nom en anglais
            name_fr: Nom en français
            name_local: Nom local
            branche_en: Nom de la famille (optionnel)
            is_in_mongo: Présence dans MongoDB (défaut: False)

        Returns:
            Nombre de lignes insérées
        """
        famille_id = None
        if branche_en:
            famille_id = LangueRepository.get_famille_id_by_branche(branche_en)

        query = """
            INSERT INTO Langues 
            (iso639_2, name_en, name_fr, name_local, famille_id, is_in_mongo)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
               iso639_2 = VALUES(iso639_2),
               name_en = VALUES(name_en),
               name_fr = VALUES(name_fr),
               name_local = VALUES(name_local),
               famille_id = VALUES(famille_id),
               is_in_mongo = VALUES(is_in_mongo)
            
        """
        return MySQLConnection.execute_update(
            query, (iso639_2, name_en, name_fr, name_local, famille_id, is_in_mongo)
        )
