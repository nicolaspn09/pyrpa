from pathlib import Path
from typer.testing import CliRunner
from pyrpa.cli import app

runner = CliRunner()


def test_cli_info():
    resultado = runner.invoke(app, ["info"])
    assert resultado.exit_code == 0
    assert "pyrpa - Framework de Engenharia de Software" in resultado.stdout
    assert "Catálogo de Conectores e Módulos Suportados" in resultado.stdout
    assert "Guia Rápido de Comandos da CLI" in resultado.stdout


def test_cli_doctor():
    resultado = runner.invoke(app, ["doctor"])
    assert resultado.exit_code == 0
    assert "Diagnóstico de Ambiente do Sistema" in resultado.stdout
    assert "Versão do Python" in resultado.stdout


def test_cli_init_deve_gerar_projeto_com_sucesso(tmp_path: Path):
    destino = tmp_path / "robo_cli"
    resultado = runner.invoke(app, ["init", "robo_cli", "--destino", str(destino)])

    assert resultado.exit_code == 0
    assert "Projeto criado com sucesso" in resultado.stdout
    assert (destino / "metadados" / "fluxo.yaml").is_file()
    assert (destino / "application" / "extracao.py").is_file()
    assert (destino / "application" / "processamento.py").is_file()


def test_cli_init_com_modulos(tmp_path: Path):
    destino = tmp_path / "robo_modulos_cli"
    resultado = runner.invoke(
        app,
        ["init", "robo_modulos_cli", "--destino", str(destino), "--modulos", "web,banco"]
    )

    assert resultado.exit_code == 0
    assert "Projeto criado com sucesso" in resultado.stdout
    assert (destino / "metadados" / "fluxo.yaml").is_file()


def test_cli_add_modulo(tmp_path: Path):
    destino = tmp_path / "robo_add_cli"
    runner.invoke(app, ["init", "robo_add_cli", "--destino", str(destino)])

    resultado = runner.invoke(app, ["add", "pdf", "--destino", str(destino)])
    assert resultado.exit_code == 0
    assert "incorporado com sucesso ao fluxo.yaml" in resultado.stdout
    assert (destino / "application" / "leitura_pdf.py").is_file()


def test_cli_add_modulo_invalido(tmp_path: Path):
    destino = tmp_path / "robo_add_err"
    runner.invoke(app, ["init", "robo_add_err", "--destino", str(destino)])

    resultado = runner.invoke(app, ["add", "modulo_invalido", "--destino", str(destino)])
    assert resultado.exit_code == 1
    assert "Falha ao adicionar módulo" in resultado.stdout


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
