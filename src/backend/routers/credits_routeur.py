# credits_routeur.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
from connexion.mysql_connect import MySQLConnection

router = APIRouter(prefix="/api/credits", tags=["Credits"])


class CreditOut(BaseModel):
    target_element: str
    source_element: str
    source_type: str
    source_url: str


class CreditsResponse(BaseModel):
    credits: List[CreditOut]


@router.get(
    "",
    response_model=CreditsResponse,
    summary="Récupérer tous les crédits",
    description="Récupération de toutes les sources de données utilisées dans l'application",
    responses={
        200: {"description": "Liste des crédits", "model": CreditsResponse},
        500: {"description": "Erreur interne du serveur"},
    },
)
def get_all_credits():
    """
    Retourne la liste complète des crédits (sources de données)
    """
    try:
        query = """
            SELECT target_element, source_element, source_type, source_url 
            FROM Credits
            ORDER BY target_element
        """
        rows = MySQLConnection.execute_query(query)

        credits_list = [
            CreditOut(
                target_element=row["target_element"],
                source_element=row["source_element"],
                source_type=row["source_type"],
                source_url=row["source_url"],
            )
            for row in rows
        ]

        return CreditsResponse(credits=credits_list)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des crédits: {str(e)}",
        )
