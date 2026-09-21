from pathlib import Path
import re
from textwrap import dedent


class GeradorProjetoException(Exception):
    """Lançada quando ocorrem erros durante a geração do projeto RPA."""
    pass


def gerar_projeto_rpa(
    nome_projeto: str,
    destino: Path,
    forcar: bool = False
) -> Path:
    """
    Cria a árvore de diretórios e arquivos de um projeto RPA seguindo Clean Architecture.

    :param nome_projeto: Identificador do projeto (ex: robo_faturamento)
    :param destino: Caminho onde o projeto será criado
    :param forcar: Se True, permite sobrescrever diretório não vazio
    :return: Caminho do diretório raiz gerado
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", nome_projeto):
        raise GeradorProjetoException(
            f"Nome de projeto inválido: '{nome_projeto}'. "
            "Use apenas letras, números, sublinhados (_) ou hífens (-)."
        )

    raiz = Path(destino).resolve()

    if raiz.exists() and any(raiz.iterdir()) and not forcar:
        raise GeradorProjetoException(
            f"O diretório de destino '{raiz}' já existe e não está vazio. "
            "Use a opção de forçar sobrescrita (--forcar) se tiver certeza."
        )

    # Criação das pastas da Clean Architecture
    pastas = [
        raiz / "domain",
        raiz / "application",
        raiz / "infrastructure",
        raiz / "interfaces",
        raiz / "metadados",
    ]

    for pasta in pastas:
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "__init__.py").touch(exist_ok=True)

    # Geração do metadados/fluxo.yaml padrão (atendendo estritamente ao contrato)
    conteudo_fluxo = dedent(f"""
    fluxo:
        nome: "{nome_projeto}"
        versao: "1.0.0"
        passos:
        - id: "passo_1"
            nome: "Extrair Dados"
            provider: "playwright"
            target: "application.extracao.ExtrairDadosUseCase"
        - id: "passo_2"
            nome: "Processar Dados"
            provider: "pandas"
            target: "application.processamento.ProcessarDadosUseCase"
    """).strip()
    (raiz / "metadados" / "fluxo.yaml").write_text(conteudo_fluxo, encoding="utf-8")

    # Geração do requirements.txt inicial
    conteudo_requirements = dedent("""
    pyrpa>=0.1.0
    playwright>=1.40.0
    pandas>=2.0.0
    python-dotenv>=1.0.0
    """).strip()
    (raiz / "requirements.txt").write_text(conteudo_requirements, encoding="utf-8")

    # Geração do .env padrão
    conteudo_env = dedent("""
    # Configurações de Ambiente do Robô
    ENVIRONMENT=development
    LOG_LEVEL=INFO
    HEADLESS=true
    """).strip()
    (raiz / ".env").write_text(conteudo_env, encoding="utf-8")

    # Geração do .gitignore padrão
    conteudo_gitignore = dedent("""
    __pycache__/
    *.py[cod]
    .env
    .venv/
    logs/
    downloads/
    """).strip()
    (raiz / ".gitignore").write_text(conteudo_gitignore, encoding="utf-8")

    # Geração do main.py de entrada
    conteudo_main = dedent(f'''
    """
    Ponto de entrada do robô: {nome_projeto}
    Estruturado com Clean Architecture via framework pyrpa.
    """
    from pathlib import Path
    from pyrpa.core.validator import validar_arquivo_fluxo


    def main() -> None:
        caminho_fluxo = Path(__file__).parent / "metadados" / "fluxo.yaml"
        esquema = validar_arquivo_fluxo(caminho_fluxo)
        print(f"Iniciando execução do fluxo: {{esquema.fluxo.nome}} (v{{esquema.fluxo.versao}})")
        print(f"Total de etapas registradas: {{len(esquema.fluxo.passos)}}")


    if __name__ == "__main__":
        main()
    ''').strip()
    (raiz / "main.py").write_text(conteudo_main, encoding="utf-8")

    return raiz