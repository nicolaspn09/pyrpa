from pathlib import Path
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pyrpa.core.compiler import AirflowCompiler, CompiladorException, mapear_periodicidade_para_cron
from pyrpa.core.doctor import executar_diagnostico_doctor
from pyrpa.core.generator import gerar_projeto_rpa, GeradorProjetoException
from pyrpa.core.modifier import adicionar_modulo_projeto, ModificadorProjetoException, MODULOS_SUPORTADOS
from pyrpa.core.runner import FluxoRunner
from pyrpa.core.validator import validar_arquivo_fluxo, FluxoInvalidoException

app = typer.Typer(
    help="pyrpa - Framework de Scaffolding e Orquestração Declarativa para RPA em Clean Architecture",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def resolver_caminho_fluxo(caminho_informado: Path, operacao: str = "Validação") -> Path:
    """
    Verifica a existência do arquivo de fluxo. Se não existir no caminho informado,
    inspeciona o diretório atual em busca de subpastas de robôs pyrpa e orienta
    o desenvolvedor de forma amigável com comandos de navegação prontos.
    """
    if caminho_informado.is_file():
        return caminho_informado

    pastas_robos = []
    try:
        for item in Path.cwd().iterdir():
            if item.is_dir() and (item / "metadados" / "fluxo.yaml").is_file():
                pastas_robos.append(item.name)
    except Exception:
        pass

    caminho_absoluto = caminho_informado.resolve()
    mensagem = f"Arquivo de fluxo não encontrado no caminho:\n[yellow]{caminho_absoluto}[/yellow]\n\n"

    comando_op = operacao.lower()
    if comando_op == "compilação":
        comando_op = "compile"
    elif comando_op == "execução":
        comando_op = "run"
    elif comando_op == "validação":
        comando_op = "validate"

    if pastas_robos:
        primeiro = pastas_robos[0]
        lista_robos = ", ".join(f"'{r}'" for r in pastas_robos)
        mensagem += (
            f"[bold green]>> Dica de Navegação:[/bold green]\n"
            f"Detectamos o(s) seguinte(s) robô(s) nesta pasta: [bold cyan]{lista_robos}[/bold cyan]!\n"
            f"Para utilizá-lo, entre na pasta do projeto primeiro:\n"
            f"  [bold yellow]cd {primeiro}[/bold yellow]\n"
            f"  [bold yellow]pyrpa {comando_op}[/bold yellow]\n\n"
            f"Ou aponte diretamente para o arquivo:\n"
            f"  [bold yellow]pyrpa {comando_op} {primeiro}/metadados/fluxo.yaml[/bold yellow]"
        )
    else:
        mensagem += (
            "[bold yellow]Dica:[/bold yellow] Certifique-se de estar dentro da pasta do robô "
            f"ou inicialize um novo projeto com: [bold cyan]pyrpa init <nome_do_projeto>[/bold cyan]"
        )

    console.print(Panel(mensagem, title=f"[bold red]Erro de {operacao}[/bold red]", border_style="red"))
    raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v",
        help="Exibe a versão instalada do pyrpa."
    ),
    info_flag: bool = typer.Option(
        False, "--info",
        help="Exibe o catálogo completo de conectores e guia rápido."
    ),
    doctor_flag: bool = typer.Option(
        False, "--doctor",
        help="Executa diagnóstico de integridade do ambiente e navegadores."
    ),
    validate_flag: bool = typer.Option(
        False, "--validate",
        help="Valida o fluxo.yaml do projeto atual."
    ),
    run_flag: bool = typer.Option(
        False, "--run",
        help="Executa o fluxo do projeto atual."
    ),
    compile_flag: bool = typer.Option(
        False, "--compile",
        help="Compila o fluxo do projeto atual para Apache Airflow."
    ),
) -> None:
    """
    pyrpa - Framework de Scaffolding e Orquestração Declarativa para RPA em Clean Architecture.
    """
    if ctx.invoked_subcommand is None:
        if version:
            console.print("[bold cyan]pyrpa[/bold cyan] versão [bold green]0.1.0[/bold green]")
            raise typer.Exit()
        if info_flag:
            info()
            raise typer.Exit()
        if doctor_flag:
            doctor(destino=None)
            raise typer.Exit()
        if validate_flag:
            validate(caminho=Path("metadados/fluxo.yaml"))
            raise typer.Exit()
        if run_flag:
            run(caminho=Path("metadados/fluxo.yaml"))
            raise typer.Exit()
        if compile_flag:
            compile_airflow(caminho=Path("metadados/fluxo.yaml"))
            raise typer.Exit()
        console.print(ctx.get_help())
        raise typer.Exit()


