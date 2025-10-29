from typing import List, Optional, Dict, Any
from bson import ObjectId
from bson.errors import InvalidId
from connexion.mongo_connect import MongoDBConnection


class ConversationOrm:
    """Repository pour la gestion des conversations (collection conversations)"""

    COLLECTION_NAME = "conversations"

    @staticmethod
    def find_by_id(conversation_id: str) -> Optional[Dict[str, Any]]:
        """Recherche une conversation par son _id

        Args:
            conversation_id (str): ID de la conversation

        Returns:
            Dict ou None si non trouvée
        """
        try:
            obj_id = ObjectId(conversation_id)
            return MongoDBConnection.find_one(
                ConversationOrm.COLLECTION_NAME, {"_id": obj_id}
            )
        except InvalidId:
            return None

    @staticmethod
    def find_all(limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Retourne toutes les conversations avec pagination

        Args:
            limit (int): Nombre max de résultats
            skip (int): Nombre de documents à ignorer

        Returns:
            Liste de conversations
        """
        collection = MongoDBConnection.get_collection(ConversationOrm.COLLECTION_NAME)
        cursor = collection.find().skip(skip).limit(limit)
        return list(cursor)

    @staticmethod
    def find_by_lang(lang_code: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Recherche des conversations par code langue

        Args:
            lang_code (str): Code ISO 639-2
            limit (int): Nombre max de résultats

        Returns:
            Liste de conversations
        """
        return MongoDBConnection.find(
            ConversationOrm.COLLECTION_NAME,
            {"lang639-2": lang_code.lower()},
            limit=limit,
        )

    @staticmethod
    def create(conversation_data: Dict[str, Any]) -> str:
        """Crée une nouvelle conversation

        Args:
            conversation_data (dict): Données de la conversation

        Returns:
            str: ID de la conversation créée
        """
        result = MongoDBConnection.insert_one(
            ConversationOrm.COLLECTION_NAME, conversation_data
        )
        return str(result.inserted_id)

    @staticmethod
    def update(conversation_id: str, update_data: Dict[str, Any]) -> int:
        """Met à jour une conversation

        Args:
            conversation_id (str): ID de la conversation
            update_data (dict): Données à mettre à jour (opération $set)

        Returns:
            int: Nombre de documents modifiés
        """
        try:
            obj_id = ObjectId(conversation_id)
            result = MongoDBConnection.update_one(
                ConversationOrm.COLLECTION_NAME, {"_id": obj_id}, update_data
            )
            return result.modified_count
        except InvalidId:
            return 0

    @staticmethod
    def delete(conversation_id: str) -> int:
        """Supprime une conversation

        Args:
            conversation_id (str): ID de la conversation

        Returns:
            int: Nombre de documents supprimés
        """
        try:
            obj_id = ObjectId(conversation_id)
            result = MongoDBConnection.delete_one(
                ConversationOrm.COLLECTION_NAME, {"_id": obj_id}
            )
            return result.deleted_count
        except InvalidId:
            return 0

    @staticmethod
    def count_all() -> int:
        """Compte le nombre total de conversations

        Returns:
            int: Nombre de conversations
        """
        return MongoDBConnection.count_documents(ConversationOrm.COLLECTION_NAME)

    @staticmethod
    def count_by_lang(lang_code: str) -> int:
        """Compte les conversations par langue

        Args:
            lang_code (str): Code ISO 639-2

        Returns:
            int: Nombre de conversations
        """
        return MongoDBConnection.count_documents(
            ConversationOrm.COLLECTION_NAME, {"lang639-2": lang_code.lower()}
        )

    @staticmethod
    def search_by_field(
        field_name: str, field_value: Any, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Recherche générique par n'importe quel champ

        Args:
            field_name (str): Nom du champ
            field_value (Any): Valeur recherchée
            limit (int): Nombre max de résultats

        Returns:
            Liste de conversations
        """
        return MongoDBConnection.find(
            ConversationOrm.COLLECTION_NAME,
            {field_name: field_value},
            limit=limit,
        )

    @staticmethod
    def aggregate_by_lang() -> List[Dict[str, Any]]:
        """Agrégation: compte les conversations par langue

        Returns:
            Liste de statistiques par langue
        """
        pipeline = [
            {"$group": {"_id": "$lang639-2", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$project": {"_id": 0, "lang_code": "$_id", "count": 1}},
        ]
        return MongoDBConnection.aggregate(ConversationOrm.COLLECTION_NAME, pipeline)
