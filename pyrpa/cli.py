from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pyrpa.core.generator import gerar_projeto_rpa, GeradorProjetoException
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


if __name__ == "__main__":
    app()