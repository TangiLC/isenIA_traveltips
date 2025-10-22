from typing import List
from fastapi import APIRouter, HTTPException, Query
from schemas.ville_dto import VilleCreate, VilleUpdate, VilleResponse
from repositories.ville_repository import VilleRepository

router = APIRouter(prefix="/api/villes", tags=["Villes"])


@router.get("/{geoname_id}", response_model=VilleResponse)
def get_ville(geoname_id: int):
    """Récupère une ville par son geoname_id"""
    ville = VilleRepository.get_by_geoname_id(geoname_id)
    if ville is None:
        raise HTTPException(status_code=404, detail="Ville non trouvée")
    return ville


@router.get("/by_name/{name_en}", response_model=List[VilleResponse])
def get_villes_by_name(name_en: str):
    """Récupère les villes par nom"""
    villes = VilleRepository.get_by_name(name_en)
    if not villes:
        raise HTTPException(status_code=404, detail="Aucune ville trouvée avec ce nom")
    return villes


@router.get("/by_country/{country_3166a2}", response_model=List[VilleResponse])
def get_villes_by_country(country_3166a2: str):
    """Récupère toutes les villes d'un pays"""
    if len(country_3166a2) != 2:
        raise HTTPException(
            status_code=400, detail="Le code pays doit contenir exactement 2 caractères"
        )

    villes = VilleRepository.get_by_country(country_3166a2)
    if not villes:
        raise HTTPException(status_code=404, detail="Aucune ville trouvée pour ce pays")
    return villes


@router.get("/", response_model=List[VilleResponse])
def get_villes(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
    """Récupère toutes les villes avec pagination"""
    villes = VilleRepository.get_all(skip, limit)
    return villes


@router.post("/", response_model=VilleResponse, status_code=201)
def create_ville(ville: VilleCreate):
    """Crée une nouvelle ville"""
    existing = VilleRepository.get_by_geoname_id(ville.geoname_id)
    if existing:
        raise HTTPException(
            status_code=400, detail="Une ville avec ce geoname_id existe déjà"
        )

    created = VilleRepository.create(ville.model_dump())
    return created


@router.put("/{geoname_id}", response_model=VilleResponse)
def update_ville(geoname_id: int, ville: VilleUpdate):
    """Met à jour une ville existante"""
    update_data = ville.model_dump(exclude_unset=True)
    updated = VilleRepository.update(geoname_id, update_data)

    if updated is None:
        raise HTTPException(status_code=404, detail="Ville non trouvée")
    return updated


@router.delete("/{geoname_id}", status_code=204)
def delete_ville(geoname_id: int):
    """Supprime une ville"""
    success = VilleRepository.delete(geoname_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ville non trouvée")
