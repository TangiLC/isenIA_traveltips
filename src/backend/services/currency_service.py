from typing import List, Dict, Any
from connexion.mysql_connect import MySQLConnection
from repositories.currency_repository import CurrencyRepository


class CurrencyService:
    """Service pour la gestion des devises"""

    @staticmethod
    def find_by_iso4217(code: str) -> Dict[str, Any]:
        """Recherche une devise par code ISO 4217

        Args:
            code: Code ISO 4217

        Returns:
            Données de la devise

        Raises:
            ValueError: Si devise non trouvée
        """
        try:
            MySQLConnection.connect()
            result = CurrencyRepository.find_by_iso4217(code)

            if not result:
                raise ValueError(f"Devise avec le code '{code}' introuvable")

            return result
        finally:
            MySQLConnection.close()

    @staticmethod
    def find_by_name_or_symbol(search_term: str) -> List[Dict[str, Any]]:
        """Recherche des devises par nom, symbole ou code

        Args:
            search_term: Terme de recherche

        Returns:
            Liste des devises
        """
        try:
            MySQLConnection.connect()
            return CurrencyRepository.find_by_name_or_symbol(search_term)
        finally:
            MySQLConnection.close()

    @staticmethod
    def create_or_replace(currency_data: Dict[str, Any]) -> int:
        """Crée ou remplace une devise

        Args:
            currency_data: Données de la devise

        Returns:
            Nombre de lignes affectées
        """
        try:
            MySQLConnection.connect()

            rows = CurrencyRepository.create_or_replace(
                iso4217=currency_data["iso4217"],
                name=currency_data["name"],
                symbol=currency_data["symbol"],
            )

            MySQLConnection.commit()
            return rows
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()

    @staticmethod
    def update_partial(iso4217: str, updates: Dict[str, Any]) -> int:
        """Mise à jour partielle d'une devise

        Args:
            iso4217: Code ISO 4217
            updates: Dictionnaire des champs à mettre à jour

        Returns:
            Nombre de lignes affectées

        Raises:
            ValueError: Si devise non trouvée ou aucun champ à mettre à jour
        """
        try:
            MySQLConnection.connect()

            # Vérifier existence
            existing = CurrencyRepository.find_by_iso4217(iso4217)
            if not existing:
                raise ValueError(f"Devise avec le code '{iso4217}' introuvable")

            # Filtrer les champs non-None
            updates_filtered = {k: v for k, v in updates.items() if v is not None}

            if not updates_filtered:
                raise ValueError("Aucun champ à mettre à jour")

            rows = CurrencyRepository.update_partial(iso4217, updates_filtered)
            MySQLConnection.commit()
            return rows
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()

    @staticmethod
    def delete(iso4217: str) -> int:
        """Supprime une devise

        Args:
            iso4217: Code ISO 4217

        Returns:
            Nombre de lignes supprimées

        Raises:
            ValueError: Si devise non trouvée
        """
        try:
            MySQLConnection.connect()

            # Vérifier existence
            existing = CurrencyRepository.find_by_iso4217(iso4217)
            if not existing:
                raise ValueError(f"Devise avec le code '{iso4217}' introuvable")

            rows = CurrencyRepository.delete(iso4217)
            MySQLConnection.commit()
            return rows
        except Exception as e:
            MySQLConnection.rollback()
            raise
        finally:
            MySQLConnection.close()
