from typing import List, Dict, Any
from connexion.mysql_connect import MySQLConnection
from repositories.electricity_repository import ElectriciteRepository


class ElectricityService:
    """Service pour la gestion des types de prises électriques"""

    @staticmethod
    def find_all() -> List[Dict[str, Any]]:
        """Liste tous les types de prises

        Returns:
            Liste des types de prises
        """
        try:
            MySQLConnection.connect()
            return ElectriciteRepository.find_all()
        finally:
            MySQLConnection.close()

    @staticmethod
    def find_by_plug_type(plug_type: str) -> Dict[str, Any]:
        """Recherche un type de prise par identifiant

        Args:
            plug_type: Identifiant du type de prise (A-N)

        Returns:
            Données du type de prise

        Raises:
            ValueError: Si type de prise non trouvé
        """
        try:
            MySQLConnection.connect()
            result = ElectriciteRepository.find_by_plug_type(plug_type.upper())

            if not result:
                raise ValueError(f"Type de prise '{plug_type}' introuvable")

            return result
        finally:
            MySQLConnection.close()

    @staticmethod
    def create_or_replace(plug_data: Dict[str, Any]) -> int:
        """Crée ou remplace un type de prise

        Args:
            plug_data: Données du type de prise

        Returns:
            Nombre de lignes affectées
        """
        try:
            MySQLConnection.connect()

            rows = ElectriciteRepository.create_or_replace(
                plug_type=plug_data["plug_type"].upper(),
                plug_png=plug_data["plug_png"],
                sock_png=plug_data["sock_png"],
            )

            MySQLConnection.commit()
            return rows
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()

    @staticmethod
    def update_partial(plug_type: str, updates: Dict[str, Any]) -> int:
        """Mise à jour partielle d'un type de prise

        Args:
            plug_type: Identifiant du type de prise
            updates: Dictionnaire des champs à mettre à jour

        Returns:
            Nombre de lignes affectées

        Raises:
            ValueError: Si type de prise non trouvé ou aucun champ à mettre à jour
        """
        try:
            MySQLConnection.connect()

            # Vérifier existence
            existing = ElectriciteRepository.find_by_plug_type(plug_type.upper())
            if not existing:
                raise ValueError(f"Type de prise '{plug_type}' introuvable")

            # Filtrer les champs non-None
            updates_filtered = {k: v for k, v in updates.items() if v is not None}

            if not updates_filtered:
                raise ValueError("Aucun champ à mettre à jour")

            rows = ElectriciteRepository.update_partial(
                plug_type.upper(), updates_filtered
            )
            MySQLConnection.commit()
            return rows
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()

    @staticmethod
    def delete(plug_type: str) -> int:
        """Supprime un type de prise

        Args:
            plug_type: Identifiant du type de prise

        Returns:
            Nombre de lignes supprimées

        Raises:
            ValueError: Si type de prise non trouvé
        """
        try:
            MySQLConnection.connect()

            # Vérifier existence
            existing = ElectriciteRepository.find_by_plug_type(plug_type.upper())
            if not existing:
                raise ValueError(f"Type de prise '{plug_type}' introuvable")

            rows = ElectriciteRepository.delete(plug_type.upper())
            MySQLConnection.commit()
            return rows
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()

    @staticmethod
    def find_countries_by_plug_type(plug_type: str) -> List[Dict[str, Any]]:
        """Liste les pays utilisant un type de prise

        Args:
            plug_type: Identifiant du type de prise

        Returns:
            Liste des pays

        Raises:
            ValueError: Si aucun pays trouvé
        """
        try:
            MySQLConnection.connect()
            results = ElectriciteRepository.find_countries_by_plug_type(
                plug_type.upper()
            )

            if not results:
                raise ValueError(
                    f"Aucun pays trouvé pour le type de prise '{plug_type}'"
                )

            return results
        finally:
            MySQLConnection.close()
