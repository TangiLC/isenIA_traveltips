from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List
from bson.errors import InvalidId
from connexion.mongo_connect import MongoDBConnection
from connexion.mysql_connect import MySQLConnection
from repositories.conversation_repository import ConversationRepository
from repositories.langue_repository import LangueRepository
from schemas.conversation_dto import (
    ConversationResponse,
    ConversationCreateRequest,
    ConversationUpdateRequest,
    ConversationListResponse,
)
from security.security import Security

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


def sync_langue_mongo_status(lang_code: str, is_in_mongo: bool):
    """Helper pour synchroniser le statut is_in_mongo dans MySQL

    Args:
        lang_code: Code ISO 639-2 de la langue
        is_in_mongo: True si la langue existe dans MongoDB, False sinon
    """
    try:
        MySQLConnection.connect()

        # Vérifier que la langue existe dans MySQL
        langue = LangueRepository.find_by_iso639_2(lang_code)

        if not langue:
            print(
                f"[WARNING] Langue '{lang_code}' introuvable dans MySQL. Synchronisation ignorée."
            )
            return

        # Mettre à jour is_in_mongo
        LangueRepository.update_partial(lang_code, {"is_in_mongo": is_in_mongo})
        print(f"[INFO] Langue '{lang_code}' -> is_in_mongo = {is_in_mongo}")

    except Exception as e:
        print(f"[ERROR] Échec synchronisation MySQL pour '{lang_code}': {str(e)}")
    finally:
        MySQLConnection.close()


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="Liste toutes les conversations",
    description="Retourne toutes les conversations avec pagination",
    responses={
        200: {"description": "Liste des conversations"},
        500: {"description": "Erreur serveur"},
    },
)
def get_all_conversations(
    skip: int = Query(0, ge=0, description="Nombre de conversations à ignorer"),
    limit: int = Query(100, ge=1, le=500, description="Nombre max de conversations"),
):
    try:
        MongoDBConnection.connect()

        conversations = ConversationRepository.find_all(limit=limit, skip=skip)
        total = ConversationRepository.count_all()

        return ConversationListResponse(
            total=total,
            conversations=[
                ConversationResponse.from_mongo(conv) for conv in conversations
            ],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )
    finally:
        MongoDBConnection.close()


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Récupère une conversation par ID",
    description="Retourne une conversation spécifique par son _id MongoDB",
    responses={
        200: {"description": "Conversation trouvée"},
        404: {"description": "Conversation non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def get_conversation_by_id(
    conversation_id: str = Path(..., description="ID MongoDB de la conversation"),
):
    try:
        MongoDBConnection.connect()

        conversation = ConversationRepository.find_by_id(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation avec l'ID '{conversation_id}' introuvable",
            )

        return ConversationResponse.from_mongo(conversation)
    except HTTPException:
        raise
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID MongoDB invalide: '{conversation_id}'",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )
    finally:
        MongoDBConnection.close()


@router.get(
    "/by_lang/{lang_code}",
    response_model=List[ConversationResponse],
    summary="Recherche par code langue",
    description="Retourne toutes les conversations d'une langue donnée (ISO 639-2)",
    responses={
        200: {"description": "Liste des conversations"},
        500: {"description": "Erreur serveur"},
    },
)
def get_conversations_by_lang(
    lang_code: str = Path(
        ..., min_length=3, max_length=3, description="Code ISO 639-2"
    ),
    limit: int = Query(100, ge=1, le=500, description="Nombre max de résultats"),
):
    try:
        MongoDBConnection.connect()

        conversations = ConversationRepository.find_by_lang(lang_code, limit=limit)

        return [ConversationResponse.from_mongo(conv) for conv in conversations]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )
    finally:
        MongoDBConnection.close()


@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle conversation",
    description="Insère une nouvelle conversation dans MongoDB avec schéma flexible",
    responses={
        201: {"description": "Conversation créée"},
        400: {"description": "Données invalides"},
        500: {"description": "Erreur serveur"},
    },
)
def create_conversation(
    conversation: ConversationCreateRequest, _=Depends(Security.secured_route)
):
    try:
        MongoDBConnection.connect()

        # Convertir le DTO en document MongoDB
        conversation_data = conversation.to_mongo()

        # Insérer dans MongoDB
        conversation_id = ConversationRepository.create(conversation_data)

        # Synchroniser is_in_mongo = True dans MySQL
        lang_code = conversation_data.get("lang639-2")
        if lang_code:
            sync_langue_mongo_status(lang_code, True)

        return {
            "message": "Conversation créée avec succès",
            "id": conversation_id,
            "lang639-2": lang_code,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Données invalides: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}",
        )
    finally:
        MongoDBConnection.close()


