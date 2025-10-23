from pydantic import BaseModel, Field
from typing import List, Optional


class BorderCountry(BaseModel):
    """Représentation simplifiée d'un pays frontalier (évite la récursivité)"""

    iso3166a2: str
    name_en: str
    name_fr: str
    name_local: str


class CountryResponse(BaseModel):
    """Réponse complète avec toutes les relations"""

    iso3166a2: str = Field(..., min_length=2, max_length=2)
    iso3166a3: str = Field(..., min_length=3, max_length=3)
    name_en: str
    name_fr: str
    name_local: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    langues: List[str] = []
    currencies: List[str] = []
    borders: List[BorderCountry] = []
    electricity_types: List[str] = []
    voltage: Optional[str] = None
    frequency: Optional[str] = None


class CountryCreate(BaseModel):
    """Création d'un pays avec ses relations"""

    iso3166a2: str = Field(..., min_length=2, max_length=2)
    iso3166a3: str = Field(..., min_length=3, max_length=3)
    name_en: str = Field(..., min_length=1)
    name_fr: str = Field(..., min_length=1)
    name_local: str = Field(..., min_length=1)
    lat: Optional[float] = None
    lng: Optional[float] = None
    langues: List[str] = []
    currencies: List[str] = []
    borders: List[str] = []
    electricity_types: List[str] = []
    voltage: Optional[str] = None
    frequency: Optional[str] = None


class CountryUpdate(BaseModel):
    """Mise à jour partielle d'un pays"""

    iso3166a3: Optional[str] = Field(None, min_length=3, max_length=3)
    name_en: Optional[str] = None
    name_fr: Optional[str] = None
    name_local: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    langues: Optional[List[str]] = None
    currencies: Optional[List[str]] = None
    borders: Optional[List[str]] = None
    electricity_types: Optional[List[str]] = None
    voltage: Optional[str] = None
    frequency: Optional[str] = None
