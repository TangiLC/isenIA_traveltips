from pydantic import BaseModel, Field
from typing import Optional


class FamilleDTO(BaseModel):
    """DTO pour les informations de famille linguistique"""

    branche_en: str = Field(..., description="Nom de la famille en anglais")
    branche_fr: str = Field(..., description="Nom de la famille en français")


class LangueResponse(BaseModel):
    """DTO de réponse pour une langue avec sa famille"""

    iso639_2: str = Field(..., min_length=3, max_length=3, description="Code ISO 639-2")
    name_en: str = Field(..., description="Nom de la langue en anglais")
    name_fr: str = Field(..., description="Nom de la langue en français")
    name_local: str = Field(..., description="Nom de la langue locale")
    famille: Optional[FamilleDTO] = Field(None, description="Famille linguistique")


class LangueCreateRequest(BaseModel):
    """DTO pour la création/remplacement d'une langue"""

    iso639_2: str = Field(..., min_length=3, max_length=3, description="Code ISO 639-2")
    name_en: str = Field(..., description="Nom de la langue en anglais")
    name_fr: str = Field(..., description="Nom de la langue en français")
    name_local: str = Field(..., description="Nom de la langue locale")
    branche_en: Optional[str] = Field(None, description="Nom de la famille en anglais")


class LangueUpdateRequest(BaseModel):
    """DTO pour la mise à jour partielle d'une langue"""

    name_en: Optional[str] = Field(None, description="Nom de la langue en anglais")
    name_fr: Optional[str] = Field(None, description="Nom de la langue en français")
    name_local: Optional[str] = Field(None, description="Nom de la langue locale")
    branche_en: Optional[str] = Field(None, description="Nom de la famille en anglais")


def map_to_response(db_row: dict) -> LangueResponse:
    """Convertit une ligne de base de données en LangueResponse\n
    Args:\n
        db_row: Dictionnaire représentant une ligne de la base\n
    Returns:
        Instance de LangueResponse
    """
    famille = None
    if db_row.get("branche_en") and db_row.get("branche_fr"):
        famille = FamilleDTO(
            branche_en=db_row["branche_en"], branche_fr=db_row["branche_fr"]
        )

    return LangueResponse(
        iso639_2=db_row["iso639_2"],
        name_en=db_row["name_en"],
        name_fr=db_row["name_fr"],
        name_local=db_row["name_local"],
        famille=famille,
    )
