# app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ================================================================
# GRUPO 1 — DTOs que espelham exatamente o JSON da API externa
# Os alias= tratam as chaves com hífen (full-name, eye-color, etc.)
# ================================================================

class PowerstatsDTO(BaseModel):
    intelligence: Optional[str] = None
    strength:     Optional[str] = None
    speed:        Optional[str] = None
    durability:   Optional[str] = None
    power:        Optional[str] = None
    combat:       Optional[str] = None


class BiographyDTO(BaseModel):
    full_name:        Optional[str] = Field(None, alias="full-name")
    alter_egos:       Optional[str] = Field(None, alias="alter-egos")
    aliases:          Optional[List[str]] = []
    place_of_birth:   Optional[str] = Field(None, alias="place-of-birth")
    first_appearance: Optional[str] = Field(None, alias="first-appearance")
    publisher:        Optional[str] = None
    alignment:        Optional[str] = None

    class Config:
        populate_by_name = True


class AppearanceDTO(BaseModel):
    gender:     Optional[str] = None
    race:       Optional[str] = None
    height:     Optional[List[str]] = []
    weight:     Optional[List[str]] = []
    eye_color:  Optional[str] = Field(None, alias="eye-color")
    hair_color: Optional[str] = Field(None, alias="hair-color")

    class Config:
        populate_by_name = True


class WorkDTO(BaseModel):
    occupation: Optional[str] = None
    base:       Optional[str] = None


class ConnectionsDTO(BaseModel):
    group_affiliation: Optional[str] = Field(None, alias="group-affiliation")
    relatives:         Optional[str] = None

    class Config:
        populate_by_name = True


class ImageDTO(BaseModel):
    url: Optional[str] = None


class SuperheroExternalDTO(BaseModel):
    """Representa um herói no array results[] da API externa."""
    id:          str
    name:        str
    powerstats:  Optional[PowerstatsDTO]  = None
    biography:   Optional[BiographyDTO]   = None
    appearance:  Optional[AppearanceDTO]  = None
    work:        Optional[WorkDTO]        = None
    connections: Optional[ConnectionsDTO] = None
    image:       Optional[ImageDTO]       = None


class SuperheroAPIResponseDTO(BaseModel):
    """Envelope completo da resposta da API externa."""
    response:    str
    results_for: Optional[str] = Field(None, alias="results-for")
    results:     Optional[List[SuperheroExternalDTO]] = []

    class Config:
        populate_by_name = True


# ================================================================
# GRUPO 2 — Schemas de entrada para o CRUD manual
# ================================================================

class PowerstatsInput(BaseModel):
    intelligence: Optional[int] = Field(None, ge=0, le=100)
    strength:     Optional[int] = Field(None, ge=0, le=100)
    speed:        Optional[int] = Field(None, ge=0, le=100)
    durability:   Optional[int] = Field(None, ge=0, le=100)
    power:        Optional[int] = Field(None, ge=0, le=100)
    combat:       Optional[int] = Field(None, ge=0, le=100)


class BiographyInput(BaseModel):
    full_name:        Optional[str] = None
    alter_egos:       Optional[str] = None
    aliases:          Optional[List[str]] = []
    place_of_birth:   Optional[str] = None
    first_appearance: Optional[str] = None
    publisher:        Optional[str] = None
    alignment:        Optional[str] = None


class AppearanceInput(BaseModel):
    gender:    Optional[str] = None
    race:      Optional[str] = None
    eye_color: Optional[str] = None
    hair_color: Optional[str] = None
    heights:   Optional[List[str]] = []
    weights:   Optional[List[str]] = []


class WorkInput(BaseModel):
    occupation: Optional[str] = None
    base:       Optional[str] = None


class ConnectionsInput(BaseModel):
    group_affiliation: Optional[str] = None
    relatives:         Optional[str] = None


class SuperheroCreate(BaseModel):
    """Schema para criar um herói manualmente via CRUD."""
    name:        str = Field(..., min_length=1, max_length=150)
    external_id: Optional[str] = None
    image_url:   Optional[str] = None
    powerstats:  Optional[PowerstatsInput]  = None
    biography:   Optional[BiographyInput]   = None
    appearance:  Optional[AppearanceInput]  = None
    work:        Optional[WorkInput]        = None
    connections: Optional[ConnectionsInput] = None


class SuperheroUpdate(BaseModel):
    """Schema para atualizar um herói. Todos os campos são opcionais."""
    name:        Optional[str] = Field(None, min_length=1, max_length=150)
    image_url:   Optional[str] = None
    powerstats:  Optional[PowerstatsInput]  = None
    biography:   Optional[BiographyInput]   = None
    appearance:  Optional[AppearanceInput]  = None
    work:        Optional[WorkInput]        = None
    connections: Optional[ConnectionsInput] = None


# ================================================================
# GRUPO 3 — Schemas de resposta para o cliente da nossa API
# ================================================================

class AliasResponse(BaseModel):
    id:    int
    alias: str

    class Config:
        from_attributes = True


class PowerstatsResponse(BaseModel):
    intelligence: Optional[int] = None
    strength:     Optional[int] = None
    speed:        Optional[int] = None
    durability:   Optional[int] = None
    power:        Optional[int] = None
    combat:       Optional[int] = None

    class Config:
        from_attributes = True


class BiographyResponse(BaseModel):
    full_name:        Optional[str] = None
    alter_egos:       Optional[str] = None
    aliases:          List[AliasResponse] = []
    place_of_birth:   Optional[str] = None
    first_appearance: Optional[str] = None
    publisher:        Optional[str] = None
    alignment:        Optional[str] = None

    class Config:
        from_attributes = True


class AppearanceResponse(BaseModel):
    gender:     Optional[str] = None
    race:       Optional[str] = None
    eye_color:  Optional[str] = None
    hair_color: Optional[str] = None
    heights:    List[str] = []
    weights:    List[str] = []

    class Config:
        from_attributes = True


class WorkResponse(BaseModel):
    occupation: Optional[str] = None
    base:       Optional[str] = None

    class Config:
        from_attributes = True


class ConnectionsResponse(BaseModel):
    group_affiliation: Optional[str] = None
    relatives:         Optional[str] = None

    class Config:
        from_attributes = True


class SuperheroResponse(BaseModel):
    """Schema de resposta completo de um herói."""
    id:          int
    external_id: Optional[str] = None
    name:        str
    image_url:   Optional[str] = None
    created_at:  Optional[datetime] = None
    updated_at:  Optional[datetime] = None
    powerstats:  Optional[PowerstatsResponse]  = None
    biography:   Optional[BiographyResponse]   = None
    appearance:  Optional[AppearanceResponse]  = None
    work:        Optional[WorkResponse]        = None
    connections: Optional[ConnectionsResponse] = None

    class Config:
        from_attributes = True


class ImportResultResponse(BaseModel):
    """Resposta do endpoint de importação."""
    query:    str
    imported: int
    skipped:  int
    heroes:   List[SuperheroResponse]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    response:   str
    tools_used: List[str] = []