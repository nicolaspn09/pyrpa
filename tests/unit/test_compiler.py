import ast
from pathlib import Path

from pyrpa.core.compiler import AirflowCompiler, mapear_periodicidade_para_cron
from pyrpa.core.generator import gerar_projeto_rpa


def test_mapeamento_periodicidade_cron():
    assert mapear_periodicidade_para_cron("manual") is None
    assert mapear_periodicidade_para_cron("diario") == "0 8 * * *"
    assert mapear_periodicidade_para_cron("horario") == "0 * * * *"
    assert mapear_periodicidade_para_cron("semanal") == "0 8 * * 1"
    assert mapear_periodicidade_para_cron("mensal") == "0 8 1 * *"
    assert mapear_periodicidade_para_cron("*/10 * * * *") == "*/10 * * * *"


def test_airflow_compiler_com_periodicidade_cron(tmp_path: Path):
    destino = tmp_path / "robo_cron"
    gerar_projeto_rpa("robo_cron", destino=destino)

    caminho_fluxo = destino / "metadados" / "fluxo.yaml"
    compilador = AirflowCompiler()
    caminho_dag = compilador.compilar(caminho_fluxo, schedule="diario")

    assert caminho_dag.is_file()
    conteudo = caminho_dag.read_text(encoding="utf-8")

    assert 'schedule_interval="0 8 * * *"' in conteudo
    assert "0 8 * * *" in conteudo
    # Validação sintática AST
    assert isinstance(ast.parse(conteudo), ast.Module)


def test_airflow_compiler_com_destino_customizado(tmp_path: Path):
    destino = tmp_path / "robo_custom_dag"
    gerar_projeto_rpa("robo_custom_dag", destino=destino)

    caminho_fluxo = destino / "metadados" / "fluxo.yaml"
    destino_custom = tmp_path / "minhas_dags" / "custom_dag.py"

    compilador = AirflowCompiler()
    caminho_gerado = compilador.compilar(caminho_fluxo, destino_dag=destino_custom, schedule="horario")

    assert caminho_gerado == destino_custom
    assert destino_custom.is_file()
    conteudo = destino_custom.read_text(encoding="utf-8")
    assert 'schedule_interval="0 * * * *"' in conteudo
