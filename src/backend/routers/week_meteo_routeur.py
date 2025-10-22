from datetime import date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from schemas.week_meteo_dto import (
    WeekMeteoCreate,
    WeekMeteoUpdate,
    WeekMeteoResponse,
    WeekMeteoBulkCreate,
)
from repositories.week_meteo_repository import WeekMeteoRepository
from models.week_meteo import WeekMeteo

router = APIRouter(prefix="/api/meteo/weekly", tags=["Météo - Hebdo"])


@router.get("/{geoname_id}", response_model=List[WeekMeteoResponse])
def get_weeks_for_city(
    geoname_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    data = WeekMeteoRepository.get_range(geoname_id, start_date, end_date)
    if not data:
        raise HTTPException(status_code=404, detail="Aucune donnée hebdomadaire")
    return data


@router.get("/", response_model=List[WeekMeteoResponse])
def list_all(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
    return WeekMeteoRepository.get_all(skip, limit)


@router.post("/", response_model=WeekMeteoResponse, status_code=201)
def create_or_update_week(payload: WeekMeteoCreate):
    created = WeekMeteoRepository.upsert(WeekMeteo(**payload.model_dump()))
    return created


@router.post("/bulk", status_code=201)
def bulk_create_or_update(payload: WeekMeteoBulkCreate):
    items = [WeekMeteo(**p.model_dump()) for p in payload.items]
    inserted = WeekMeteoRepository.bulk_upsert(items)
    return {"upserted_rows": inserted}


@router.put("/{geoname_id}/{week_start_date}", response_model=WeekMeteoResponse)
def update_one(geoname_id: int, week_start_date: date, changes: WeekMeteoUpdate):
    existing = WeekMeteoRepository.get_by_pk(geoname_id, week_start_date)
    if existing is None:
        raise HTTPException(status_code=404, detail="Semaine non trouvée")
    data = existing.model_dump()
    for k, v in changes.model_dump(exclude_unset=True).items():
        data[k] = v
    updated = WeekMeteoRepository.upsert(WeekMeteo(**data))
    return updated


@router.delete("/{geoname_id}/{week_start_date}", status_code=204)
def delete_one(geoname_id: int, week_start_date: date):
    ok = WeekMeteoRepository.delete(geoname_id, week_start_date)
    if not ok:
        raise HTTPException(status_code=404, detail="Semaine non trouvée")
