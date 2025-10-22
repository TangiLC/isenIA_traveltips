from fastapi import APIRouter, HTTPException, status
from typing import List
from connexion.mysql_connect import MySQLConnection
from repositories.electricity_repository import ElectriciteRepository
from schemas.electricity_dto import (
    ElectriciteResponse,
    ElectriciteCreateRequest,
    ElectriciteUpdateRequest,
    map_to_response,
)

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
        MySQLConnection.connect()
        results = ElectriciteRepository.find_all()
        return [map_to_response(r) for r in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )
    finally:
        MySQLConnection.close()


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
        MySQLConnection.connect()
        result = ElectriciteRepository.find_by_plug_type(plug_type.upper())
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Type de prise '{plug_type}' introuvable",
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


@router.put(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Créer ou remplacer un type de prise",
    description="Insère un nouveau type de prise ou remplace un existant (REPLACE INTO)",
    responses={
        201: {"description": "Type de prise créé ou remplacé"},
        500: {"description": "Erreur serveur lors de la création"},
    },
)
def create_or_replace_plug_type(plug: ElectriciteCreateRequest):
    try:
        MySQLConnection.connect()
        rows = ElectriciteRepository.create_or_replace(
            plug_type=plug.plug_type.upper(),
            plug_png=plug.plug_png,
            sock_png=plug.sock_png,
        )
        MySQLConnection.commit()
        return {
            "message": f"Type de prise '{plug.plug_type}' créé/remplacé avec succès",
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
    "/{plug_type}",
    response_model=dict,
    summary="Mise à jour partielle d'un type de prise",
    description="Met à jour uniquement les champs fournis (plug_png, sock_png)",
    responses={
        200: {"description": "Type de prise mis à jour"},
        404: {"description": "Type de prise non trouvé"},
        500: {"description": "Erreur serveur"},
    },
)
def update_plug_type_partial(plug_type: str, updates: ElectriciteUpdateRequest):
    try:
        MySQLConnection.connect()

        existing = ElectriciteRepository.find_by_plug_type(plug_type.upper())
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Type de prise '{plug_type}' introuvable",
            )

        updates_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
        if not updates_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun champ à mettre à jour",
            )

        rows = ElectriciteRepository.update_partial(plug_type.upper(), updates_dict)
        MySQLConnection.commit()
        return {
            "message": f"Type de prise '{plug_type}' mis à jour avec succès",
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
    "/{plug_type}",
    response_model=dict,
    summary="Supprimer un type de prise",
    description="Supprime un type de prise par son identifiant",
    responses={
        200: {"description": "Type de prise supprimé"},
        404: {"description": "Type de prise non trouvé"},
        500: {"description": "Erreur serveur"},
    },
)
def delete_plug_type(plug_type: str):
    try:
        MySQLConnection.connect()

        existing = ElectriciteRepository.find_by_plug_type(plug_type.upper())
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Type de prise '{plug_type}' introuvable",
            )

        rows = ElectriciteRepository.delete(plug_type.upper())
        MySQLConnection.commit()
        return {
            "message": f"Type de prise '{plug_type}' supprimé avec succès",
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
