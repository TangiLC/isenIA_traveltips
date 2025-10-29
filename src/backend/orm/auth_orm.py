from typing import Optional, Dict, Any
from connexion.mysql_connect import MySQLConnection
from mysql.connector import Error

DDL_UTILISATEURS = """

"""


class AuthOrm:

    @staticmethod
    def row_to_user_out(row: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": row["id"], "pseudo": row["pseudo"], "role": row["role"]}

    @staticmethod
    def get_by_name(pseudo: str) -> Optional[Dict[str, Any]]:
        q = "SELECT id, pseudo, password, role FROM Utilisateurs WHERE pseudo = %s"
        rows = MySQLConnection.execute_query(q, (pseudo,))
        return rows[0] if rows else None

    @staticmethod
    def get_by_id(uid: int) -> Optional[Dict[str, Any]]:
        q = "SELECT id, pseudo, password, role FROM Utilisateurs WHERE id = %s"
        rows = MySQLConnection.execute_query(q, (uid,))
        return rows[0] if rows else None

    @staticmethod
    def create(pseudo: str, password: str, role: str) -> int:
        try:
            q = "INSERT INTO Utilisateurs (pseudo, password, role) VALUES (%s, %s, %s)"
            MySQLConnection.execute_update(q, (pseudo, password, role))
            MySQLConnection.commit()
            row = MySQLConnection.execute_query("SELECT LAST_INSERT_ID() AS id")
            return int(row[0]["id"])
        except Error:
            MySQLConnection.rollback()
            raise

    @staticmethod
    def update_full(uid: int, pseudo: str, password: str, role: str) -> bool:
        try:
            q = """
                UPDATE Utilisateurs 
                SET pseudo = %s, password = %s, role = %s
                WHERE id = %s
            """
            count = MySQLConnection.execute_update(q, (pseudo, password, role, uid))
            MySQLConnection.commit()
            return count > 0
        except Error:
            MySQLConnection.rollback()
            raise

    @staticmethod
    def update_partial(uid: int, pseudo=None, password=None, role=None) -> bool:
        sets = []
        params = []
        if pseudo is not None:
            sets.append("pseudo = %s")
            params.append(pseudo)
        if password is not None:
            sets.append("password = %s")
            params.append(password)
        if role is not None:
            sets.append("role = %s")
            params.append(role)

        if not sets:
            return False

        params.append(uid)
        q = f"UPDATE Utilisateurs SET {', '.join(sets)} WHERE id = %s"
        try:
            count = MySQLConnection.execute_update(q, tuple(params))
            MySQLConnection.commit()
            return count > 0
        except Error:
            MySQLConnection.rollback()
            raise

    @staticmethod
    def delete(uid: int) -> bool:
        try:
            q = "DELETE FROM Utilisateurs WHERE id = %s"
            count = MySQLConnection.execute_update(q, (uid,))
            MySQLConnection.commit()
            return count > 0
        except Error:
            MySQLConnection.rollback()
            raise
