from pydantic import BaseModel, Field
from typing import Optional


class Monnaie(BaseModel):
    """Modèle pour une monnaie ISO 4217"""

    iso4217: str = Field(..., min_length=3, max_length=3)
    name: str
    symbol: str
