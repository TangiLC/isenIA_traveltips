from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.ville_dto import VilleCreate, VilleUpdate, VilleResponse
from repositories.ville_repository import VilleRepository
from security.security import Security

router = APIRouter(prefix="/api/villes", tags=["Villes"])


@router.get(
    "/{geoname_id}",
    response_model=VilleResponse,
    summary="Récupère les villes par nom",
    description="Récupère des informations villes selon le geoname-id",
    responses={
        200: {"description": "Ville récupérée avec succès"},
        404: {"description": "Aucune ville trouvée"},
        422: {"description": "Format des données incompatible"},
        500: {"description": "Erreur serveur"},
    },
)
def get_ville(geoname_id: int):
    ville = VilleRepository.get_by_geoname_id(geoname_id)
    if ville is None:
        raise HTTPException(status_code=404, detail="Ville non trouvée")
    return ville


@router.get(
    "/by_name/{name_en}",
    response_model=List[VilleResponse],
    summary="Récupère les villes par nom",
    description="Récupère des informations villes selon le nom",
    responses={
        200: {"description": "Ville récupérée avec succès"},
        404: {"description": "Aucune ville trouvée"},
        422: {"description": "Format des données incompatible"},
        500: {"description": "Erreur serveur"},
    },
)
def get_villes_by_name(name_en: str):
    villes = VilleRepository.get_by_name(name_en)
    if not villes:
        raise HTTPException(status_code=404, detail="Aucune ville trouvée avec ce nom")
    return villes


@router.get(
    "/by_country/{country_3166a2}",
    response_model=List[VilleResponse],
    summary="Récupère toutes les villes d'un pays",
    description="Lister toutes les villes de la base (pagination)",
    responses={
        200: {"description": "Liste récupérée avec succès"},
        400: {"description": "Le code pays doit être iso-alpha2"},
        422: {"description": "Format des données incompatible"},
        500: {"description": "Erreur serveur"},
    },
)
def get_villes_by_country(country_3166a2: str):
    if len(country_3166a2) != 2:
        raise HTTPException(
            status_code=400, detail="Le code pays doit contenir exactement 2 caractères"
        )

    villes = VilleRepository.get_by_country(country_3166a2)
    if not villes:
        raise HTTPException(status_code=404, detail="Aucune ville trouvée pour ce pays")
    return villes


@router.get(
    "/",
    response_model=List[VilleResponse],
    summary="Lister toutes les villes",
    description="Lister toutes les villes de la base (pagination)",
    responses={
        200: {"description": "Liste récupérée avec succès"},
        422: {"description": "Format des données incompatible"},
        500: {"description": "Erreur serveur"},
    },
)
def get_villes(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
    villes = VilleRepository.get_all(skip, limit)
    return villes


@router.post(
    "/",
    response_model=VilleResponse,
    summary="Ajouter une ville",
    description="Ajouter une nouvelle ville",
    responses={
        200: {"description": "Ville ajoutée avec succès"},
        400: {"description": "Une ville existe déjà avec ce geoname-id"},
        403: {"description": "Accès interdit (route sécurisée par JWT)"},
        422: {"description": "Format des données incompatible"},
        500: {"description": "Erreur serveur"},
    },
)
def create_ville(ville: VilleCreate, _=Depends(Security.secured_route)):
    existing = VilleRepository.get_by_geoname_id(ville.geoname_id)
    if existing:
        raise HTTPException(
            status_code=400, detail="Une ville avec ce geoname_id existe déjà"
        )

    created = VilleRepository.create(ville.model_dump())
    return created


@router.put(
    "/{geoname_id}",
    response_model=VilleResponse,
    summary="Modifier une ville",
    description="Modifier les données d'une ville existante",
    responses={
        201: {"description": "Ville modifiée"},
        403: {"description": "Accès interdit (route sécurisée par JWT)"},
        404: {"description": "Ville non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def update_ville(
    geoname_id: int, ville: VilleUpdate, _=Depends(Security.secured_route)
):
    update_data = ville.model_dump(exclude_unset=True)
    updated = VilleRepository.update(geoname_id, update_data)

    if updated is None:
        raise HTTPException(status_code=404, detail="Ville non trouvée")
    return updated


@router.delete(
    "/{geoname_id}",
    response_model=str,
    summary="Supprimer une ville",
    description="Supprime une ville par son code geoname-id",
    responses={
        200: {"description": "Langue supprimée"},
        403: {"description": "Accès interdit (route sécurisée par JWT)"},
        404: {"description": "Langue non trouvée"},
        500: {"description": "Erreur serveur"},
    },
)
def delete_ville(geoname_id: int, _=Depends(Security.secured_route)):
    success = VilleRepository.delete(geoname_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ville non trouvée")
    return f"Ville '{geoname_id}' supprimée avec succès"
