from fastapi import APIRouter, HTTPException, status, Query
from typing import List
from connexion.mysql_connect import MySQLConnection
from repositories.langue_repository import LangueRepository
from schemas.langue_dto import (
    LangueResponse,
    LangueCreateRequest,
    LangueUpdateRequest,
    map_to_response,
)


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
        MySQLConnection.connect()
        result = LangueRepository.find_by_iso639_2(code)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Langue avec le code '{code}' introuvable",
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
        MySQLConnection.connect()
        results = LangueRepository.find_by_name(name)
        return [map_to_response(row) for row in results]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )
    finally:
        MySQLConnection.close()


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
        MySQLConnection.connect()
        results = LangueRepository.find_by_famille(famille)
        return [map_to_response(row) for row in results]

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
    summary="Créer ou remplacer une langue",
    description="Insère une nouvelle langue ou remplace une existante (REPLACE INTO)",
    responses={
        201: {"description": "Langue créée ou remplacée"},
        500: {"description": "Erreur serveur lors de la création"},
    },
)
def create_or_replace_langue(langue: LangueCreateRequest):
    """Crée ou remplace une langue"""
    try:
        MySQLConnection.connect()

        rows_affected = LangueRepository.create_or_replace(
            iso639_2=langue.iso639_2,
            name_en=langue.name_en,
            name_fr=langue.name_fr,
            name_local=langue.name_local,
            branche_en=langue.branche_en,
        )

        MySQLConnection.commit()

        return {
            "message": f"Langue '{langue.iso639_2}' créée/remplacée avec succès",
            "rows_affected": rows_affected,
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
def update_langue_partial(iso639_2: str, updates: LangueUpdateRequest):
    """Mise à jour partielle d'une langue"""
    try:
        MySQLConnection.connect()

        # Vérifier que la langue existe
        existing = LangueRepository.find_by_iso639_2(iso639_2)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Langue avec le code '{iso639_2}' introuvable",
            )

        # Filtrer les champs non-None
        updates_dict = {k: v for k, v in updates.model_dump().items() if v is not None}

        if not updates_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun champ à mettre à jour",
            )

        rows_affected = LangueRepository.update_partial(iso639_2, updates_dict)
        MySQLConnection.commit()

        return {
            "message": f"Langue '{iso639_2}' mise à jour avec succès",
            "rows_affected": rows_affected,
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
    "/{iso639_2}",
    response_model=dict,
    summary="Supprimer une langue",
    description="Supprime une langue par son code ISO 639-2",
    responses={
        200: {"description": "Langue supprimée"},
        404: {"description": "Langue non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def delete_langue(iso639_2: str):
    """Supprime une langue par son code ISO 639-2"""
    try:
        MySQLConnection.connect()

        # Vérifier que la langue existe
        existing = LangueRepository.find_by_iso639_2(iso639_2)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Langue avec le code '{iso639_2}' introuvable",
            )

        rows_affected = LangueRepository.delete(iso639_2)
        MySQLConnection.commit()

        return {
            "message": f"Langue '{iso639_2}' supprimée avec succès",
            "rows_affected": rows_affected,
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
