from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from services.currency_service import CurrencyService
from schemas.currency_dto import (
    CurrencyResponse,
    CurrencyCreateRequest,
    CurrencyUpdateRequest,
    map_to_response,
)
from security.security import Security

router = APIRouter(prefix="/api/monnaies", tags=["Monnaies"])


@router.get(
    "/by_code_iso",
    response_model=CurrencyResponse,
    summary="Rechercher une devise par code ISO 4217",
    description="Retourne une devise correspondant au code ISO 4217 fourni",
    responses={
        200: {"description": "Devise trouvée"},
        404: {"description": "Devise non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def get_currency_by_code_iso(
    code: str = Query(..., min_length=3, max_length=3, description="Code ISO 4217"),
):
    try:
        result = CurrencyService.find_by_iso4217(code)
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
    response_model=List[CurrencyResponse],
    summary="Rechercher des devises par nom, symbole ou code",
    description="Recherche dans name, symbol et iso4217 (insensible à la casse)",
    responses={
        200: {"description": "Liste des devises correspondantes"},
        500: {"description": "Erreur serveur"},
    },
)
def get_currencies_by_name(
    name: str = Query(..., min_length=1, description="Terme de recherche"),
):
    try:
        results = CurrencyService.find_by_name_or_symbol(name)
        return [map_to_response(r) for r in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )


@router.put(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Créer ou remplacer une devise",
    description="Insère une nouvelle devise ou remplace une existante (REPLACE INTO)",
    responses={
        201: {"description": "Devise créée ou remplacée"},
        500: {"description": "Erreur serveur lors de la création"},
    },
)
def create_or_replace_currency(
    currency: CurrencyCreateRequest, _=Depends(Security.secured_route)
):
    try:
        rows = CurrencyService.create_or_replace(currency.model_dump())

        return {
            "message": f"Devise '{currency.iso4217}' créée/remplacée avec succès",
            "rows_affected": rows,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}",
        )


@router.patch(
    "/{iso4217}",
    response_model=dict,
    summary="Mise à jour partielle d'une devise",
    description="Met à jour uniquement les champs fournis (name, symbol)",
    responses={
        200: {"description": "Devise mise à jour"},
        404: {"description": "Devise non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def update_currency_partial(
    iso4217: str, updates: CurrencyUpdateRequest, _=Depends(Security.secured_route)
):
    try:
        rows = CurrencyService.update_partial(iso4217, updates.model_dump())

        return {
            "message": f"Devise '{iso4217}' mise à jour avec succès",
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
    "/{iso4217}",
    response_model=dict,
    summary="Supprimer une devise",
    description="Supprime une devise par son code ISO 4217",
    responses={
        200: {"description": "Devise supprimée"},
        404: {"description": "Devise non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def delete_currency(iso4217: str, _=Depends(Security.secured_route)):
    try:
        rows = CurrencyService.delete(iso4217)

        return {
            "message": f"Devise '{iso4217}' supprimée avec succès",
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