@app.command(name="info")
def info() -> None:
    """
    Exibe o catálogo completo de conectores, arquitetura e guia de comandos do pyrpa.
    """
    console.print(Panel.fit(
        "[bold cyan]pyrpa - Framework de Engenharia de Software e RPA Corporativo[/bold cyan]\n"
        "[white]Desenvolvido com Clean Architecture, tipagem estática e orquestração declarativa.[/white]",
        border_style="cyan"
    ))

    # Tabela de Módulos
    tabela_modulos = Table(title="Catálogo de Conectores e Módulos Suportados", header_style="bold magenta")
    tabela_modulos.add_column("Módulo", style="bold cyan", width=12)
    tabela_modulos.add_column("Tecnologias Utilizadas", style="yellow", width=32)
    tabela_modulos.add_column("Casos de Uso Corporativos", style="white")

    tabela_modulos.add_row(
        "web",
        "Playwright, Selenium, Undetected",
        "Navegação em portais, preenchimento de formulários e download com fechamento seguro."
    )
    tabela_modulos.add_row(
        "banco",
        "SQLAlchemy, SQLite",
        "Persistência transacional com commit/rollback automático para PostgreSQL, SQL Server e SQLite."
    )
    tabela_modulos.add_row(
        "excel",
        "Pandas, OpenPyXL",
        "Exportação de planilhas formatadas (.xlsx), leitor de dados universal (CSV, JSON, Excel)."
    )
    tabela_modulos.add_row(
        "pdf",
        "PyPDF, Expressões Regulares",
        "Extração de textos e reconhecimento automático de CNPJs, datas, valores e boletos bancários."
    )
    tabela_modulos.add_row(
        "ia",
        "LLMs (OpenAI, Groq, Ollama)",
        "Classificação inteligente de e-mails/chamados e extração estruturada de dados com prompts."
    )
    tabela_modulos.add_row(
        "email",
        "SMTP Corporativo, Webhooks",
        "Disparo de relatórios com anexos e alertas em canais do Microsoft Teams ou Slack."
    )
    console.print(tabela_modulos)

    # Tabela de Comandos
    tabela_comandos = Table(title="Guia Rápido de Comandos da CLI", header_style="bold green")
    tabela_comandos.add_column("Comando", style="bold cyan", width=22)
    tabela_comandos.add_column("Descrição", style="white")
    tabela_comandos.add_column("Exemplo de Uso", style="yellow")

    tabela_comandos.add_row(
        "pyrpa init <nome>",
        "Cria novo robô com Clean Architecture.",
        "pyrpa init robo_compras -m web,banco"
    )
    tabela_comandos.add_row(
        "pyrpa add <modulo>",
        "Acrescenta um conector ao robô existente.",
        "pyrpa add pdf"
    )
    tabela_comandos.add_row(
        "pyrpa validate",
        "Valida integridade do fluxo.yaml.",
        "pyrpa validate metadados/fluxo.yaml"
    )
    tabela_comandos.add_row(
        "pyrpa run",
        "Executa o fluxo localmente com cronômetro.",
        "pyrpa run"
    )
    tabela_comandos.add_row(
        "pyrpa compile",
        "Gera DAG para o Apache Airflow.",
        "pyrpa compile -s diario"
    )
    tabela_comandos.add_row(
        "pyrpa doctor",
        "Verifica saúde do ambiente e navegadores.",
        "pyrpa doctor"
    )
    tabela_comandos.add_row(
        "pyrpa info",
        "Apresenta este manual interativo.",
        "pyrpa info"
    )
    console.print(tabela_comandos)


