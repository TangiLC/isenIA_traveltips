from pydantic import BaseModel, Field
from typing import Optional


class ElectriciteResponse(BaseModel):
    """DTO de réponse pour un type de prise électrique"""

    plug_type: str = Field(
        ..., min_length=1, max_length=1, description="Type de prise (A-N)"
    )
    plug_png: str = Field(..., max_length=10, description="Nom du fichier image plug")
    sock_png: str = Field(..., max_length=10, description="Nom du fichier image socket")


class ElectriciteCreateRequest(BaseModel):
    """DTO pour la création/remplacement d'un type de prise"""

    plug_type: str = Field(
        ..., min_length=1, max_length=1, description="Type de prise (A-N)"
    )
    plug_png: str = Field(..., max_length=10, description="Nom du fichier image plug")
    sock_png: str = Field(..., max_length=10, description="Nom du fichier image socket")


class ElectriciteUpdateRequest(BaseModel):
    """DTO pour la mise à jour partielle d'un type de prise"""

    plug_png: Optional[str] = Field(
        None, max_length=10, description="Nom du fichier image plug"
    )
    sock_png: Optional[str] = Field(
        None, max_length=10, description="Nom du fichier image socket"
    )


def map_to_response(db_row: dict) -> ElectriciteResponse:
    """Map une ligne SQL -> ElectriciteResponse"""
    return ElectriciteResponse(
        plug_type=db_row["plug_type"],
        plug_png=db_row["plug_png"],
        sock_png=db_row["sock_png"],
    )
