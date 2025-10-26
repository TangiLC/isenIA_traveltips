from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class WeekMeteo(BaseModel):
    geoname_id: int = Field(..., description="Identifiant GeoNames (FK vers Villes)")
    week_start_date: date = Field(
        ..., description="Début de période de 14 jours (YYYY-MM-DD)"
    )
    week_end_date: date = Field(
        ..., description="Fin de période de 14 jours (YYYY-MM-DD)"
    )
    temperature_max_avg: Optional[float] = Field(
        None, description="Moyenne des T° max sur 14 jours"
    )
    temperature_min_avg: Optional[float] = Field(
        None, description="Moyenne des T° min sur 14 jours"
    )
    precipitation_sum: Optional[float] = Field(
        None, description="Somme des précipitations sur 14 jours"
    )

    @classmethod
    def from_dict(cls, data: dict) -> "WeekMeteo":
        return cls(**data)

    def to_dict(self) -> dict:
        return self.model_dump()
