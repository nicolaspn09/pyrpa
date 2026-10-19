from pathlib import Path
from textwrap import dedent
from typing import Optional, Union

from pyrpa.core.validator import validar_arquivo_fluxo


class CompiladorException(Exception):
    """Exceção lançada em falhas durante a compilação do fluxo declarativo para DAGs."""
    pass


def mapear_periodicidade_para_cron(periodicidade: Optional[str]) -> Optional[str]:
    """
    Traduz opções amigáveis em expressões cron padrão para o Apache Airflow.
    """
    if not periodicidade:
        return None
    p = str(periodicidade).strip().lower()
    if p in {"none", "manual", "sob_demanda", "sob demanda", "1"}:
        return None
    if p in {"horario", "horário", "hora", "@hourly", "2"}:
        return "0 * * * *"
    if p in {"diario", "diário", "dia", "@daily", "3"}:
        return "0 8 * * *"
    if p in {"semanal", "semana", "@weekly", "4"}:
        return "0 8 * * 1"
    if p in {"mensal", "mes", "mês", "@monthly", "5"}:
        return "0 8 1 * *"
    return str(periodicidade).strip()


class AirflowCompiler:
    """
    Compilador declarativo para Apache Airflow (RF05 do TCC).
    Converte as especificações do fluxo.yaml em código Python executável de DAGs,
    mapeando passos para PythonOperators e encadeando dependências sequenciais.
    """

    def compilar(
        self,
        caminho_fluxo: Union[str, Path],
        destino_dag: Optional[Union[str, Path]] = None,
        schedule: Optional[str] = None,
    ) -> Path:
        caminho = Path(caminho_fluxo).resolve()
        if not caminho.is_file():
            raise FileNotFoundError(f"Arquivo de fluxo não encontrado para compilação: {caminho}")

        esquema = validar_arquivo_fluxo(caminho)
        fluxo = esquema.fluxo

        if destino_dag is not None:
            caminho_saida = Path(destino_dag).resolve()
        else:
            pasta_dags = caminho.parent.parent / "dags"
            pasta_dags.mkdir(parents=True, exist_ok=True)
            caminho_saida = pasta_dags / f"dag_{fluxo.nome}.py"

        caminho_saida.parent.mkdir(parents=True, exist_ok=True)

        cron_expr = mapear_periodicidade_para_cron(schedule)
        schedule_valor = f'"{cron_expr}"' if cron_expr else "None"
        descricao_cron = f"Cron: {cron_expr}" if cron_expr else "Execução manual (sob demanda)"

        # Gera as funções de wrapper para cada tarefa
        funcoes_tarefas = []
        instanciacao_operadores = []
        nomes_tasks = []

        for passo in fluxo.passos:
            task_var = f"task_{passo.id}"
            func_name = f"_executar_{passo.id}"
            nomes_tasks.append(task_var)

            funcao_codigo = f"""
def {func_name}(**context):
    \"\"\"Wrapper de execução da etapa '{passo.nome}' ({passo.id}).\"\"\"
    import importlib
    from pyrpa.domain.contracts import ContextoExecucao

    modulo_nome, classe_nome = "{passo.target}".rsplit(".", 1)
    modulo = importlib.import_module(modulo_nome)
    classe_use_case = getattr(modulo, classe_nome)
    instancia = classe_use_case()

    ctx = ContextoExecucao()
    resultado = instancia.executar(ctx)

    if not resultado.sucesso:
        raise RuntimeError(f"Falha na etapa '{passo.id}': {{resultado.mensagem}}")
    return resultado.dados
""".strip()
            funcoes_tarefas.append(funcao_codigo)

            operador_codigo = f"""
    {task_var} = PythonOperator(
        task_id="{passo.id}",
        python_callable={func_name},
        doc_md=\"\"\"{passo.nome} (Provider: {passo.provider.value})\"\"\",
    )
""".rstrip()
            instanciacao_operadores.append(operador_codigo)

        # Encadeamento sequencial: task_1 >> task_2 >> task_3
        if len(nomes_tasks) > 1:
            encadeamento = " >> ".join(nomes_tasks)
        elif len(nomes_tasks) == 1:
            encadeamento = f"# Tarefa única no fluxo:\n    {nomes_tasks[0]}"
        else:
            encadeamento = "pass"

        bloco_funcoes = "\n\n\n".join(funcoes_tarefas)
        bloco_operadores = "\n".join(instanciacao_operadores)

        conteudo_dag = f"""\"\"\"
DAG gerada automaticamente pelo framework pyrpa (AirflowCompiler - RF05).
Fluxo: {fluxo.nome} (v{fluxo.versao})
Periodicidade: {descricao_cron}
Data de Geração: Automática
\"\"\"
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {{
    "owner": "pyrpa",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}}


{bloco_funcoes}


with DAG(
    dag_id="dag_{fluxo.nome}",
    default_args=default_args,
    description="Orquestração do robô {fluxo.nome} ({descricao_cron})",
    schedule_interval={schedule_valor},
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["pyrpa", "rpa", "clean_architecture"],
) as dag:

{bloco_operadores}

    # Encadeamento sequencial estrito das etapas
    {encadeamento}
"""

        caminho_saida.write_text(conteudo_dag.strip() + "\n", encoding="utf-8")
        return caminho_saida


def compilar_fluxo_airflow(
    caminho_fluxo: Union[str, Path],
    destino_dag: Optional[Union[str, Path]] = None,
    schedule: Optional[str] = None,
) -> Path:
    """Função utilitária para acionamento direto do compilador do Airflow."""
    compilador = AirflowCompiler()
    return compilador.compilar(caminho_fluxo, destino_dag, schedule=schedule)
