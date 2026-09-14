from pathlib import Path
from textwrap import dedent
import pytest
from pydantic import ValidationError
import yaml

from pyrpa.core.validator import validar_arquivo_fluxo, FluxoInvalidoException


def test_deve_validar_arquivo_yaml_valido_com_sucesso(tmp_path: Path):
    # Arrange: cria um fluxo.yaml válido no diretório temporário
    arquivo_yaml = tmp_path / "fluxo.yaml"
    conteudo = dedent("""
        fluxo:
          nome: "robo_nf"
          versao: "1.0.0"
          passos:
            - id: "passo_1"
              nome: "Baixar NFs"
              provider: "playwright"
              target: "application.nfs.BaixarUseCase"
        """).strip()
    arquivo_yaml.write_text(conteudo, encoding="utf-8")

    # Act
    esquema = validar_arquivo_fluxo(arquivo_yaml)

    # Assert
    assert esquema.fluxo.nome == "robo_nf"
    assert len(esquema.fluxo.passos) == 1
    assert esquema.fluxo.passos[0].id == "passo_1"


def test_deve_lancar_excecao_quando_arquivo_nao_existir(tmp_path: Path):
    arquivo_inexistente = tmp_path / "inexistente.yaml"

    with pytest.raises(FileNotFoundError) as exc_info:
        validar_arquivo_fluxo(arquivo_inexistente)

    assert "Arquivo de fluxo não encontrado" in str(exc_info.value)


def test_deve_lancar_excecao_quando_yaml_tiver_erro_de_sintaxe(tmp_path: Path):
    arquivo_corrompido = tmp_path / "corrompido.yaml"
    arquivo_corrompido.write_text("fluxo:\n  nome: robo\n passos: [", encoding="utf-8")

    with pytest.raises(FluxoInvalidoException) as exc_info:
        validar_arquivo_fluxo(arquivo_corrompido)

    assert "Erro de sintaxe no arquivo YAML" in str(exc_info.value)