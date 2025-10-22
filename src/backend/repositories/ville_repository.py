from typing import List, Optional
from models.ville import Ville
from connexion.mysql_connect import MySQLConnection


class VilleRepository:
    """Repository pour la gestion des villes"""

    @staticmethod
    def get_by_geoname_id(geoname_id: int) -> Optional[Ville]:
        """Récupère une ville par son geoname_id"""
        MySQLConnection.connect()
        query = "SELECT * FROM Villes WHERE geoname_id = %s"
        results = MySQLConnection.execute_query(query, (geoname_id,))

        if not results:
            return None

        return Ville.from_dict(results[0])

    @staticmethod
    def get_by_name(name_en: str) -> List[Ville]:
        """Récupère les villes par nom (recherche souple, insensible à la casse)"""
        MySQLConnection.connect()
        query = "SELECT * FROM Villes WHERE LOWER(name_en) LIKE LOWER(%s)"
        pattern = f"%{name_en}%"
        results = MySQLConnection.execute_query(query, (pattern,))

        return [Ville.from_dict(row) for row in results]

    @staticmethod
    def get_by_country(country_3166a2: str) -> List[Ville]:
        """Récupère toutes les villes d'un pays"""
        MySQLConnection.connect()
        query = "SELECT * FROM Villes WHERE country_3166a2 = %s"
        results = MySQLConnection.execute_query(query, (country_3166a2.upper(),))

        return [Ville.from_dict(row) for row in results]

    @staticmethod
    def get_all(skip: int = 0, limit: int = 100) -> List[Ville]:
        """Récupère toutes les villes avec pagination"""
        MySQLConnection.connect()
        query = "SELECT * FROM Villes LIMIT %s OFFSET %s"
        results = MySQLConnection.execute_query(query, (limit, skip))

        return [Ville.from_dict(row) for row in results]

    @staticmethod
    def create(ville_data: dict) -> Ville:
        """Crée une nouvelle ville"""
        MySQLConnection.connect()
        query = """
            INSERT INTO Villes 
            (geoname_id, name_en, latitude, longitude, country_3166a2,is_capital)
            VALUES (%s, %s, %s, %s, %s,%s)
        """
        params = (
            ville_data["geoname_id"],
            ville_data["name_en"],
            ville_data.get("latitude"),
            ville_data.get("longitude"),
            ville_data.get("country_3166a2"),
            ville_data.get("is_capital"),
        )

        MySQLConnection.execute_update(query, params)
        MySQLConnection.commit()

        return VilleRepository.get_by_geoname_id(ville_data["geoname_id"])

    @staticmethod
    def update(geoname_id: int, ville_data: dict) -> Optional[Ville]:
        """Met à jour une ville existante"""
        existing = VilleRepository.get_by_geoname_id(geoname_id)
        if existing is None:
            return None

        MySQLConnection.connect()

        # Construire la requête UPDATE dynamiquement
        set_clauses = []
        params = []

        for key, value in ville_data.items():
            if value is not None:
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return existing

        params.append(geoname_id)
        query = f"UPDATE Villes SET {', '.join(set_clauses)} WHERE geoname_id = %s"

        MySQLConnection.execute_update(query, tuple(params))
        MySQLConnection.commit()

        return VilleRepository.get_by_geoname_id(geoname_id)

    @staticmethod
    def delete(geoname_id: int) -> bool:
        """Supprime une ville"""
        existing = VilleRepository.get_by_geoname_id(geoname_id)
        if existing is None:
            return False

        MySQLConnection.connect()
        query = "DELETE FROM Villes WHERE geoname_id = %s"
        MySQLConnection.execute_update(query, (geoname_id,))
        MySQLConnection.commit()

        return True

    @staticmethod
    def bulk_insert_ignore(villes_data: List[dict]) -> int:
        """Insert en masse avec INSERT IGNORE pour éviter les doublons"""
        if not villes_data:
            return 0
        query = """
            INSERT IGNORE INTO Villes
            (geoname_id, name_en, latitude, longitude, country_3166a2, is_capital)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = [
            (
                record["geoname_id"],
                record["name_en"],
                record.get("latitude"),
                record.get("longitude"),
                record.get("country_3166a2", ""),
                record.get("is_capital"),
            )
            for record in villes_data
        ]
        MySQLConnection.commit()
        return MySQLConnection.execute_update(query, values)
