import ast
from pathlib import Path

from pyrpa.core.compiler import AirflowCompiler
from pyrpa.core.generator import gerar_projeto_rpa


def test_airflow_compiler_deve_gerar_dag_sintaticamente_valida(tmp_path: Path):
    destino = tmp_path / "robo_airflow"
    gerar_projeto_rpa("robo_airflow", destino=destino)

    caminho_fluxo = destino / "metadados" / "fluxo.yaml"
    compilador = AirflowCompiler()
    caminho_dag = compilador.compilar(caminho_fluxo)

    assert caminho_dag.is_file()
    assert caminho_dag.name == "dag_robo_airflow.py"

    conteudo_dag = caminho_dag.read_text(encoding="utf-8")

    # Validação sintática formal via analisador abstrato do Python (AST)
    arvore_ast = ast.parse(conteudo_dag)
    assert isinstance(arvore_ast, ast.Module)

    # Validações de conteúdo da DAG
    assert "dag_id=\"dag_robo_airflow\"" in conteudo_dag
    assert "PythonOperator" in conteudo_dag
    assert "task_id=\"passo_1\"" in conteudo_dag
    assert "task_id=\"passo_2\"" in conteudo_dag
    assert "task_passo_1 >> task_passo_2" in conteudo_dag


def test_airflow_compiler_com_destino_customizado(tmp_path: Path):
    destino = tmp_path / "robo_custom_dag"
    gerar_projeto_rpa("robo_custom_dag", destino=destino)

    caminho_fluxo = destino / "metadados" / "fluxo.yaml"
    destino_custom = tmp_path / "minhas_dags" / "custom_dag.py"

    compilador = AirflowCompiler()
    caminho_gerado = compilador.compilar(caminho_fluxo, destino_dag=destino_custom)

    assert caminho_gerado == destino_custom
    assert destino_custom.is_file()
