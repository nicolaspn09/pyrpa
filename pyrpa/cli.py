from pathlib import Path
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pyrpa.core.compiler import AirflowCompiler, CompiladorException, mapear_periodicidade_para_cron
from pyrpa.core.generator import gerar_projeto_rpa, GeradorProjetoException
from pyrpa.core.runner import FluxoRunner
from pyrpa.core.validator import validar_arquivo_fluxo, FluxoInvalidoException

app = typer.Typer(
    help="pyrpa - CLI Opinativa para Scaffolding e Gestão de Projetos RPA em Clean Architecture",
    no_args_is_help=True
)
console = Console()


@app.command(name="init")
def init(
    nome_projeto: str = typer.Argument(..., help="Nome do projeto / robô a ser criado"),
    destino: Optional[Path] = typer.Option(
        None,
        "--destino", "-d",
        help="Diretório onde o projeto será criado (padrão: ./<nome_projeto>)"
    ),
    forcar: bool = typer.Option(
        False,
        "--forcar", "-f",
        help="Sobrescrever arquivos se o diretório de destino já existir"
    )
) -> None:
    """
    Inicializa um novo projeto RPA estruturado estritamente em Clean Architecture.
    """
    pasta_destino = destino if destino is not None else Path.cwd() / nome_projeto

    console.print(f"\n[bold blue]>> Inicializando projeto RPA:[/bold blue] [green]{nome_projeto}[/green]")

    try:
        caminho_final = gerar_projeto_rpa(
            nome_projeto=nome_projeto,
            destino=pasta_destino,
            forcar=forcar
        )

        tabela = Table(title="Camadas Arquiteturais Geradas", show_header=True, header_style="bold magenta")
        tabela.add_column("Camada", style="cyan", width=20)
        tabela.add_column("Responsabilidade Clean Architecture", style="white")

        tabela.add_row("domain/", "Entidades, regras de cálculo e validação pura (Python puro, zero dependências)")
        tabela.add_row("application/", "Casos de uso e orquestração interna das regras de negócio do robô")
        tabela.add_row("infrastructure/", "Adaptadores externos: drivers (Playwright/Selenium), bancos SQL e APIs")
        tabela.add_row("interfaces/", "Ponto de entrada, controladores locais e adapters de terminal")
        tabela.add_row("metadados/fluxo.yaml", "Orquestração declarativa dos passos e adaptadores")

        console.print(tabela)
        console.print(Panel.fit(
            f"[bold green][OK] Projeto criado com sucesso em:[/bold green]\n{caminho_final}\n\n"
            f"[yellow]Para começar:[/yellow]\n"
            f"  cd {caminho_final.name}\n"
            f"  python main.py",
            border_style="green"
        ))

    except GeradorProjetoException as exc:
        console.print(Panel(f"[bold red]Falha na inicialização:[/bold red]\n{exc}", border_style="red"))
        raise typer.Exit(code=1)


@app.command(name="validate")
def validate(
    caminho: Path = typer.Argument(
        Path("metadados/fluxo.yaml"),
        help="Caminho do arquivo de fluxo YAML a ser validado"
    )
) -> None:
    """
    Valida um arquivo de orquestração de fluxo contra o contrato Pydantic do pyrpa.
    """
    console.print(f"\n[bold blue]>> Validando contrato de fluxo:[/bold blue] {caminho}")

    try:
        esquema = validar_arquivo_fluxo(caminho)

        tabela = Table(title=f"Fluxo: {esquema.fluxo.nome} (v{esquema.fluxo.versao})", border_style="green")
        tabela.add_column("ID", style="bold cyan")
        tabela.add_column("Nome da Etapa", style="white")
        tabela.add_column("Provider", style="yellow")
        tabela.add_column("Target UseCase", style="magenta")

        for passo in esquema.fluxo.passos:
            tabela.add_row(passo.id, passo.nome, passo.provider.value, passo.target)

        console.print(tabela)
        console.print(f"[bold green][OK] Fluxo válido e pronto para execução ou compilação de DAG![/bold green]\n")

    except (FileNotFoundError, FluxoInvalidoException) as exc:
        console.print(Panel(f"[bold red]Erro de Validação:[/bold red]\n{exc}", border_style="red"))
        raise typer.Exit(code=1)


