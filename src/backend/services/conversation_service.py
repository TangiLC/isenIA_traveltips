from typing import Dict, Any, Tuple
from connexion.mysql_connect import MySQLConnection
from orm.conversation_orm import ConversationOrm
from orm.langue_orm import LangueOrm


class ConversationService:
    """Service pour la gestion des conversations avec synchronisation MySQL"""

    @staticmethod
    def _sync_langue_status(lang_code: str, is_in_mongo: bool) -> None:
        """Synchronise is_in_mongo dans MySQL

        Args:
            lang_code: Code ISO 639-2
            is_in_mongo: Statut de présence dans MongoDB
        """
        try:
            MySQLConnection.connect()

            langue = LangueOrm.find_by_iso639_2(lang_code)

            if not langue:
                print(
                    f"[WARNING] Langue '{lang_code}' introuvable dans MySQL. Synchronisation ignorée."
                )
                return

            LangueOrm.update_partial(lang_code, {"is_in_mongo": is_in_mongo})
            print(f"[INFO] Langue '{lang_code}' -> is_in_mongo = {is_in_mongo}")

        except Exception as e:
            print(f"[ERROR] Échec synchronisation MySQL pour '{lang_code}': {str(e)}")
        finally:
            MySQLConnection.close()

    @staticmethod
    def create(conversation_data: Dict[str, Any]) -> Tuple[str, str]:
        """Crée une conversation et synchronise MySQL

        Args:
            conversation_data: Données de la conversation

        Returns:
            Tuple (conversation_id, lang_code)
        """
        conversation_id = ConversationOrm.create(conversation_data)

        lang_code = conversation_data.get("lang639-2")
        if lang_code:
            ConversationService._sync_langue_status(lang_code, True)

        return conversation_id, lang_code

    @staticmethod
    def delete(
        conversation_id: str, existing_conversation: Dict[str, Any]
    ) -> Tuple[int, str]:
        """Supprime une conversation et synchronise MySQL

        Args:
            conversation_id: ID de la conversation
            existing_conversation: Document conversation existant

        Returns:
            Tuple (deleted_count, lang_code)
        """
        lang_code = existing_conversation.get("lang639-2")

        deleted_count = ConversationOrm.delete(conversation_id)

        if lang_code:
            ConversationService._sync_langue_status(lang_code, False)

        return deleted_count, lang_code

    @staticmethod
    def validate_lang_unchanged(
        existing: Dict[str, Any], new_data: Dict[str, Any]
    ) -> None:
        """Valide que lang639-2 n'a pas changé

        Args:
            existing: Conversation existante
            new_data: Nouvelles données

        Raises:
            ValueError: Si lang639-2 a changé
        """
        existing_lang = existing.get("lang639-2")
        new_lang = new_data.get("lang639-2")

        if existing_lang != new_lang:
            raise ValueError(
                f"Modification de 'lang639-2' interdite. "
                f"Valeur actuelle: '{existing_lang}', valeur demandée: '{new_lang}'"
            )

    @staticmethod
    def validate_no_lang_in_updates(update_data: Dict[str, Any]) -> None:
        """Valide qu'il n'y a pas de lang639-2 dans les updates

        Args:
            update_data: Données de mise à jour MongoDB ($set)

        Raises:
            ValueError: Si lang639-2 est présent
        """
        if update_data.get("$set") and "lang639-2" in update_data["$set"]:
            raise ValueError(
                "Modification du champ 'lang639-2' interdite. "
                "Seuls les champs comme 'sentences' peuvent être modifiés."
            )
