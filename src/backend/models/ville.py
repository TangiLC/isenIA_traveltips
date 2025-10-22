from pydantic import BaseModel, Field
from typing import Optional


class Ville(BaseModel):
    geoname_id: int = Field(..., description="Identifiant unique GeoNames")
    name_en: str = Field(..., max_length=100, description="Nom de la ville en anglais")
    latitude: Optional[float] = Field(None, description="Latitude WGS84")
    longitude: Optional[float] = Field(None, description="Longitude WGS84")
    country_3166a2: Optional[str] = Field(
        None, max_length=2, description="Code pays ISO 3166-1 alpha-2"
    )
    is_capital: bool = Field(..., description="Cette ville est la capitale du pays")

    @classmethod
    def from_dict(cls, data: dict) -> "Ville":
        """Crée une instance Ville depuis un dictionnaire"""
        return cls(**data)

    def to_dict(self) -> dict:
        """Convertit l'instance en dictionnaire"""
        return self.model_dump()
