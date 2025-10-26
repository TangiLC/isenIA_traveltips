from pydantic import BaseModel, Field


class Electricite(BaseModel):
    """Modèle pour un type de prise électrique"""

    plug_type: str = Field(..., min_length=1, max_length=1)
    plug_png: str = Field(..., max_length=10)
    sock_png: str = Field(..., max_length=10)
