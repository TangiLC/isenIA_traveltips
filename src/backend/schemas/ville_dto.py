from pydantic import BaseModel, Field
from typing import Optional
from models.ville import Ville


class VilleCreate(Ville):
    """DTO pour la création d'une ville"""

    pass


class VilleUpdate(BaseModel):
    """DTO pour la mise à jour d'une ville (tous les champs optionnels)"""

    name_en: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country_3166a2: Optional[str] = Field(None, max_length=2)
    is_capital: Optional[bool] = None


class VilleResponse(Ville):
    """DTO pour la réponse API"""

    class Config:
        from_attributes = True
