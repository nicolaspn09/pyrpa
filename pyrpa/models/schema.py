from enum import Enum
from typing import List
from pydantic import BaseModel, Field, field_validator


class TipoProvider(str, Enum):
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"
    UNDETECTED_CHROMEDRIVER = "undetected_chromedriver"
    PANDAS = "pandas"
    DATABASE = "database"
    HTTP = "http"
    STORAGE = "storage"
    NOTIFIER = "notifier"
    CUSTOM = "custom"


class PassoModel(BaseModel):
    id: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Identificador único da etapa, sem espaços ou caracteres especiais."
    )
    nome: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Nome descritivo legível para logs e interfaces."
    )
    provider: TipoProvider = Field(
        default=TipoProvider.CUSTOM,
        description="Ferramenta/adaptador responsável pela execução."
    )
    target: str = Field(
        ...,
        pattern=r"^([a-zA-Z_]\w*\.)+[a-zA-Z_]\w*$",
        description="Caminho canônico de importação do UseCase (ex: application.modulo.ClasseUseCase)."
    )


class FluxoModel(BaseModel):
    nome: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    versao: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    passos: List[PassoModel] = Field(..., min_length=1)

    @field_validator("passos")
    @classmethod
    def validar_passos_unicos(cls, passos: List[PassoModel]) -> List[PassoModel]:
        ids_encontrados = set()
        duplicados = set()

        for passo in passos:
            if passo.id in ids_encontrados:
                duplicados.add(passo.id)
            ids_encontrados.add(passo.id)

        if duplicados:
            raise ValueError(f"IDs de passos duplicados encontrados: {', '.join(duplicados)}")

        return passos


class FluxoSchema(BaseModel):
    fluxo: FluxoModel
