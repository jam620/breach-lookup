from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class BreachRecord(BaseModel):
    id: Optional[int] = None
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    documento: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    email: Optional[str] = None
    movil: Optional[str] = None
    telefono: Optional[str] = None
    pais_origen: Optional[str] = None
    fecha_registro: Optional[str] = None
    usuario: Optional[str] = None
    friend_terpel: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "BreachRecord":
        return cls(**dict(row))


class SearchField(str):
    ALLOWED = {
        "__all__", "documento", "email", "movil", "telefono",
        "nombres", "apellidos", "usuario",
    }

    @classmethod
    def validate(cls, v: str) -> str:
        if v not in cls.ALLOWED:
            raise ValueError(f"field must be one of {cls.ALLOWED}")
        return v


class SearchRequest(BaseModel):
    q: str
    field: str = "__all__"
    limit: int = 50
    offset: int = 0

    @field_validator("field")
    @classmethod
    def field_must_be_valid(cls, v: str) -> str:
        return SearchField.validate(v)

    @field_validator("q")
    @classmethod
    def q_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("q cannot be empty")
        return v

    @field_validator("limit")
    @classmethod
    def limit_range(cls, v: int) -> int:
        if not 1 <= v <= 200:
            raise ValueError("limit must be between 1 and 200")
        return v


class SearchResponse(BaseModel):
    total: int
    results: list[BreachRecord]
    query_field: str
    page_offset: int
    page_limit: int


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class StatsResponse(BaseModel):
    total_records: int
    top_paises: list[dict]
    top_dominios_email: list[dict]
    nulos_por_campo: dict[str, int]
