from typing import Optional, List
from pydantic import BaseModel
from models.week_meteo import WeekMeteo


class WeekMeteoCreate(WeekMeteo):
    """DTO pour création/enregistrement d'un agrégat (période 14 jours)."""

    pass


class WeekMeteoUpdate(BaseModel):
    """DTO pour mise à jour partielle"""

    temperature_max_avg: Optional[float] = None
    temperature_min_avg: Optional[float] = None
    precipitation_sum: Optional[float] = None


class WeekMeteoResponse(WeekMeteo):
    """DTO de réponse API"""

    class Config:
        from_attributes = True


class WeekMeteoBulkCreate(BaseModel):
    """Payload pour insertions en masse"""

    items: List[WeekMeteoCreate]
