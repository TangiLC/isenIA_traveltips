from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from services.langue_service import LangueService
from schemas.langue_dto import (
    LangueResponse,
    LangueCreateRequest,
    LangueUpdateRequest,
    map_to_response,
)
from security.security import Security


router = APIRouter(prefix="/api/langues", tags=["Langues"])


@router.get(
    "/by_code_iso",
    response_model=LangueResponse,
    summary="Rechercher une langue par code ISO 639-2",
    description="Retourne une langue correspondant au code ISO 639-2 fourni",
    responses={
        200: {"description": "Langue trouvée"},
        404: {"description": "Langue non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def get_langue_by_code_iso(
    code: str = Query(..., min_length=3, max_length=3, description="Code ISO 639-2")
):
    """Recherche une langue par son code ISO 639-2"""
    try:
        result = LangueService.find_by_iso639_2(code)
        return map_to_response(result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )


@router.get(
    "/by_name",
    response_model=List[LangueResponse],
    summary="Rechercher des langues par nom",
    description="Recherche dans name_en, name_fr et name_local (insensible à la casse)",
    responses={
        200: {"description": "Liste des langues correspondantes"},
        404: {"description": "Langue non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def get_langues_by_name(
    name: str = Query(..., min_length=1, description="Terme de recherche")
):
    """Recherche des langues par nom (name_en, name_fr ou name_local)"""
    try:
        results = LangueService.find_by_name(name)
        return [map_to_response(row) for row in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )


@router.get(
    "/by_famille",
    response_model=List[LangueResponse],
    summary="Rechercher des langues par famille linguistique",
    description="Retourne toutes les langues d'une famille donnée (recherche de pattern partiel)",
    responses={
        200: {"description": "Liste des langues de la famille"},
        404: {"description": "Famille non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def get_langues_by_famille(
    famille: str = Query(
        ...,
        description="Nom de la famille (ex: 'Indo-European' ou 'indo-européenne' ou 'euro')",
    )
):
    """Recherche des langues par famille linguistique"""
    try:
        results = LangueService.find_by_famille(famille)
        return [map_to_response(row) for row in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )


@router.put(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Créer ou remplacer une langue",
    description="Insère une nouvelle langue ou remplace une existante (REPLACE INTO)",
    responses={
        201: {"description": "Langue créée ou remplacée"},
        500: {"description": "Erreur serveur lors de la création"},
    },
)
def create_or_replace_langue(
    langue: LangueCreateRequest, _=Depends(Security.secured_route)
):
    """Crée ou remplace une langue"""
    try:
        rows_affected = LangueService.create_or_replace(langue.model_dump())

        return {
            "message": f"Langue '{langue.iso639_2}' créée/remplacée avec succès",
            "rows_affected": rows_affected,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}",
        )


@router.patch(
    "/{iso639_2}",
    response_model=dict,
    summary="Mise à jour partielle d'une langue",
    description="Met à jour uniquement les champs fournis",
    responses={
        200: {"description": "Langue mise à jour"},
        404: {"description": "Langue non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def update_langue_partial(
    iso639_2: str, updates: LangueUpdateRequest, _=Depends(Security.secured_route)
):
    """Mise à jour partielle d'une langue"""
    try:
        rows_affected = LangueService.update_partial(iso639_2, updates.model_dump())

        return {
            "message": f"Langue '{iso639_2}' mise à jour avec succès",
            "rows_affected": rows_affected,
        }
    except ValueError as e:
        # Déterminer le status code selon le message
        if "introuvable" in str(e):
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}",
        )


@router.delete(
    "/{iso639_2}",
    response_model=dict,
    summary="Supprimer une langue",
    description="Supprime une langue par son code ISO 639-2",
    responses={
        200: {"description": "Langue supprimée"},
        403: {"description": "Accès interdit (route sécurisée par JWT)"},
        404: {"description": "Langue non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def delete_langue(iso639_2: str, _=Depends(Security.secured_route)):
    """Supprime une langue par son code ISO 639-2"""
    try:
        rows_affected = LangueService.delete(iso639_2)

        return {
            "message": f"Langue '{iso639_2}' supprimée avec succès",
            "rows_affected": rows_affected,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}",
        )
