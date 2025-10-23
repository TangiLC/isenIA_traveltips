from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from schemas.week_meteo_dto import (
    WeekMeteoCreate,
    WeekMeteoUpdate,
    WeekMeteoResponse,
    WeekMeteoBulkCreate,
)
from repositories.week_meteo_repository import WeekMeteoRepository
from models.week_meteo import WeekMeteo
from security.security import Security

router = APIRouter(
    prefix="/api/meteo",
    tags=["Météo - Hebdo"],
)


@router.get(
    "/{geoname_id}",
    response_model=List[WeekMeteoResponse],
    summary="Lister les semaines météo pour une ville",
    description=(
        "Retourne les relevés météo hebdomadaires pour une ville identifiée par son **geoname_id**.\n\n"
        "Vous pouvez restreindre la plage avec `start_date` et/ou `end_date` (inclusives)."
    ),
    responses={
        200: {"description": "Liste des semaines correspondant aux critères."},
        404: {
            "description": "Aucune donnée hebdomadaire trouvée pour les critères fournis."
        },
    },
)
def get_weeks_for_city(
    geoname_id: int,
    start_date: Optional[date] = Query(
        None,
        description="Date de début (incluse) au format ISO, ex: 2025-01-06.",
    ),
    end_date: Optional[date] = Query(
        None,
        description="Date de fin (incluse) au format ISO, ex: 2025-02-03.",
    ),
):
    """
    Récupère les semaines météo pour `geoname_id` dans la plage optionnelle [`start_date`, `end_date`].
    """
    data = WeekMeteoRepository.get_range(geoname_id, start_date, end_date)
    if not data:
        raise HTTPException(status_code=404, detail="Aucune donnée hebdomadaire")
    return data


@router.get(
    "/",
    response_model=List[WeekMeteoResponse],
    summary="Parcourir toutes les semaines météo",
    description="Liste paginée de toutes les semaines météo, tri/ordre définis au niveau dépôt.",
    responses={
        200: {"description": "Page de semaines météo."},
    },
)
def list_all(
    skip: int = Query(
        0,
        ge=0,
        description="Décalage de pagination (nombre d'éléments à ignorer).",
        examples={"default": {"summary": "Début de liste", "value": 0}},
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Taille de page (1 à 1000).",
    ),
):
    """
    Retourne une page des semaines météo disponibles.
    """
    return WeekMeteoRepository.get_all(skip, limit)


@router.post(
    "/",
    response_model=WeekMeteoResponse,
    status_code=201,
    summary="Créer ou mettre à jour une semaine",
    description=(
        "Crée ou met à jour (upsert) un enregistrement de semaine météo. "
        "Nécessite une route sécurisée."
    ),
    responses={
        201: {"description": "Semaine créée ou mise à jour."},
        401: {"description": "Authentification requise ou invalide."},
        422: {"description": "Corps de requête invalide."},
    },
)
def create_or_update_week(
    payload: WeekMeteoCreate = Body(
        ...,
        description="Données de la semaine météo à créer/mettre à jour.",
    ),
    _=Depends(Security.secured_route),
):
    """
    Upsert d'une semaine météo à partir du schéma `WeekMeteoCreate`.
    """
    created = WeekMeteoRepository.upsert(WeekMeteo(**payload.model_dump()))
    return created


@router.post(
    "/bulk",
    status_code=201,
    summary="Créations/Mises à jour en masse",
    description=(
        "Crée ou met à jour plusieurs semaines en une seule requête. "
        "Retourne le nombre de lignes upsertées. Route sécurisée."
    ),
    responses={
        201: {"description": "Opération terminée, nombre de lignes upsertées renvoyé."},
        401: {"description": "Authentification requise ou invalide."},
        422: {"description": "Corps de requête invalide."},
    },
)
def bulk_create_or_update(
    payload: WeekMeteoBulkCreate = Body(
        ...,
        description="Collection d'éléments conformes au schéma `WeekMeteoCreate`.",
    ),
    _=Depends(Security.secured_route),
):
    """
    Upsert en masse de semaines météo. Retourne `{"upserted_rows": <int>}`.
    """
    items = [WeekMeteo(**p.model_dump()) for p in payload.items]
    inserted = WeekMeteoRepository.bulk_upsert(items)
    return {"upserted_rows": inserted}


@router.put(
    "/{geoname_id}/{week_start_date}",
    response_model=WeekMeteoResponse,
    summary="Mettre à jour une semaine existante",
    description=(
        "Applique des modifications partielles sur une semaine identifiée par la clé composite "
        "`geoname_id` + `week_start_date`. Route sécurisée."
    ),
    responses={
        200: {"description": "Semaine mise à jour."},
        401: {"description": "Authentification requise ou invalide."},
        404: {"description": "Semaine non trouvée."},
        422: {"description": "Paramètres ou corps de requête invalides."},
    },
)
def update_one(
    geoname_id: int,
    week_start_date: date,
    changes: WeekMeteoUpdate = Body(
        ...,
        description="Champs à modifier (seuls les champs fournis sont pris en compte).",
        examples={
            "patch": {
                "summary": "Modifier précipitations et ensoleillement",
                "value": {"precip_mm": 12.0, "sun_hours": 25.0},
            }
        },
    ),
    _=Depends(Security.secured_route),
):
    """
    Met à jour une semaine existante en conservant les valeurs non spécifiées.
    """
    existing = WeekMeteoRepository.get_by_pk(geoname_id, week_start_date)
    if existing is None:
        raise HTTPException(status_code=404, detail="Semaine non trouvée")
    data = existing.model_dump()
    for k, v in changes.model_dump(exclude_unset=True).items():
        data[k] = v
    updated = WeekMeteoRepository.upsert(WeekMeteo(**data))
    return updated


@router.delete(
    "/{geoname_id}/{week_start_date}",
    status_code=204,
    summary="Supprimer une semaine",
    description="Supprime la semaine identifiée par `geoname_id` et `week_start_date`. Route sécurisée.",
    responses={
        204: {"description": "Semaine supprimée."},
        401: {"description": "Authentification requise ou invalide."},
        404: {"description": "Semaine non trouvée."},
    },
)
def delete_one(
    geoname_id: int,
    week_start_date: date,
    _=Depends(Security.secured_route),
):
    """
    Supprime définitivement la semaine ciblée si elle existe.
    """
    ok = WeekMeteoRepository.delete(geoname_id, week_start_date)
    if not ok:
        raise HTTPException(status_code=404, detail="Semaine non trouvée")
