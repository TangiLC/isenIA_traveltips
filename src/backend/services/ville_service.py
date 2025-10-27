from typing import List, Dict, Any, Optional
from repositories.ville_repository import VilleRepository
from models.ville import Ville


class VilleService:
    """Service pour la gestion des villes"""

    @staticmethod
    def get_by_geoname_id(geoname_id: int) -> Ville:
        """Récupère une ville par son geoname_id

        Args:
            geoname_id: ID GeoNames

        Returns:
            Ville trouvée

        Raises:
            ValueError: Si ville non trouvée
        """
        ville = VilleRepository.get_by_geoname_id(geoname_id)
        if ville is None:
            raise ValueError("Ville non trouvée")
        return ville

    @staticmethod
    def get_by_name(name_en: str) -> List[Ville]:
        """Récupère les villes par nom

        Args:
            name_en: Nom de la ville en anglais

        Returns:
            Liste des villes

        Raises:
            ValueError: Si aucune ville trouvée
        """
        villes = VilleRepository.get_by_name(name_en)
        if not villes:
            raise ValueError("Aucune ville trouvée avec ce nom")
        return villes

    @staticmethod
    def get_by_country(country_3166a2: str) -> List[Ville]:
        """Récupère les villes par pays

        Args:
            country_3166a2: Code ISO 3166 alpha-2 du pays

        Returns:
            Liste des villes

        Raises:
            ValueError: Si code pays invalide ou aucune ville trouvée
        """
        if len(country_3166a2) != 2:
            raise ValueError("Le code pays doit contenir exactement 2 caractères")

        villes = VilleRepository.get_by_country(country_3166a2)
        if not villes:
            raise ValueError("Aucune ville trouvée pour ce pays")
        return villes

    @staticmethod
    def get_all(skip: int = 0, limit: int = 100) -> List[Ville]:
        """Liste toutes les villes avec pagination

        Args:
            skip: Nombre d'éléments à ignorer
            limit: Nombre maximum d'éléments

        Returns:
            Liste des villes
        """
        return VilleRepository.get_all(skip, limit)

    @staticmethod
    def create(ville_data: Dict[str, Any]) -> Ville:
        """Crée une nouvelle ville

        Args:
            ville_data: Données de la ville

        Returns:
            Ville créée

        Raises:
            ValueError: Si une ville avec ce geoname_id existe déjà
        """
        existing = VilleRepository.get_by_geoname_id(ville_data["geoname_id"])
        if existing:
            raise ValueError("Une ville avec ce geoname_id existe déjà")

        return VilleRepository.create(ville_data)

    @staticmethod
    def update(geoname_id: int, update_data: Dict[str, Any]) -> Ville:
        """Met à jour une ville

        Args:
            geoname_id: ID GeoNames de la ville
            update_data: Données à mettre à jour

        Returns:
            Ville mise à jour

        Raises:
            ValueError: Si ville non trouvée
        """
        updated = VilleRepository.update(geoname_id, update_data)
        if updated is None:
            raise ValueError("Ville non trouvée")
        return updated

    @staticmethod
    def delete(geoname_id: int) -> bool:
        """Supprime une ville

        Args:
            geoname_id: ID GeoNames de la ville

        Returns:
            True si supprimée, False sinon
        """
        return VilleRepository.delete(geoname_id)