@app.command(name="doctor")
def doctor(
    destino: Optional[Path] = typer.Option(
        None,
        "--destino", "-d",
        help="Diretório do projeto a ser diagnosticado (padrão: diretório atual)"
    )
) -> None:
    """
    Executa diagnóstico de saúde do ambiente, dependências e navegadores instalados.
    """
    console.print("\n[bold blue]>> Executando diagnóstico do ambiente (pyrpa doctor)...[/bold blue]\n")
    diagnosticos = executar_diagnostico_doctor(diretorio_atual=destino)

    tabela = Table(title="Diagnóstico de Ambiente do Sistema", header_style="bold magenta")
    tabela.add_column("Categoria", style="cyan", width=24)
    tabela.add_column("Componente / Recurso", style="white", width=34)
    tabela.add_column("Status", style="bold", width=10)
    tabela.add_column("Diagnóstico / Detalhes", style="white")

    total_ok = 0
    total_avisos = 0
    total_falhas = 0

    for item in diagnosticos:
        if item.status == "OK":
            status_fmt = "[green][OK][/green]"
            total_ok += 1
        elif item.status == "AVISO":
            status_fmt = "[yellow][AVISO][/yellow]"
            total_avisos += 1
        else:
            status_fmt = "[red][FALHA][/red]"
            total_falhas += 1

        tabela.add_row(item.categoria, item.item, status_fmt, item.detalhes)

    console.print(tabela)

    if total_falhas == 0:
        console.print(Panel.fit(
            f"[bold green][OK] Ambiente pronto para desenvolvimento e execução RPA![/bold green]\n"
            f"Itens operacionais: {total_ok} | Avisos opcionais: {total_avisos}",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[bold red][FALHA] Foram encontrados {total_falhas} item(ns) impeditivo(s).[/bold red]\n"
            f"Verifique as linhas marcadas com [FALHA] acima antes de executar o robô.",
            border_style="red"
        ))


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
    ),
    modulos: Optional[str] = typer.Option(
        None,
        "--modulos", "-m",
        help="Módulos a incluir (ex: 'web,banco', 'excel,email', 'completo')"
    )
) -> None:
    """
    Inicializa um novo projeto RPA estruturado estritamente em Clean Architecture.
    """
    pasta_destino = destino if destino is not None else Path.cwd() / nome_projeto

    # Menu interativo se não foi informado via linha de comando
    if modulos is None and sys.stdin.isatty():
        console.print(f"\n[bold cyan]>> Configuração de Módulos para o Robô:[/bold cyan] [green]{nome_projeto}[/green]")
        console.print("  [1] Completo (Navegador, Banco, Excel, PDF, IA e E-mail) [Recomendado]")
        console.print("  [2] Automação Web (Playwright/Selenium)")
        console.print("  [3] Banco de Dados & APIs (SQLAlchemy, SQLite e HTTP Client)")
        console.print("  [4] Extração de Documentos & IA (PDFs + Inteligência Artificial)")
        console.print("  [5] Planilhas & Mensageria (Excel + Disparador de E-mail)")
        console.print("  [6] Personalizado (digitar módulos separados por vírgula)")
        escolha = typer.prompt("Opção", default="1")
        if escolha == "1":
            modulos = "completo"
        elif escolha == "2":
            modulos = "web"
        elif escolha == "3":
            modulos = "banco"
        elif escolha == "4":
            modulos = "pdf,ia"
        elif escolha == "5":
            modulos = "excel,email"
        elif escolha == "6":
            modulos = typer.prompt("Digite os módulos (ex: web,banco,pdf)")
        else:
            modulos = "completo"

    console.print(f"\n[bold blue]>> Inicializando projeto RPA:[/bold blue] [green]{nome_projeto}[/green]")

    try:
        caminho_final = gerar_projeto_rpa(
            nome_projeto=nome_projeto,
            destino=pasta_destino,
            forcar=forcar,
            modulos=modulos,
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
            f"  pyrpa run\n\n"
            f"[yellow]Para adicionar novos módulos depois:[/yellow]\n"
            f"  pyrpa add <modulo>  (ex: pyrpa add pdf)",
            border_style="green"
        ))

    except GeradorProjetoException as exc:
        console.print(Panel(f"[bold red]Falha na inicialização:[/bold red]\n{exc}", border_style="red"))
        raise typer.Exit(code=1)


@app.command(name="add")
def add(
    modulo: str = typer.Argument(
        ...,
        help=f"Módulo a ser adicionado ao robô: {', '.join(sorted(MODULOS_SUPORTADOS))}"
    ),
    destino: Optional[Path] = typer.Option(
        None,
        "--destino", "-d",
        help="Diretório do projeto (padrão: diretório atual)"
    )
) -> None:
    """
    Acrescenta um novo conector de infraestrutura e caso de uso a um projeto existente.
    """
    console.print(f"\n[bold blue]>> Adicionando módulo ao projeto:[/bold blue] [cyan]{modulo}[/cyan]")

    try:
        resultado = adicionar_modulo_projeto(nome_modulo=modulo, diretorio_projeto=destino)

        tabela = Table(title=f"Módulo Adicionado: {resultado.nome_modulo.upper()}", border_style="green")
        tabela.add_column("Item Modificado", style="bold cyan")
        tabela.add_column("Detalhe", style="white")

        tabela.add_row("Identificador da Etapa", resultado.passo_adicionado_id)
        tabela.add_row("Nome da Etapa", resultado.passo_adicionado_nome)
        for arq in resultado.arquivos_criados:
            tabela.add_row("Arquivo Gerado/Atualizado", arq)

        console.print(tabela)
        console.print(Panel.fit(
            f"[bold green][OK] Módulo '{modulo}' incorporado com sucesso ao fluxo.yaml![/bold green]\n\n"
            f"[yellow]Próximos passos:[/yellow]\n"
            f"  pyrpa validate   (conferir a nova etapa)\n"
            f"  pyrpa run        (testar a execução)",
            border_style="green"
        ))

    except ModificadorProjetoException as exc:
        console.print(Panel(f"[bold red]Falha ao adicionar módulo:[/bold red]\n{exc}", border_style="red"))
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
    caminho = resolver_caminho_fluxo(caminho, operacao="Validação")
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
    caminho = resolver_caminho_fluxo(caminho, operacao="Execução")
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
    caminho = resolver_caminho_fluxo(caminho, operacao="Compilação")
    console.print(f"\n[bold blue]>> Compilando fluxo para Apache Airflow:[/bold blue] {caminho}")

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
