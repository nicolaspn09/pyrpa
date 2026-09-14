import pytest
from pydantic import ValidationError
from pyrpa.models.schema import FluxoSchema, TipoProvider


def test_deve_validar_fluxo_com_sucesso():
    dados_validos = {
        "fluxo": {
            "nome": "robo_faturamento",
            "versao": "1.0.0",
            "passos": [
                {
                    "id": "extrair_relatorio",
                    "nome": "Extrair Relatório Web",
                    "provider": "playwright",
                    "target": "application.extracao.ExtrairRelatorioUseCase"
                },
                {
                    "id": "processar_dados",
                    "nome": "Processar Dados Extraídos",
                    "provider": "pandas",
                    "target": "application.processamento.ProcessarUseCase"
                }
            ]
        }
    }
    esquema = FluxoSchema(**dados_validos)
    assert esquema.fluxo.nome == "robo_faturamento"
    assert len(esquema.fluxo.passos) == 2
    assert esquema.fluxo.passos[0].provider == TipoProvider.PLAYWRIGHT


def test_deve_falhar_quando_houver_ids_de_passos_duplicados():
    dados_duplicados = {
        "fluxo": {
            "nome": "robo_duplicado",
            "versao": "1.0.0",
            "passos": [
                {
                    "id": "mesmo_id",
                    "nome": "Passo Um",
                    "provider": "custom",
                    "target": "application.passo.UmUseCase"
                },
                {
                    "id": "mesmo_id",
                    "nome": "Passo Dois",
                    "provider": "custom",
                    "target": "application.passo.DoisUseCase"
                }
            ]
        }
    }
    with pytest.raises(ValidationError) as exc_info:
        FluxoSchema(**dados_duplicados)

    assert "IDs de passos duplicados encontrados: mesmo_id" in str(exc_info.value)


def test_deve_falhar_quando_target_nao_tiver_modulo():
    dados_target_invalido = {
        "fluxo": {
            "nome": "robo_teste",
            "versao": "1.0.0",
            "passos": [
                {
                    "id": "passo_1",
                    "nome": "Passo 1",
                    "provider": "custom",
                    "target": "ClasseSemModulo"
                }
            ]
        }
    }
    with pytest.raises(ValidationError):
        FluxoSchema(**dados_target_invalido)