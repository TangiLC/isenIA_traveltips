from typing import List, Optional, Dict, Any
from connexion.mysql_connect import MySQLConnection


class CurrencyOrm:
    """Repository pour la gestion des devises (table Monnaies)"""

    @staticmethod
    def find_by_iso4217(code: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT iso4217, name, symbol
            FROM Monnaies
            WHERE iso4217 = %s
        """
        result = MySQLConnection.execute_query(query, (code,))
        return result[0] if result else None

    @staticmethod
    def find_by_name_or_symbol(search_term: str) -> List[Dict[str, Any]]:
        """Recherche insensible à la casse dans name et symbol"""
        query = """
            SELECT iso4217, name, symbol
            FROM Monnaies
            WHERE LOWER(name) LIKE LOWER(%s)
               OR LOWER(symbol) LIKE LOWER(%s)
        """
        pattern = f"%{search_term}%"
        return MySQLConnection.execute_query(query, (pattern, pattern))

    @staticmethod
    def create_or_replace(iso4217: str, name: str, symbol: str) -> int:
        """REPLACE INTO -> crée ou remplace une devise"""
        query = """
            REPLACE INTO Monnaies (iso4217, name, symbol)
            VALUES (%s, %s, %s)
        """
        return MySQLConnection.execute_update(query, (iso4217, name, symbol))

    @staticmethod
    def insert_ignore(iso4217: str, name: str, symbol: str) -> int:
        """INSERT IGNORE -> insère uniquement si la devise n'existe pas"""
        query = """
            INSERT IGNORE INTO Monnaies (iso4217, name, symbol)
            VALUES (%s, %s, %s)
        """
        return MySQLConnection.execute_update(query, (iso4217, name, symbol))

    @staticmethod
    def update_partial(iso4217: str, updates: Dict[str, Any]) -> int:
        """Mise à jour partielle (name, symbol)"""
        allowed = {"name", "symbol"}
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return 0

        set_clause = ", ".join(f"{k} = %s" for k in filtered)
        values = list(filtered.values()) + [iso4217]
        query = f"UPDATE Monnaies SET {set_clause} WHERE iso4217 = %s"
        return MySQLConnection.execute_update(query, tuple(values))

    @staticmethod
    def delete(iso4217: str) -> int:
        query = "DELETE FROM Monnaies WHERE iso4217 = %s"
        return MySQLConnection.execute_update(query, (iso4217,))
