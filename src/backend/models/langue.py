from pydantic import BaseModel, Field
from typing import Optional


class Famille(BaseModel):
    """Modèle pour une famille de langues"""

    branche: str


class Langue(BaseModel):
    """Modèle pour une langue ISO 639"""

    iso639_2: str = Field(..., min_length=3, max_length=3)
    name_en: str
    name_fr: str
    name_local: str
    famille: Optional[Famille] = None
