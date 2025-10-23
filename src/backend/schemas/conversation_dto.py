from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from bson import ObjectId


class PyObjectId(str):
    """Classe personnalisée pour gérer les ObjectId MongoDB avec Pydantic"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("ObjectId invalide")
        return str(v)


class ConversationResponse(BaseModel):
    """DTO de réponse pour une conversation"""

    id: str = Field(alias="_id", description="Identifiant MongoDB")
    lang639_2: str = Field(
        alias="lang639-2",
        min_length=3,
        max_length=3,
        description="Code langue ISO 639-2",
    )
    sentences: Optional[Dict[str, str]] = Field(
        None, description="Phrases clé-valeur (ex: GREETING_INFORMAL: 'Hello')"
    )

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @classmethod
    def from_mongo(cls, doc: dict) -> "ConversationResponse":
        """Convertit un document MongoDB en ConversationResponse"""
        if not doc:
            return None

        base_fields = {"_id": str(doc["_id"]), "lang639-2": doc.get("lang639-2", "")}

        sentences = doc.get("sentences", {})

        response = cls(**base_fields)
        response.sentences = sentences if sentences else None
        return response


class ConversationCreateRequest(BaseModel):
    """DTO pour la création d'une conversation"""

    lang639_2: str = Field(
        alias="lang639-2",
        min_length=3,
        max_length=3,
        description="Code langue ISO 639-2 (ex: 'fra', 'eng')",
    )

    sentences: Optional[Dict[str, str]] = Field(
        None,
        description="Dictionnaire de phrases (ex: {'GREETING_INFORMAL': 'Hello'})",
    )

    @field_validator("lang639_2")
    @classmethod
    def validate_lang_code(cls, v: str) -> str:
        """Valide que le code est bien en 3 lettres minuscules"""
        if not v.isalpha():
            raise ValueError("Le code langue doit contenir uniquement des lettres")
        return v.lower()

    class Config:
        populate_by_name = True

    def to_mongo(self) -> dict:
        """Convertit le DTO en document MongoDB"""
        doc = {"lang639-2": self.lang639_2.lower()}

        if self.sentences:
            doc["sentences"] = self.sentences

        return doc


class ConversationUpdateRequest(BaseModel):
    """DTO pour la mise à jour d'une conversation"""

    lang639_2: Optional[str] = Field(
        None,
        alias="lang639-2",
        min_length=3,
        max_length=3,
        description="Code langue ISO 639-2",
    )

    sentences: Optional[Dict[str, str]] = Field(
        None, description="Dictionnaire de phrases à mettre à jour"
    )

    @field_validator("lang639_2")
    @classmethod
    def validate_lang_code(cls, v: Optional[str]) -> Optional[str]:
        """Valide que le code est bien en 3 lettres minuscules"""
        if v is not None:
            if not v.isalpha():
                raise ValueError("Le code langue doit contenir uniquement des lettres")
            return v.lower()
        return v

    class Config:
        populate_by_name = True

    def to_mongo_update(self) -> dict:
        """Convertit le DTO en opération $set MongoDB"""
        updates = {}

        if self.lang639_2 is not None:
            updates["lang639-2"] = self.lang639_2.lower()

        if self.sentences is not None:
            updates["sentences"] = self.sentences

        return {"$set": updates} if updates else {}


class ConversationListResponse(BaseModel):
    """DTO pour une liste de conversations"""

    total: int = Field(description="Nombre total de conversations")
    conversations: list[ConversationResponse] = Field(
        description="Liste des conversations"
    )


class ConversationBulkCreateRequest(BaseModel):
    """DTO pour l'import en masse de conversations (ETL)"""

    conversations: List[ConversationCreateRequest] = Field(
        ..., description="Liste de conversations à importer"
    )
