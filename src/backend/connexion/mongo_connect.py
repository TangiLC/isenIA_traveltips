from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import os
from dotenv import load_dotenv


class MongoDBConnection:
    """Classe de gestion de connexion MongoDB"""

    client = None
    db = None
    base_dir = Path(__file__).resolve().parents[2]

    @classmethod
    def _load_env_config(cls):
        """Charge la configuration depuis les variables d'environnement"""
        load_dotenv()

        config = {
            "host": os.getenv("MONGODB_HOST", "localhost"),
            "port": int(os.getenv("MONGODB_PORT", 27017)),
            "database": os.getenv("MONGO_DATABASE"),
            "username": os.getenv("MONGO_ROOT_USER"),
            "password": os.getenv("MONGO_ROOT_PASSWORD"),
            "authSource": "admin",  # Base d'authentification
            "serverSelectionTimeoutMS": 5000,
        }

        # Vérifier que les paramètres obligatoires sont présents
        required_fields = ["database", "username", "password"]
        missing_fields = [field for field in required_fields if not config.get(field)]

        if missing_fields:
            raise ValueError(
                f"Variables d'environnement manquantes: {', '.join(missing_fields)}"
            )

        return config

    @classmethod
    def connect(cls):
        """Établit la connexion à la base de données MongoDB"""
        if cls.client is None:
            try:
                config = cls._load_env_config()

                print(f"Connexion à MongoDB sur {config['host']}:{config['port']}...")

                # Construction de l'URI de connexion
                uri = (
                    f"mongodb://{config['username']}:{config['password']}@"
                    f"{config['host']}:{config['port']}/"
                    f"?authSource={config['authSource']}"
                )

                cls.client = MongoClient(
                    uri, serverSelectionTimeoutMS=config["serverSelectionTimeoutMS"]
                )

                # Tester la connexion
                cls.client.admin.command("ping")

                # Sélectionner la base de données
                cls.db = cls.client[config["database"]]

                server_info = cls.client.server_info()
                print(f"Connecté à MongoDB Server version {server_info['version']}")
                print(f"Base de données: {config['database']}")

            except ConnectionFailure as e:
                print(f"Erreur de connexion MongoDB: {e}")
                cls.client = None
                cls.db = None
                raise
            except ValueError as e:
                print(f"Erreur de configuration: {e}")
                raise
            except Exception as e:
                print(f"Erreur inattendue: {e}")
                cls.client = None
                cls.db = None
                raise

    @classmethod
    def close(cls):
        """Ferme la connexion"""
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.db = None
            print("Connexion MongoDB fermée")

    @classmethod
    def get_collection(cls, collection_name):
        """Retourne une collection MongoDB\n
        Args:
            collection_name (str): Nom de la collection\n
        Returns:
            Collection: Collection MongoDB
        """
        if cls.db is None:
            cls.connect()
        return cls.db[collection_name]

    @classmethod
    def find(cls, collection_name, query=None, projection=None, limit=0):
        """Exécute une requête de recherche\n
        Args:\n
            collection_name (str): Nom de la collection\n
            query (dict, optional): Filtre de recherche\n
            projection (dict, optional): Champs à retourner\n
            limit (int, optional): Nombre maximum de documents\n
        Returns:
            list: Liste des documents trouvés
        """
        if cls.db is None:
            cls.connect()

        try:
            collection = cls.get_collection(collection_name)
            cursor = collection.find(query or {}, projection)

            if limit > 0:
                cursor = cursor.limit(limit)

            return list(cursor)
        except OperationFailure as e:
            print(f"Erreur d'exécution de requête: {e}")
            raise

    @classmethod
    def find_one(cls, collection_name, query=None, projection=None):
        """Trouve un seul document\n
        Args:\n
            collection_name (str): Nom de la collection\n
            query (dict, optional): Filtre de recherche\n
            projection (dict, optional): Champs à retourner\n
        Returns:
            dict: Document trouvé ou None
        """
        if cls.db is None:
            cls.connect()

        try:
            collection = cls.get_collection(collection_name)
            return collection.find_one(query or {}, projection)
        except OperationFailure as e:
            print(f"Erreur d'exécution de requête: {e}")
            raise

    @classmethod
    def insert_one(cls, collection_name, document):
        """Insère un document\n
        Args:\n
            collection_name (str): Nom de la collection\n
            document (dict): Document à insérer\n
        Returns:
            InsertOneResult: Résultat de l'insertion
        """
        if cls.db is None:
            cls.connect()

        try:
            collection = cls.get_collection(collection_name)
            result = collection.insert_one(document)
            print(f"Document inséré avec l'ID: {result.inserted_id}")
            return result
        except OperationFailure as e:
            print(f"Erreur d'insertion: {e}")
            raise

    @classmethod
    def insert_many(cls, collection_name, documents):
        """Insère plusieurs documents\n
        Args:\n
            collection_name (str): Nom de la collection\n
            documents (list): Liste de documents à insérer\n
        Returns:
            InsertManyResult: Résultat de l'insertion
        """
        if cls.db is None:
            cls.connect()

        try:
            collection = cls.get_collection(collection_name)
            result = collection.insert_many(documents)
            print(f"{len(result.inserted_ids)} documents insérés")
            return result
        except OperationFailure as e:
            print(f"Erreur d'insertion multiple: {e}")
            raise

    @classmethod
    def update_one(cls, collection_name, query, update, upsert=False):
        """Met à jour un document\n
        Args:\n
            collection_name (str): Nom de la collection\n
            query (dict): Filtre de sélection\n
            update (dict): Opérations de mise à jour\n
            upsert (bool): Créer le document s'il n'existe pas\n
        Returns:
            UpdateResult: Résultat de la mise à jour
        """
        if cls.db is None:
            cls.connect()

        try:
            collection = cls.get_collection(collection_name)
            result = collection.update_one(query, update, upsert=upsert)
            print(f"{result.modified_count} document(s) modifié(s)")
            return result
        except OperationFailure as e:
            print(f"Erreur de mise à jour: {e}")
            raise

    @classmethod
    def update_many(cls, collection_name, query, update, upsert=False):
        """Met à jour plusieurs documents\n
        Args:\n
            collection_name (str): Nom de la collection\n
            query (dict): Filtre de sélection\n
            update (dict): Opérations de mise à jour\n
            upsert (bool): Créer les documents s'ils n'existent pas\n
        Returns:
            UpdateResult: Résultat de la mise à jour
        """
        if cls.db is None:
            cls.connect()

        try:
            collection = cls.get_collection(collection_name)
            result = collection.update_many(query, update, upsert=upsert)
            print(f"{result.modified_count} document(s) modifié(s)")
            return result
        except OperationFailure as e:
            print(f"Erreur de mise à jour multiple: {e}")
            raise

    @classmethod
    def delete_one(cls, collection_name, query):
        """Supprime un document\n
        Args:\n
            collection_name (str): Nom de la collection\n
            query (dict): Filtre de sélection\n
        Returns:\n
            DeleteResult: Résultat de la suppression\n
        """
        if cls.db is None:
            cls.connect()

        try:
            collection = cls.get_collection(collection_name)
            result = collection.delete_one(query)
            print(f"{result.deleted_count} document(s) supprimé(s)")
            return result
        except OperationFailure as e:
            print(f"Erreur de suppression: {e}")
            raise

    @classmethod
    def delete_many(cls, collection_name, query):
        """Supprime plusieurs documents\n
        Args:\n
            collection_name (str): Nom de la collection\n
            query (dict): Filtre de sélection\n
        Returns:
            DeleteResult: Résultat de la suppression
        """
        if cls.db is None:
            cls.connect()

        try:
            collection = cls.get_collection(collection_name)
            result = collection.delete_many(query)
            print(f"{result.deleted_count} document(s) supprimé(s)")
            return result
        except OperationFailure as e:
            print(f"Erreur de suppression multiple: {e}")
            raise

    @classmethod
    def count_documents(cls, collection_name, query=None):
        """Compte les documents dans une collection\n
        Args:\n
            collection_name (str): Nom de la collection\n
            query (dict, optional): Filtre de sélection\n
        Returns:
            int: Nombre de documents
        """
        if cls.db is None:
            cls.connect()

        try:
            collection = cls.get_collection(collection_name)
            return collection.count_documents(query or {})
        except OperationFailure as e:
            print(f"Erreur de comptage: {e}")
            raise

    @classmethod
    def aggregate(cls, collection_name, pipeline):
        """Exécute une pipeline d'agrégation\n
        Args:\n
            collection_name (str): Nom de la collection\n
            pipeline (list): Pipeline d'agrégation MongoDB\n
        Returns:
            list: Résultats de l'agrégation
        """
        if cls.db is None:
            cls.connect()

        try:
            collection = cls.get_collection(collection_name)
            return list(collection.aggregate(pipeline))
        except OperationFailure as e:
            print(f"Erreur d'agrégation: {e}")
            raise


# Exemple d'utilisation
if __name__ == "__main__":
    try:
        # Connexion
        MongoDBConnection.connect()

        # Test: Lister les collections
        collections = MongoDBConnection.db.list_collection_names()
        print(f"Collections disponibles: {collections}")

        # Test: Insérer un document
        test_doc = {"nom": "Test", "description": "Document de test", "actif": True}
        result = MongoDBConnection.insert_one("test_collection", test_doc)

        # Test: Rechercher des documents
        documents = MongoDBConnection.find("test_collection", limit=5)
        print(f"\nDocuments trouvés: {len(documents)}")
        for doc in documents:
            print(doc)

        # Test: Compter les documents
        count = MongoDBConnection.count_documents("test_collection")
        print(f"\nNombre total de documents: {count}")

    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        MongoDBConnection.close()
