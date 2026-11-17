from pathlib import Path
from pyrpa.core.generator import gerar_projeto_rpa
from pyrpa.core.runner import FluxoRunner
from pyrpa.domain.contracts import ContextoExecucao


def test_runner_deve_executar_fluxo_completo_gerado_com_sucesso(tmp_path: Path):
    destino = tmp_path / "robo_runner_ok"
    gerar_projeto_rpa("robo_runner_ok", destino=destino)

    caminho_fluxo = destino / "metadados" / "fluxo.yaml"
    runner = FluxoRunner()
    resultado = runner.executar(caminho_fluxo=caminho_fluxo, diretorio_projeto=destino)

    assert resultado.sucesso is True
    assert resultado.nome_fluxo == "robo_runner_ok"
    assert resultado.passos_executados == 2
    assert resultado.total_passos == 2
    assert "passo_1" in resultado.resultados_passos
    assert "passo_2" in resultado.resultados_passos
    assert resultado.resultados_passos["passo_1"].sucesso is True
    assert resultado.resultados_passos["passo_2"].sucesso is True


def test_runner_deve_interromper_execucao_quando_etapa_falhar(tmp_path: Path):
    destino = tmp_path / "robo_runner_falha"
    gerar_projeto_rpa("robo_runner_falha", destino=destino)

    # Modifica o use case do passo_1 para falhar intencionalmente
    codigo_falha = """
from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso

class ExtrairDadosUseCase(BaseUseCase):
    def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
        return ResultadoPasso(sucesso=False, mensagem="Simulação de erro na extração web")
"""
    (destino / "application" / "extracao.py").write_text(codigo_falha.strip(), encoding="utf-8")

    caminho_fluxo = destino / "metadados" / "fluxo.yaml"
    runner = FluxoRunner()
    resultado = runner.executar(caminho_fluxo=caminho_fluxo, diretorio_projeto=destino)

    assert resultado.sucesso is False
    assert resultado.passos_executados == 1
    assert "Simulação de erro na extração web" in (resultado.erro or "")
    assert "passo_2" not in resultado.resultados_passos


def test_runner_deve_compartilhar_dados_entre_passos_via_contexto(tmp_path: Path):
    destino = tmp_path / "robo_contexto"
    gerar_projeto_rpa("robo_contexto", destino=destino)

    caminho_fluxo = destino / "metadados" / "fluxo.yaml"
    ctx = ContextoExecucao()
    runner = FluxoRunner()
    resultado = runner.executar(caminho_fluxo=caminho_fluxo, diretorio_projeto=destino, contexto_inicial=ctx)

    assert resultado.sucesso is True
    # O passo_1 gravou "dados_extraidos" no contexto
    assert ctx.contem("dados_extraidos") is True
    dados = ctx.obter("dados_extraidos")
    assert len(dados) == 3


def test_runner_deve_carregar_variaveis_do_dotenv_do_projeto(tmp_path: Path, monkeypatch):
    import os

    destino = tmp_path / "robo_dotenv"
    gerar_projeto_rpa("robo_dotenv", destino=destino)

    # Garante ambiente limpo antes da execução e configura valor customizado no .env
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("DB_URL", raising=False)
    monkeypatch.delenv("HEADLESS", raising=False)
    monkeypatch.delenv("BROWSER_ENGINE", raising=False)
    (destino / ".env").write_text(
        "ENVIRONMENT=production\nHEADLESS=false\nBROWSER_ENGINE=selenium\nDB_URL=sqlite:///dados_rpa.db\n",
        encoding="utf-8",
    )

    runner = FluxoRunner()
    resultado = runner.executar(
        caminho_fluxo=destino / "metadados" / "fluxo.yaml",
        diretorio_projeto=destino,
    )

    assert resultado.sucesso is True
    assert os.getenv("HEADLESS") == "false"
    assert os.getenv("BROWSER_ENGINE") == "selenium"
