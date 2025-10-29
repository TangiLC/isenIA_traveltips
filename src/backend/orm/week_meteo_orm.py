from __future__ import annotations
from typing import List, Optional, Iterable, Tuple
from datetime import date
from models.week_meteo import WeekMeteo
from connexion.mysql_connect import MySQLConnection


class WeekMeteoOrm:
    """Accès table Meteo_Weekly (clé unique: geoname_id + week_start_date)."""

    @staticmethod
    def get_by_pk(geoname_id: int, week_start_date: date) -> Optional[WeekMeteo]:
        MySQLConnection.connect()
        q = """
            SELECT geoname_id, week_start_date, week_end_date,
                   temperature_max_avg, temperature_min_avg, precipitation_sum
            FROM Meteo_Weekly
            WHERE geoname_id = %s AND week_start_date = %s
        """
        rows = MySQLConnection.execute_query(q, (geoname_id, week_start_date))
        if not rows:
            return None
        return WeekMeteo.from_dict(rows[0])

    @staticmethod
    def get_range(
        geoname_id: int, start_date: Optional[date], end_date: Optional[date]
    ) -> List[WeekMeteo]:
        MySQLConnection.connect()
        if start_date and end_date:
            q = """
                SELECT geoname_id, week_start_date, week_end_date,
                       temperature_max_avg, temperature_min_avg, precipitation_sum
                FROM Meteo_Weekly
                WHERE geoname_id = %s
                  AND week_start_date >= %s
                  AND week_end_date <= %s
                ORDER BY week_start_date ASC
            """
            params = (geoname_id, start_date, end_date)
        else:
            q = """
                SELECT geoname_id, week_start_date, week_end_date,
                       temperature_max_avg, temperature_min_avg, precipitation_sum
                FROM Meteo_Weekly
                WHERE geoname_id = %s
                ORDER BY week_start_date ASC
            """
            params = (geoname_id,)
        rows = MySQLConnection.execute_query(q, params)
        return [WeekMeteo.from_dict(r) for r in rows]

    @staticmethod
    def get_all(skip: int = 0, limit: int = 100) -> List[WeekMeteo]:
        MySQLConnection.connect()
        q = """
            SELECT geoname_id, week_start_date, week_end_date,
                   temperature_max_avg, temperature_min_avg, precipitation_sum
            FROM Meteo_Weekly
            ORDER BY geoname_id, week_start_date
            LIMIT %s OFFSET %s
        """
        rows = MySQLConnection.execute_query(q, (limit, skip))
        return [WeekMeteo.from_dict(r) for r in rows]

    @staticmethod
    def get_existing_geoname_ids() -> set:
        """
        Récupère la liste des geoname_id distincts présents dans Meteo_Weekly.
        Utilisé pour filtrer les villes déjà chargées lors d'ETL incrémentaux.

        Returns:
            set: Ensemble des geoname_id présents en base
        """
        MySQLConnection.connect()
        q = "SELECT DISTINCT geoname_id FROM Meteo_Weekly"
        rows = MySQLConnection.execute_query(q)
        return {row["geoname_id"] for row in rows}

    @staticmethod
    def upsert(item: WeekMeteo) -> WeekMeteo:
        MySQLConnection.connect()
        q = """
            INSERT INTO Meteo_Weekly
            (geoname_id, week_start_date, week_end_date,
             temperature_max_avg, temperature_min_avg, precipitation_sum)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              week_end_date = VALUES(week_end_date),
              temperature_max_avg = VALUES(temperature_max_avg),
              temperature_min_avg = VALUES(temperature_min_avg),
              precipitation_sum = VALUES(precipitation_sum)
        """
        params = (
            item.geoname_id,
            item.week_start_date,
            item.week_end_date,
            item.temperature_max_avg,
            item.temperature_min_avg,
            item.precipitation_sum,
        )
        MySQLConnection.execute_update(q, params)
        MySQLConnection.commit()
        return WeekMeteoOrm.get_by_pk(item.geoname_id, item.week_start_date)

    @staticmethod
    def bulk_upsert(items: Iterable[WeekMeteo]) -> int:
        items = list(items)
        if not items:
            return 0
        MySQLConnection.connect()
        q = """
            INSERT INTO Meteo_Weekly
            (geoname_id, week_start_date, week_end_date,
             temperature_max_avg, temperature_min_avg, precipitation_sum)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              week_end_date = VALUES(week_end_date),
              temperature_max_avg = VALUES(temperature_max_avg),
              temperature_min_avg = VALUES(temperature_min_avg),
              precipitation_sum = VALUES(precipitation_sum)
        """
        values = [
            (
                it.geoname_id,
                it.week_start_date,
                it.week_end_date,
                it.temperature_max_avg,
                it.temperature_min_avg,
                it.precipitation_sum,
            )
            for it in items
        ]
        # executemany géré dans MySQLConnection.execute_update(...)
        rowcount = MySQLConnection.execute_update(q, values)
        MySQLConnection.commit()
        return rowcount

    @staticmethod
    def delete(geoname_id: int, week_start_date: date) -> bool:
        MySQLConnection.connect()
        q = "DELETE FROM Meteo_Weekly WHERE geoname_id = %s AND week_start_date = %s"
        rc = MySQLConnection.execute_update(q, (geoname_id, week_start_date))
        MySQLConnection.commit()
        return rc > 0