@router.patch(
    "/{conversation_id}",
    response_model=dict,
    summary="Mise à jour partielle d'une conversation",
    description="Met à jour uniquement les champs fournis (schéma flexible). Modification de lang639-2 interdite.",
    responses={
        200: {"description": "Conversation mise à jour"},
        404: {"description": "Conversation non trouvée"},
        400: {
            "description": "Données invalides ou modification de lang639-2 interdite"
        },
        500: {"description": "Erreur serveur"},
    },
)
def update_conversation(
    conversation_id: str = Path(..., description="ID MongoDB de la conversation"),
    updates: ConversationUpdateRequest = ...,
    _=Depends(Security.secured_route),
):
    try:
        MongoDBConnection.connect()

        # Vérifier que la conversation existe
        existing = ConversationRepository.find_by_id(conversation_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation avec l'ID '{conversation_id}' introuvable",
            )

        # Convertir en opération MongoDB $set
        update_data = updates.to_mongo_update()

        # VERROUILLAGE : Interdire modification de lang639-2
        if update_data.get("$set") and "lang639-2" in update_data["$set"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Modification du champ 'lang639-2' interdite. Seuls les champs comme 'sentences' peuvent être modifiés.",
            )

        if not update_data.get("$set"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun champ à mettre à jour",
            )

        # Exécuter la mise à jour
        modified_count = ConversationRepository.update(conversation_id, update_data)

        return {
            "message": f"Conversation '{conversation_id}' mise à jour avec succès",
            "modified_count": modified_count,
        }
    except HTTPException:
        raise
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID MongoDB invalide: '{conversation_id}'",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Données invalides: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}",
        )
    finally:
        MongoDBConnection.close()


@router.put(
    "/{conversation_id}",
    response_model=dict,
    summary="Remplacement complet d'une conversation",
    description="Remplace entièrement une conversation (tous les champs). Modification de lang639-2 interdite.",
    responses={
        200: {"description": "Conversation remplacée"},
        404: {"description": "Conversation non trouvée"},
        400: {
            "description": "Données invalides ou tentative de modification de lang639-2"
        },
        500: {"description": "Erreur serveur"},
    },
)
def replace_conversation(
    conversation_id: str = Path(..., description="ID MongoDB de la conversation"),
    conversation: ConversationCreateRequest = ...,
    _=Depends(Security.secured_route),
):
    try:
        MongoDBConnection.connect()

        # Vérifier que la conversation existe
        existing = ConversationRepository.find_by_id(conversation_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation avec l'ID '{conversation_id}' introuvable",
            )

        # Convertir le DTO en document MongoDB
        conversation_data = conversation.to_mongo()

        # VERROUILLAGE : Vérifier que lang639-2 n'a pas changé
        existing_lang = existing.get("lang639-2")
        new_lang = conversation_data.get("lang639-2")

        if existing_lang != new_lang:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Modification de 'lang639-2' interdite. Valeur actuelle: '{existing_lang}', valeur demandée: '{new_lang}'",
            )

        # Remplacer (sans modifier l'_id)
        update_data = {"$set": conversation_data}
        modified_count = ConversationRepository.update(conversation_id, update_data)

        return {
            "message": f"Conversation '{conversation_id}' remplacée avec succès",
            "modified_count": modified_count,
        }
    except HTTPException:
        raise
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID MongoDB invalide: '{conversation_id}'",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Données invalides: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du remplacement: {str(e)}",
        )
    finally:
        MongoDBConnection.close()


@router.delete(
    "/{conversation_id}",
    response_model=dict,
    summary="Supprimer une conversation",
    description="Supprime une conversation par son _id MongoDB et met à jour is_in_mongo dans MySQL",
    responses={
        200: {"description": "Conversation supprimée"},
        404: {"description": "Conversation non trouvée"},
        400: {"description": "ID invalide"},
        500: {"description": "Erreur serveur"},
    },
)
def delete_conversation(
    conversation_id: str = Path(..., description="ID MongoDB de la conversation"),
    _=Depends(Security.secured_route),
):
    try:
        MongoDBConnection.connect()

        # Vérifier que la conversation existe et récupérer lang639-2
        existing = ConversationRepository.find_by_id(conversation_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation avec l'ID '{conversation_id}' introuvable",
            )

        lang_code = existing.get("lang639-2")

        # Supprimer
        deleted_count = ConversationRepository.delete(conversation_id)

        # Synchroniser is_in_mongo = False dans MySQL
        # Pas de count car il n'y a qu'une seule conversation par langue
        if lang_code:
            sync_langue_mongo_status(lang_code, False)

        return {
            "message": f"Conversation '{conversation_id}' supprimée avec succès",
            "deleted_count": deleted_count,
            "lang639-2": lang_code,
        }
    except HTTPException:
        raise
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID MongoDB invalide: '{conversation_id}'",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}",
        )
    finally:
        MongoDBConnection.close()
