from fastapi import APIRouter, HTTPException, status, Query
from typing import List
from connexion.mysql_connect import MySQLConnection
from repository.currency_repository import CurrencyRepository
from schemas.currency_dto import (
    CurrencyResponse,
    CurrencyCreateRequest,
    CurrencyUpdateRequest,
    map_to_response,
)

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
        MySQLConnection.connect()
        result = CurrencyRepository.find_by_iso4217(code)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devise avec le code '{code}' introuvable",
            )
        return map_to_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )
    finally:
        MySQLConnection.close()


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
        MySQLConnection.connect()
        results = CurrencyRepository.find_by_name_or_symbol(name)
        return [map_to_response(r) for r in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )
    finally:
        MySQLConnection.close()


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
def create_or_replace_currency(currency: CurrencyCreateRequest):
    try:
        MySQLConnection.connect()
        rows = CurrencyRepository.create_or_replace(
            iso4217=currency.iso4217,
            name=currency.name,
            symbol=currency.symbol,
        )
        MySQLConnection.commit()
        return {
            "message": f"Devise '{currency.iso4217}' créée/remplacée avec succès",
            "rows_affected": rows,
        }
    except Exception as e:
        MySQLConnection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}",
        )
    finally:
        MySQLConnection.close()


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
def update_currency_partial(iso4217: str, updates: CurrencyUpdateRequest):
    try:
        MySQLConnection.connect()

        existing = CurrencyRepository.find_by_iso4217(iso4217)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devise avec le code '{iso4217}' introuvable",
            )

        updates_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
        if not updates_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun champ à mettre à jour",
            )

        rows = CurrencyRepository.update_partial(iso4217, updates_dict)
        MySQLConnection.commit()
        return {
            "message": f"Devise '{iso4217}' mise à jour avec succès",
            "rows_affected": rows,
        }
    except HTTPException:
        raise
    except Exception as e:
        MySQLConnection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}",
        )
    finally:
        MySQLConnection.close()


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
def delete_currency(iso4217: str):
    try:
        MySQLConnection.connect()

        existing = CurrencyRepository.find_by_iso4217(iso4217)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Devise avec le code '{iso4217}' introuvable",
            )

        rows = CurrencyRepository.delete(iso4217)
        MySQLConnection.commit()
        return {
            "message": f"Devise '{iso4217}' supprimée avec succès",
            "rows_affected": rows,
        }
    except HTTPException:
        raise
    except Exception as e:
        MySQLConnection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}",
        )
    finally:
        MySQLConnection.close()
