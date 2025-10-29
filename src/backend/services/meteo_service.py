from datetime import date
from typing import List, Optional
from orm.week_meteo_orm import WeekMeteoRepository
from models.week_meteo import WeekMeteo


class MeteoService:
    """Service pour la gestion de la météo hebdomadaire"""

    @staticmethod
    def get_weeks_for_city(
        geoname_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[WeekMeteo]:
        """Récupère les semaines météo pour une ville

        Args:
            geoname_id: ID GeoNames de la ville
            start_date: Date de début (incluse)
            end_date: Date de fin (incluse)

        Returns:
            Liste des semaines météo

        Raises:
            ValueError: Si aucune donnée trouvée
        """
        data = WeekMeteoRepository.get_range(geoname_id, start_date, end_date)
        if not data:
            raise ValueError("Aucune donnée hebdomadaire")
        return data

    @staticmethod
    def get_all(skip: int = 0, limit: int = 100) -> List[WeekMeteo]:
        """Liste toutes les semaines météo avec pagination

        Args:
            skip: Nombre d'éléments à ignorer
            limit: Nombre maximum d'éléments

        Returns:
            Liste des semaines météo
        """
        return WeekMeteoRepository.get_all(skip, limit)

    @staticmethod
    def create_or_update(week_data: WeekMeteo) -> WeekMeteo:
        """Crée ou met à jour une semaine météo

        Args:
            week_data: Données de la semaine

        Returns:
            Semaine créée/mise à jour
        """
        return WeekMeteoRepository.upsert(week_data)

    @staticmethod
    def bulk_create_or_update(items: List[WeekMeteo]) -> int:
        """Création/mise à jour en masse

        Args:
            items: Liste des semaines météo

        Returns:
            Nombre de lignes upsertées
        """
        return WeekMeteoRepository.bulk_upsert(items)

    @staticmethod
    def update_partial(
        geoname_id: int, week_start_date: date, changes: dict
    ) -> WeekMeteo:
        """Mise à jour partielle d'une semaine

        Args:
            geoname_id: ID GeoNames de la ville
            week_start_date: Date de début de semaine
            changes: Dictionnaire des modifications

        Returns:
            Semaine mise à jour

        Raises:
            ValueError: Si la semaine n'existe pas
        """
        existing = WeekMeteoRepository.get_by_pk(geoname_id, week_start_date)
        if existing is None:
            raise ValueError("Semaine non trouvée")

        data = existing.model_dump()
        for k, v in changes.items():
            data[k] = v

        return WeekMeteoRepository.upsert(WeekMeteo(**data))

    @staticmethod
    def delete(geoname_id: int, week_start_date: date) -> bool:
        """Supprime une semaine météo

        Args:
            geoname_id: ID GeoNames de la ville
            week_start_date: Date de début de semaine

        Returns:
            True si supprimée, False si non trouvée
        """
        return WeekMeteoRepository.delete(geoname_id, week_start_date)
