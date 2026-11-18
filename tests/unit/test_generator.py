from pathlib import Path
import pytest

from pyrpa.core.generator import gerar_projeto_rpa, GeradorProjetoException
from pyrpa.core.validator import validar_arquivo_fluxo


def test_deve_gerar_estrutura_completa_do_projeto(tmp_path: Path):
    destino = tmp_path / "meu_robo"
    caminho_gerado = gerar_projeto_rpa(nome_projeto="meu_robo", destino=destino)

    # Valida presença das 4 camadas Clean Architecture + metadados
    assert (caminho_gerado / "domain").is_dir()
    assert (caminho_gerado / "application").is_dir()
    assert (caminho_gerado / "infrastructure").is_dir()
    assert (caminho_gerado / "interfaces").is_dir()
    assert (caminho_gerado / "metadados").is_dir()

    # Valida arquivos essenciais
    assert (caminho_gerado / "main.py").is_file()
    assert (caminho_gerado / "requirements.txt").is_file()
    assert (caminho_gerado / ".env").is_file()
    assert (caminho_gerado / ".gitignore").is_file()

    req_txt = (caminho_gerado / "requirements.txt").read_text(encoding="utf-8")
    assert "pyrpa>=0.1.0" not in req_txt
    assert "pandas>=" in req_txt and "# pandas" not in req_txt

    # Valida que o fluxo gerado respeita o contrato do Pydantic
    arquivo_fluxo = caminho_gerado / "metadados" / "fluxo.yaml"
    esquema = validar_arquivo_fluxo(arquivo_fluxo)
    assert esquema.fluxo.nome == "meu_robo"
    assert len(esquema.fluxo.passos) == 2


def test_deve_falhar_quando_diretorio_existir_e_nao_estiver_vazio(tmp_path: Path):
    destino = tmp_path / "robo_existente"
    destino.mkdir()
    (destino / "antigo.txt").write_text("conteudo", encoding="utf-8")

    with pytest.raises(GeradorProjetoException) as exc_info:
        gerar_projeto_rpa(nome_projeto="robo_existente", destino=destino)

    assert "já existe e não está vazio" in str(exc_info.value)


def test_deve_falhar_com_nome_de_projeto_invalido(tmp_path: Path):
    with pytest.raises(GeradorProjetoException) as exc_info:
        gerar_projeto_rpa(nome_projeto="Nome Inválido Com Espaço", destino=tmp_path / "invalido")

    assert "Nome de projeto inválido" in str(exc_info.value)