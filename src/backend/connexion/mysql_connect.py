from pathlib import Path
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv


class Connection:
    """Classe de gestion de connexion MySQL"""

    connexion = None
    cursor = None
    base_dir = Path(__file__).resolve().parents[2]
    init_sql_path = base_dir / "db" / "init_script_lang.sql"

    @classmethod
    def _load_env_config(cls):
        """Charge la configuration depuis les variables d'environnement"""
        load_dotenv()

        config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", 3307)),
            "database": os.getenv("MYSQL_DATABASE"),
            "user": os.getenv("MYSQL_USER"),
            "password": os.getenv("MYSQL_PASSWORD"),
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
            "autocommit": False,
        }

        # Vérifier que les paramètres obligatoires sont présents
        required_fields = ["database", "user", "password"]
        missing_fields = [field for field in required_fields if not config.get(field)]

        if missing_fields:
            raise ValueError(
                f"Variables d'environnement manquantes: {', '.join(missing_fields)}"
            )

        return config

    @classmethod
    def connect(cls):
        """Établit la connexion à la base de données MySQL"""
        if cls.connexion is None:
            try:
                config = cls._load_env_config()

                print(f"Connexion à MySQL sur {config['host']}:{config['port']}...")

                cls.connexion = mysql.connector.connect(**config)

                if cls.connexion.is_connected():
                    db_info = cls.connexion.server_info
                    print(f"✅ Connecté à MySQL Server version {db_info}")
                    print(f"✅ Base de données: {config['database']}")
                else:
                    raise Error("Échec de la connexion")

            except Error as e:
                print(f"❌ Erreur de connexion MySQL: {e}")
                cls.connexion = None
                raise
            except ValueError as e:
                print(f"❌ Erreur de configuration: {e}")
                raise
            except Exception as e:
                print(f"❌ Erreur inattendue: {e}")
                cls.connexion = None
                raise

        if cls.cursor is None and cls.connexion is not None:
            cls.cursor = cls.connexion.cursor(dictionary=True)

        # === Lancer le script d'initialisation dès la connexion ===
        try:
            cls.run_sql_script(cls.init_sql_path)
            cls.commit()
            print("✅ Script d'initialisation exécuté.")
        except FileNotFoundError:
            # On n'échoue pas la connexion si le fichier n'est pas présent,
            # mais on remonte l'info clairement.
            print(f"ℹ️  Script d'init introuvable: {cls.init_sql_path} (connexion OK).")
        except Exception as e:
            cls.rollback()
            print(f"❌ Échec exécution script d'init: {e}")
            raise

    @classmethod
    def run_sql_script(cls, path):
        """
        Exécute un script SQL simple (CREATE/INSERT/etc.) sans blocs DELIMITER.
        Suppose un SQL "plat" où ';' termine chaque instruction.
        """
        if cls.cursor is None:
            cls.connect()

        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()

        # Découpage naïf sur ';' et retrait des commentaires '--' et '#'
        statements = []
        for raw in sql.split(";"):
            stmt = raw.strip()
            if not stmt:
                continue
            lines = []
            for line in stmt.splitlines():
                l = line.strip()
                if l.startswith("--") or l.startswith("#"):
                    continue
                lines.append(l)
            stmt = "\n".join(lines).strip()
            if stmt:
                cls.execute_update(stmt)

    @classmethod
    def commit(cls):
        """Valide la transaction en cours"""
        if cls.connexion is not None:
            try:
                cls.connexion.commit()
            except Error as e:
                print(f"❌ Erreur lors du commit: {e}")
                raise

    @classmethod
    def rollback(cls):
        """Annule la transaction en cours"""
        if cls.connexion is not None:
            try:
                cls.connexion.rollback()
                print("⚠️  Transaction annulée (rollback)")
            except Error as e:
                print(f"❌ Erreur lors du rollback: {e}")
                raise

    @classmethod
    def close(cls):
        """Ferme le curseur et la connexion"""
        if cls.cursor is not None:
            cls.cursor.close()
            cls.cursor = None

        if cls.connexion is not None:
            if cls.connexion.is_connected():
                cls.connexion.close()
                print("✅ Connexion MySQL fermée")
            cls.connexion = None

    @classmethod
    def execute_query(cls, query, params=None):
        """Exécute une requête SELECT et retourne les résultats

        Args:
            query (str): Requête SQL
            params (tuple/dict, optional): Paramètres de la requête

        Returns:
            list: Liste des résultats
        """
        if cls.cursor is None:
            cls.connect()

        try:
            cls.cursor.execute(query, params or ())
            return cls.cursor.fetchall()
        except Error as e:
            print(f"❌ Erreur d'exécution de requête: {e}")
            raise

    @classmethod
    def execute_update(cls, query, params=None):
        """Exécute une requête INSERT/UPDATE/DELETE

        Args:
            query (str): Requête SQL
            params (tuple/dict, optional): Paramètres de la requête

        Returns:
            int: Nombre de lignes affectées
        """
        if cls.cursor is None:
            cls.connect()

        try:
            cls.cursor.execute(query, params or ())
            return cls.cursor.rowcount
        except Error as e:
            print(f"❌ Erreur d'exécution de mise à jour: {e}")
            cls.rollback()
            raise


# Exemple d'utilisation
if __name__ == "__main__":
    try:
        # Connexion
        Connection.connect()

        # Test de requête
        result = Connection.execute_query("SELECT DATABASE()")
        print(f"Base de données active: {result}")

        # Test sur la table Famille
        familles = Connection.execute_query("SELECT * FROM Familles LIMIT 5")
        print(f"\nFamilles linguistiques: {familles}")

    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        Connection.close()
