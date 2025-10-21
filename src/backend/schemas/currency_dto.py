from pydantic import BaseModel, Field
from typing import Optional, List


class CurrencyResponse(BaseModel):
    """DTO de réponse pour une devise"""

    iso4217: str = Field(..., min_length=3, max_length=3, description="Code ISO 4217")
    name: str = Field(..., description="Nom de la devise")
    symbol: str = Field(..., description="Symbole monétaire")


class CurrencyCreateRequest(BaseModel):
    """DTO pour la création/remplacement d'une devise"""

    iso4217: str = Field(..., min_length=3, max_length=3, description="Code ISO 4217")
    name: str = Field(..., description="Nom de la devise")
    symbol: str = Field(..., description="Symbole monétaire")


class CurrencyUpdateRequest(BaseModel):
    """DTO pour la mise à jour partielle d'une devise"""

    name: Optional[str] = Field(None, description="Nom de la devise")
    symbol: Optional[str] = Field(None, description="Symbole monétaire")


def map_to_response(db_row: dict) -> CurrencyResponse:
    """Map une ligne SQL -> CurrencyResponse"""
    return CurrencyResponse(
        iso4217=db_row["iso4217"],
        name=db_row["name"],
        symbol=db_row["symbol"],
    )
