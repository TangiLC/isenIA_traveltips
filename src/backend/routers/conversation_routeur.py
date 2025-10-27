from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List
from bson.errors import InvalidId
from connexion.mongo_connect import MongoDBConnection
from services.conversation_service import ConversationService

# from connexion.mysql_connect import MySQLConnection
from repositories.conversation_repository import ConversationRepository

# from repositories.langue_repository import LangueRepository
from schemas.conversation_dto import (
    ConversationResponse,
    ConversationCreateRequest,
    ConversationUpdateRequest,
    ConversationListResponse,
)
from security.security import Security

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


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
        conversation_id, lang_code = ConversationService.create(conversation_data)

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
        try:
            ConversationService.validate_no_lang_in_updates(update_data)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
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
        try:
            ConversationService.validate_lang_unchanged(existing, conversation_data)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
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

        # Supprimer et synchroniser MySQL
        deleted_count, lang_code = ConversationService.delete(conversation_id, existing)

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
