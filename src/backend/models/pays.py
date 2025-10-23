from pydantic import BaseModel, Field
from typing import Optional, List


class Pays(BaseModel):
    iso3166a2: str = Field(..., min_length=2, max_length=2)
    iso3166a3: str = Field(..., min_length=3, max_length=3)
    name_en: str
    name_fr: str
    name_local: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class PaysRelations(BaseModel):
    langues: List[str] = []
    currencies: List[str] = []
    borders: List[str] = []
    electricity_types: List[str] = []
    voltage: Optional[str] = None
    frequency: Optional[str] = None
