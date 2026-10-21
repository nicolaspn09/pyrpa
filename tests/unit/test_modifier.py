from pathlib import Path
import pytest
from pyrpa.core.generator import gerar_projeto_rpa
from pyrpa.core.modifier import (
    adicionar_modulo_projeto,
    ModificadorProjetoException,
    MODULOS_SUPORTADOS
)
from pyrpa.core.validator import validar_arquivo_fluxo


def test_adicionar_modulo_invalido_deve_lancar_excecao(tmp_path: Path):
    with pytest.raises(ModificadorProjetoException) as exc:
        adicionar_modulo_projeto("modulo_fantasma", diretorio_projeto=tmp_path)
    assert "Módulo desconhecido" in str(exc.value)


def test_adicionar_modulo_sem_fluxo_deve_lancar_excecao(tmp_path: Path):
    with pytest.raises(ModificadorProjetoException) as exc:
        adicionar_modulo_projeto("web", diretorio_projeto=tmp_path)
    assert "Projeto pyrpa não encontrado" in str(exc.value)


@pytest.mark.parametrize("modulo", sorted(MODULOS_SUPORTADOS))
def test_adicionar_cada_modulo_suportado(tmp_path: Path, modulo: str):
    projeto_dir = tmp_path / f"robo_{modulo}"
    gerar_projeto_rpa(f"robo_{modulo}", destino=projeto_dir)

    resultado = adicionar_modulo_projeto(modulo, diretorio_projeto=projeto_dir)

    assert resultado.nome_modulo == modulo
    assert resultado.passo_adicionado_id.startswith("etapa_")
    assert len(resultado.arquivos_criados) > 0

    # Validação do arquivo gerado
    caminho_fluxo = projeto_dir / "metadados" / "fluxo.yaml"
    esquema = validar_arquivo_fluxo(caminho_fluxo)

    ids = [p.id for p in esquema.fluxo.passos]
    assert resultado.passo_adicionado_id in ids


def test_adicionar_modulo_duplicado_gera_id_unico(tmp_path: Path):
    projeto_dir = tmp_path / "robo_multi_modulos"
    gerar_projeto_rpa("robo_multi_modulos", destino=projeto_dir)

    # Primeira adição
    res1 = adicionar_modulo_projeto("banco", diretorio_projeto=projeto_dir)
    assert res1.passo_adicionado_id == "etapa_banco_dados"

    # Segunda adição do mesmo módulo
    res2 = adicionar_modulo_projeto("banco", diretorio_projeto=projeto_dir)
    assert res2.passo_adicionado_id == "etapa_banco_dados_2"

    caminho_fluxo = projeto_dir / "metadados" / "fluxo.yaml"
    esquema = validar_arquivo_fluxo(caminho_fluxo)

    ids = [p.id for p in esquema.fluxo.passos]
    assert "etapa_banco_dados" in ids
    assert "etapa_banco_dados_2" in ids
