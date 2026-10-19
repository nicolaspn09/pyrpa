from pathlib import Path
from typer.testing import CliRunner
from pyrpa.cli import app

runner = CliRunner()


def test_cli_init_deve_gerar_projeto_com_sucesso(tmp_path: Path):
    destino = tmp_path / "robo_cli"
    resultado = runner.invoke(app, ["init", "robo_cli", "--destino", str(destino)])

    assert resultado.exit_code == 0
    assert "Projeto criado com sucesso" in resultado.stdout
    assert (destino / "metadados" / "fluxo.yaml").is_file()
    assert (destino / "application" / "extracao.py").is_file()
    assert (destino / "application" / "processamento.py").is_file()


def test_cli_validate_deve_validar_fluxo_gerado(tmp_path: Path):
    destino = tmp_path / "robo_teste"
    runner.invoke(app, ["init", "robo_teste", "--destino", str(destino)])

    arquivo_fluxo = destino / "metadados" / "fluxo.yaml"
    resultado = runner.invoke(app, ["validate", str(arquivo_fluxo)])

    assert resultado.exit_code == 0
    assert "Fluxo válido e pronto para execução" in resultado.stdout
    assert "robo_teste" in resultado.stdout


def test_cli_validate_deve_falhar_com_arquivo_inexistente(tmp_path: Path):
    resultado = runner.invoke(app, ["validate", str(tmp_path / "inexistente.yaml")])
    assert resultado.exit_code == 1
    assert "Arquivo de fluxo não encontrado" in resultado.stdout


def test_cli_run_deve_executar_fluxo_com_sucesso(tmp_path: Path):
    destino = tmp_path / "robo_exec_cli"
    runner.invoke(app, ["init", "robo_exec_cli", "--destino", str(destino)])

    arquivo_fluxo = destino / "metadados" / "fluxo.yaml"
    resultado = runner.invoke(app, ["run", str(arquivo_fluxo)])

    assert resultado.exit_code == 0
    assert "Execução concluída com sucesso" in resultado.stdout
    assert "passo_1" in resultado.stdout
    assert "passo_2" in resultado.stdout


def test_cli_compile_deve_gerar_dag_airflow(tmp_path: Path):
    destino = tmp_path / "robo_compile_cli"
    runner.invoke(app, ["init", "robo_compile_cli", "--destino", str(destino)])

    arquivo_fluxo = destino / "metadados" / "fluxo.yaml"
    resultado = runner.invoke(app, ["compile", str(arquivo_fluxo)])

    assert resultado.exit_code == 0
    assert "DAG do Apache Airflow gerada com sucesso" in resultado.stdout
    assert (destino / "dags" / "dag_robo_compile_cli.py").is_file()