@app.command(name="run")
def run(
    caminho: Path = typer.Argument(
        Path("metadados/fluxo.yaml"),
        help="Caminho do arquivo de fluxo YAML a ser executado"
    )
) -> None:
    """
    Executa localmente o fluxo do robô conforme definido no fluxo.yaml.
    """
    console.print(f"\n[bold blue]>> Executando fluxo RPA:[/bold blue] {caminho}")

    try:
        runner = FluxoRunner()
        resultado = runner.executar(caminho)

        tabela = Table(
            title=f"Resultado da Execução: {resultado.nome_fluxo} (v{resultado.versao})",
            border_style="green" if resultado.sucesso else "red"
        )
        tabela.add_column("ID Passo", style="bold cyan")
        tabela.add_column("Status", style="bold")
        tabela.add_column("Duração (s)", style="yellow")
        tabela.add_column("Mensagem", style="white")

        for passo_id, res_passo in resultado.resultados_passos.items():
            status_txt = "[green][OK][/green]" if res_passo.sucesso else "[red][FALHA][/red]"
            tabela.add_row(passo_id, status_txt, f"{res_passo.duracao_segundos:.3f}", res_passo.mensagem)

        console.print(tabela)

        if resultado.sucesso:
            console.print(Panel.fit(
                f"[bold green][OK] Execução concluída com sucesso![/bold green]\n"
                f"Passos executados: {resultado.passos_executados}/{resultado.total_passos}\n"
                f"Tempo total: {resultado.duracao_total_segundos:.3f} segundos",
                border_style="green"
            ))
        else:
            console.print(Panel.fit(
                f"[bold red][FALHA] Execução interrompida:[/bold red]\n{resultado.erro}\n"
                f"Passos executados com êxito: {resultado.passos_executados - 1}/{resultado.total_passos}",
                border_style="red"
            ))
            raise typer.Exit(code=1)

    except (FileNotFoundError, FluxoInvalidoException) as exc:
        console.print(Panel(f"[bold red]Erro de Validação pré-execução:[/bold red]\n{exc}", border_style="red"))
        raise typer.Exit(code=1)


@app.command(name="compile")
def compile_airflow(
    caminho: Path = typer.Argument(
        Path("metadados/fluxo.yaml"),
        help="Caminho do arquivo de fluxo YAML a ser compilado"
    ),
    destino: Optional[Path] = typer.Option(
        None,
        "--destino", "-o",
        help="Caminho do arquivo DAG a ser gerado (padrão: ./dags/dag_<nome>.py)"
    ),
    schedule: Optional[str] = typer.Option(
        None,
        "--schedule", "-s",
        help="Periodicidade de execução cron (ex: 'diario', 'horario', 'semanal', '0 8 * * *', 'manual')"
    )
) -> None:
    """
    Compila o fluxo.yaml para uma DAG executável do Apache Airflow com agendamento cron (RF05 do TCC).
    """
    console.print(f"\n[bold blue]>> Compilando fluxo para Apache Airflow:[/bold blue] {caminho}")

    # Pergunta interativamente a periodicidade caso não tenha sido passada por parâmetro
    if schedule is None and sys.stdin.isatty():
        console.print("\n[bold cyan]Escolha a periodicidade de execução no Airflow:[/bold cyan]")
        console.print("  [1] Manual (Sob demanda / sem agendamento)")
        console.print("  [2] De hora em hora (@hourly)")
        console.print("  [3] Diário (todos os dias às 08:00)")
        console.print("  [4] Semanal (toda segunda-feira às 08:00)")
        console.print("  [5] Mensal (no 1º dia do mês às 08:00)")
        console.print("  [6] Personalizado (digitar expressão cron)")
        opcao = typer.prompt("Opção", default="1")
        if opcao == "6":
            schedule = typer.prompt("Digite a expressão cron (ex: */15 * * * *)")
        else:
            schedule = opcao

    try:
        compilador = AirflowCompiler()
        caminho_dag = compilador.compilar(caminho_fluxo=caminho, destino_dag=destino, schedule=schedule)
        cron_resolvido = mapear_periodicidade_para_cron(schedule)
        info_agenda = f"[yellow]Agendamento:[/yellow] {cron_resolvido}" if cron_resolvido else "[yellow]Agendamento:[/yellow] Manual (None)"

        console.print(Panel.fit(
            f"[bold green][OK] DAG do Apache Airflow gerada com sucesso![/bold green]\n\n"
            f"[cyan]Arquivo gerado:[/cyan] {caminho_dag}\n"
            f"{info_agenda}\n\n"
            f"[yellow]Para publicar no Airflow:[/yellow] Copie este arquivo para a pasta $AIRFLOW_HOME/dags/",
            border_style="green"
        ))

    except (FileNotFoundError, FluxoInvalidoException, CompiladorException) as exc:
        console.print(Panel(f"[bold red]Erro de Compilação:[/bold red]\n{exc}", border_style="red"))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
