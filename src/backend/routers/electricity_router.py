from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from schemas.electricity_dto import (
    ElectriciteResponse,
    ElectriciteCreateRequest,
    ElectriciteUpdateRequest,
    map_to_response,
)
from services.electricity_service import ElectricityService
from security.security import Security

router = APIRouter(prefix="/api/electricite", tags=["Electricite"])


@router.get(
    "",
    response_model=List[ElectriciteResponse],
    summary="Lister tous les types de prises",
    description="Retourne la liste complète des types de prises électriques",
    responses={
        200: {"description": "Liste des types de prises"},
        500: {"description": "Erreur serveur"},
    },
)
def get_all_plug_types():
    try:
        results = ElectricityService.find_all()
        return [map_to_response(r) for r in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )


@router.get(
    "/{plug_type}",
    response_model=ElectriciteResponse,
    summary="Rechercher un type de prise par son identifiant",
    description="Retourne les informations d'un type de prise (A-N)",
    responses={
        200: {"description": "Type de prise trouvé"},
        404: {"description": "Type de prise non trouvé"},
        500: {"description": "Erreur serveur"},
    },
)
def get_plug_type_by_id(plug_type: str):
    try:
        result = ElectricityService.find_by_plug_type(plug_type)
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


@router.put(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Créer ou remplacer un type de prise",
    description="Insère un nouveau type de prise ou remplace un existant (REPLACE INTO)",
    responses={
        201: {"description": "Type de prise créé ou remplacé"},
        403: {"description": "Accès interdit (route sécurisé par JWT)"},
        500: {"description": "Erreur serveur lors de la création"},
    },
)
def create_or_replace_plug_type(
    plug: ElectriciteCreateRequest, _=Depends(Security.secured_route)
):
    try:
        rows = ElectricityService.create_or_replace(plug.model_dump())

        return {
            "message": f"Type de prise '{plug.plug_type}' créé/remplacé avec succès",
            "rows_affected": rows,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}",
        )


@router.patch(
    "/{plug_type}",
    response_model=dict,
    summary="Mise à jour partielle d'un type de prise",
    description="Met à jour uniquement les champs fournis (plug_png, sock_png)",
    responses={
        200: {"description": "Type de prise mis à jour"},
        403: {"description": "Accès interdit (route sécurisé par JWT)"},
        404: {"description": "Type de prise non trouvé"},
        500: {"description": "Erreur serveur"},
    },
)
def update_plug_type_partial(
    plug_type: str, updates: ElectriciteUpdateRequest, _=Depends(Security.secured_route)
):
    try:
        rows = ElectricityService.update_partial(plug_type, updates.model_dump())

        return {
            "message": f"Type de prise '{plug_type}' mis à jour avec succès",
            "rows_affected": rows,
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
    "/{plug_type}",
    response_model=dict,
    summary="Supprimer un type de prise",
    description="Supprime un type de prise par son identifiant",
    responses={
        200: {"description": "Type de prise supprimé"},
        403: {"description": "Accès interdit (route sécurisé par JWT)"},
        404: {"description": "Type de prise non trouvé"},
        500: {"description": "Erreur serveur"},
    },
)
def delete_plug_type(plug_type: str, _=Depends(Security.secured_route)):
    try:
        rows = ElectricityService.delete(plug_type)

        return {
            "message": f"Type de prise '{plug_type}' supprimé avec succès",
            "rows_affected": rows,
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
