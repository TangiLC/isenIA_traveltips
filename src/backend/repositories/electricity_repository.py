from typing import List, Optional, Dict, Any
from connexion.mysql_connect import MySQLConnection


class ElectriciteRepository:
    """Repository pour la gestion des types de prises électriques (table Electricite)"""

    @staticmethod
    def find_by_plug_type(plug_type: str) -> Optional[Dict[str, Any]]:
        """Récupère un type de prise par son identifiant"""
        query = """
            SELECT plug_type, plug_png, sock_png
            FROM Electricite
            WHERE plug_type = %s
        """
        result = MySQLConnection.execute_query(query, (plug_type,))
        return result[0] if result else None

    @staticmethod
    def find_all() -> List[Dict[str, Any]]:
        """Récupère tous les types de prises électriques"""
        query = """
            SELECT plug_type, plug_png, sock_png
            FROM Electricite
            ORDER BY plug_type
        """
        return MySQLConnection.execute_query(query)

    @staticmethod
    def create_or_replace(plug_type: str, plug_png: str, sock_png: str) -> int:
        """REPLACE INTO -> crée ou remplace un type de prise"""
        query = """
            REPLACE INTO Electricite (plug_type, plug_png, sock_png)
            VALUES (%s, %s, %s)
        """
        return MySQLConnection.execute_update(query, (plug_type, plug_png, sock_png))

    @staticmethod
    def insert_ignore(plug_type: str, plug_png: str, sock_png: str) -> int:
        """INSERT IGNORE -> insère uniquement si le type de prise n'existe pas"""
        query = """
            INSERT IGNORE INTO Electricite (plug_type, plug_png, sock_png)
            VALUES (%s, %s, %s)
        """
        return MySQLConnection.execute_update(query, (plug_type, plug_png, sock_png))

    @staticmethod
    def update_partial(plug_type: str, updates: Dict[str, Any]) -> int:
        """Mise à jour partielle (plug_png, sock_png)"""
        allowed = {"plug_png", "sock_png"}
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return 0

        set_clause = ", ".join(f"{k} = %s" for k in filtered)
        values = list(filtered.values()) + [plug_type]
        query = f"UPDATE Electricite SET {set_clause} WHERE plug_type = %s"
        return MySQLConnection.execute_update(query, tuple(values))

    @staticmethod
    def delete(plug_type: str) -> int:
        """Supprime un type de prise"""
        query = "DELETE FROM Electricite WHERE plug_type = %s"
        return MySQLConnection.execute_update(query, (plug_type,))
