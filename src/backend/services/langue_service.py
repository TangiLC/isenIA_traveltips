from typing import List, Dict, Any
from connexion.mysql_connect import MySQLConnection
from orm.langue_orm import LangueOrm


class LangueService:
    """Service pour la gestion des langues"""

    @staticmethod
    def find_by_iso639_2(code: str) -> Dict[str, Any]:
        """Recherche une langue par code ISO 639-2

        Args:
            code: Code ISO 639-2

        Returns:
            Données de la langue

        Raises:
            ValueError: Si langue non trouvée
        """
        try:
            MySQLConnection.connect()
            result = LangueOrm.find_by_iso639_2(code)

            if not result:
                raise ValueError(f"Langue avec le code '{code}' introuvable")

            return result
        finally:
            MySQLConnection.close()

    @staticmethod
    def find_by_name(name: str) -> List[Dict[str, Any]]:
        """Recherche des langues par nom

        Args:
            name: Terme de recherche

        Returns:
            Liste des langues
        """
        try:
            MySQLConnection.connect()
            return LangueOrm.find_by_name(name)
        finally:
            MySQLConnection.close()

    @staticmethod
    def find_by_famille(famille: str) -> List[Dict[str, Any]]:
        """Recherche des langues par famille

        Args:
            famille: Nom de la famille

        Returns:
            Liste des langues
        """
        try:
            MySQLConnection.connect()
            return LangueOrm.find_by_famille(famille)
        finally:
            MySQLConnection.close()

    @staticmethod
    def create_or_replace(langue_data: Dict[str, Any]) -> int:
        """Crée ou remplace une langue

        Args:
            langue_data: Données de la langue

        Returns:
            Nombre de lignes affectées
        """
        try:
            MySQLConnection.connect()

            rows_affected = LangueOrm.create_or_replace(
                iso639_2=langue_data["iso639_2"],
                name_en=langue_data["name_en"],
                name_fr=langue_data["name_fr"],
                name_local=langue_data["name_local"],
                branche_en=langue_data.get("branche_en"),
                is_in_mongo=langue_data.get("is_in_mongo", False),
            )

            MySQLConnection.commit()
            return rows_affected
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()

    @staticmethod
    def update_partial(iso639_2: str, updates: Dict[str, Any]) -> int:
        """Mise à jour partielle d'une langue

        Args:
            iso639_2: Code ISO 639-2
            updates: Dictionnaire des champs à mettre à jour

        Returns:
            Nombre de lignes affectées

        Raises:
            ValueError: Si langue non trouvée ou aucun champ à mettre à jour
        """
        try:
            MySQLConnection.connect()

            # Vérifier existence
            existing = LangueOrm.find_by_iso639_2(iso639_2)
            if not existing:
                raise ValueError(f"Langue avec le code '{iso639_2}' introuvable")

            # Filtrer les champs non-None
            updates_filtered = {k: v for k, v in updates.items() if v is not None}

            if not updates_filtered:
                raise ValueError("Aucun champ à mettre à jour")

            rows_affected = LangueOrm.update_partial(iso639_2, updates_filtered)
            MySQLConnection.commit()
            return rows_affected
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()

    @staticmethod
    def delete(iso639_2: str) -> int:
        """Supprime une langue

        Args:
            iso639_2: Code ISO 639-2

        Returns:
            Nombre de lignes supprimées

        Raises:
            ValueError: Si langue non trouvée
        """
        try:
            MySQLConnection.connect()

            # Vérifier existence
            existing = LangueOrm.find_by_iso639_2(iso639_2)
            if not existing:
                raise ValueError(f"Langue avec le code '{iso639_2}' introuvable")

            rows_affected = LangueOrm.delete(iso639_2)
            MySQLConnection.commit()
            return rows_affected
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()
