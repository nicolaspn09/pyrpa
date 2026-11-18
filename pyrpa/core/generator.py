from pathlib import Path
import re
from textwrap import dedent
from typing import List, Optional, Set, Union

from pyrpa.core.installer import gerar_conteudo_requirements


class GeradorProjetoException(Exception):
    """Lançada quando ocorrem erros durante a geração do projeto RPA."""
    pass


def normalizar_modulos(modulos: Optional[Union[str, List[str]]]) -> Set[str]:
    """Interpreta os módulos informados e retorna um conjunto padronizado."""
    if not modulos or modulos in ("completo", "all", "1"):
        return {"web", "banco", "excel", "pdf", "ia", "email"}
    if isinstance(modulos, str):
        return {m.strip().lower() for m in modulos.split(",") if m.strip()}
    return {str(m).strip().lower() for m in modulos if m}


def gerar_projeto_rpa(
    nome_projeto: str,
    destino: Path,
    forcar: bool = False,
    modulos: Optional[Union[str, List[str]]] = None,
) -> Path:
    """
    Cria a árvore de diretórios e arquivos de um projeto RPA seguindo Clean Architecture.

    :param nome_projeto: Identificador do projeto (ex: robo_faturamento)
    :param destino: Caminho onde o projeto será criado
    :param forcar: Se True, permite sobrescrever diretório não vazio
    :param modulos: Lista ou string de módulos selecionados (ex: 'web,banco', 'completo')
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

    mods_selecionados = normalizar_modulos(modulos)

    # Criação das pastas da Clean Architecture e governança
    pastas = [
        raiz / "domain",
        raiz / "application",
        raiz / "infrastructure",
        raiz / "interfaces",
        raiz / "metadados",
        raiz / "dags",
        raiz / "logs",
        raiz / "downloads",
        raiz / "relatorios",
    ]

    for pasta in pastas:
        pasta.mkdir(parents=True, exist_ok=True)
        if pasta.name in {"domain", "application", "infrastructure", "interfaces"}:
            (pasta / "__init__.py").touch(exist_ok=True)

    # 1. Camada DOMAIN: Entidades de negócio puro e gestão de filas
    conteudo_entities = dedent("""
    from dataclasses import dataclass, field
    from datetime import datetime, timezone
    from typing import Optional


    @dataclass
    class ItemProcessamento:
        \"\"\"Entidade de negócio representando um item processado pelo robô.\"\"\"
        id: str
        descricao: str
        valor: float
        status: str = "PENDENTE"
        data_registro: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """).strip()
    (raiz / "domain" / "entities.py").write_text(conteudo_entities, encoding="utf-8")

    # 2. Camada APPLICATION: Casos de uso de exemplo implementando BaseUseCase
    conteudo_extracao = dedent("""
    from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
    from infrastructure.logger import RPAAuditLogger


    class ExtrairDadosUseCase(BaseUseCase):
        \"\"\"Caso de uso responsável pela coleta e extração de dados do robô.\"\"\"

        def __init__(self) -> None:
            self.logger = RPAAuditLogger(nome_robo="extracao")

        def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
            self.logger.info("Iniciando extração de dados operacionais...")

            dados_coletados = [
                {"id": "DOC-101", "descricao": "Fatura Serviço Cloud", "valor": 1250.50},
                {"id": "DOC-102", "descricao": "Licença Software Antigravity", "valor": 890.00},
                {"id": "DOC-103", "descricao": "Manutenção Servidor Dedicado", "valor": 3400.00},
            ]

            contexto.definir("dados_extraidos", dados_coletados)
            self.logger.info(f"Extração concluída com {len(dados_coletados)} registros obtidos.")

            return ResultadoPasso(
                sucesso=True,
                mensagem=f"Foram extraídos {len(dados_coletados)} registros com sucesso.",
                dados={"total_registros": len(dados_coletados)}
            )
    """).strip()
    (raiz / "application" / "extracao.py").write_text(conteudo_extracao, encoding="utf-8")

    conteudo_processamento = dedent("""
    from pathlib import Path
    from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
    from infrastructure.database import get_db_session
    from infrastructure.logger import RPAAuditLogger
    from infrastructure.storage import StorageAdapter


    class ProcessarDadosUseCase(BaseUseCase):
        \"\"\"Caso de uso responsável pela validação, gravação em banco e exportação Excel.\"\"\"

        def __init__(self) -> None:
            self.logger = RPAAuditLogger(nome_robo="processamento")

        def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
            self.logger.info("Iniciando processamento e conciliação dos dados...")

            itens = contexto.obter("dados_extraidos", [])
            if not itens:
                return ResultadoPasso(
                    sucesso=False,
                    mensagem="Nenhum dado encontrado no contexto para processamento."
                )

            # 1. Persistência transacional demonstrativa no SQLite local
            with get_db_session() as session:
                session.executar(
                    \"\"\"
                    CREATE TABLE IF NOT EXISTS registros_processados (
                        id TEXT PRIMARY KEY,
                        descricao TEXT,
                        valor REAL,
                        data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    \"\"\"
                )
                for item in itens:
                    session.executar(
                        \"\"\"
                        INSERT OR REPLACE INTO registros_processados (id, descricao, valor)
                        VALUES (?, ?, ?)
                        \"\"\",
                        (item["id"], item["descricao"], item["valor"])
                    )

            # 2. Exportação demonstrativa para planilha Excel
            storage = StorageAdapter(Path.cwd())
            caminho_excel = storage.exportar_excel("relatorio_processamento.xlsx", itens)

            self.logger.info(f"Processamento concluído. Planilha gerada em: {caminho_excel}")
            return ResultadoPasso(
                sucesso=True,
                mensagem=f"Processados e exportados {len(itens)} itens para Excel.",
                dados={"itens_processados": len(itens), "arquivo_excel": str(caminho_excel)}
            )
    """).strip()
    (raiz / "application" / "processamento.py").write_text(conteudo_processamento, encoding="utf-8")

    # 3. Camada INFRASTRUCTURE: Adaptadores base injetados no robô
    conteudo_infra_logger = dedent("""
    from pyrpa.infrastructure.logger import RPAAuditLogger, JsonEstruturadoFormatter

    __all__ = ["RPAAuditLogger", "JsonEstruturadoFormatter"]
    """).strip()
    (raiz / "infrastructure" / "logger.py").write_text(conteudo_infra_logger, encoding="utf-8")

    conteudo_infra_db = dedent("""
    from pyrpa.infrastructure.database import DatabaseConfig, DatabaseSession, get_db_session

    __all__ = ["DatabaseConfig", "DatabaseSession", "get_db_session"]
    """).strip()
    (raiz / "infrastructure" / "database.py").write_text(conteudo_infra_db, encoding="utf-8")

    conteudo_infra_browser = dedent("""
    from pyrpa.infrastructure.browser import BrowserConfig, BrowserSession, get_browser

    __all__ = ["BrowserConfig", "BrowserSession", "get_browser"]
    """).strip()
    (raiz / "infrastructure" / "browser.py").write_text(conteudo_infra_browser, encoding="utf-8")

    conteudo_infra_storage = dedent("""
    from pyrpa.infrastructure.storage import StorageAdapter

    __all__ = ["StorageAdapter"]
    """).strip()
    (raiz / "infrastructure" / "storage.py").write_text(conteudo_infra_storage, encoding="utf-8")

    conteudo_infra_notifier = dedent("""
    from pyrpa.infrastructure.notifier import NotifierConfig, NotifierAdapter, EmailConfig

    __all__ = ["NotifierConfig", "NotifierAdapter", "EmailConfig"]
    """).strip()
    (raiz / "infrastructure" / "notifier.py").write_text(conteudo_infra_notifier, encoding="utf-8")

    conteudo_infra_http = dedent("""
    from pyrpa.infrastructure.http_client import HttpClientAdapter, HttpResponse

    __all__ = ["HttpClientAdapter", "HttpResponse"]
    """).strip()
    (raiz / "infrastructure" / "http_client.py").write_text(conteudo_infra_http, encoding="utf-8")

    conteudo_infra_pdf = dedent("""
    from pyrpa.infrastructure.pdf import PdfAdapter, PdfExtracaoException

    __all__ = ["PdfAdapter", "PdfExtracaoException"]
    """).strip()
    (raiz / "infrastructure" / "pdf.py").write_text(conteudo_infra_pdf, encoding="utf-8")

    conteudo_infra_ai = dedent("""
    from pyrpa.infrastructure.ai import AiClientAdapter, AiConfig, AiException

    __all__ = ["AiClientAdapter", "AiConfig", "AiException"]
    """).strip()
    (raiz / "infrastructure" / "ai.py").write_text(conteudo_infra_ai, encoding="utf-8")

    # 4. Geração do metadados/fluxo.yaml padrão (atendendo estritamente ao contrato)
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

    # 5. Geração do requirements.txt descomentado conforme módulos selecionados
    conteudo_requirements = gerar_conteudo_requirements(mods_selecionados)
    (raiz / "requirements.txt").write_text(conteudo_requirements, encoding="utf-8")

    # 6. Geração do .env padrão
    conteudo_env = dedent("""
    # Configurações de Ambiente do Robô
    ENVIRONMENT=development
    LOG_LEVEL=INFO
    HEADLESS=true
    BROWSER_ENGINE=simulacao
    BROWSER_TYPE=chrome
    DB_URL=sqlite:///dados_rpa.db

    # Disparo de Alertas e Notificações (Webhooks Microsoft Teams / Slack)
    # WEBHOOK_URL=https://webhook.site/seu-endpoint-corporativo

    # Disparo de E-mails com Anexos (SMTP Corporativo / Outlook / Gmail)
    # SMTP_HOST=smtp.office365.com
    # SMTP_PORT=587
    # SMTP_USER=seu_email@empresa.com.br
    # SMTP_PASSWORD=sua_senha_de_aplicativo
    # SMTP_USE_TLS=true
    # SMTP_FROM=seu_email@empresa.com.br

    # Inteligência Artificial em Automações Cognitivas (OpenAI / Groq / Ollama / DeepSeek)
    # AI_API_KEY=sua_chave_de_api
    # AI_MODEL=gpt-4o-mini
    # AI_BASE_URL=https://api.openai.com/v1
    """).strip()
    (raiz / ".env").write_text(conteudo_env, encoding="utf-8")

    # 7. Geração do .gitignore padrão
    conteudo_gitignore = dedent("""
    __pycache__/
    *.py[cod]
    .env
    .venv/
    logs/
    downloads/
    relatorios/
    *.db
    """).strip()
    (raiz / ".gitignore").write_text(conteudo_gitignore, encoding="utf-8")

    # 8. Geração do main.py de entrada com o Runner oficial
    conteudo_main = dedent(f'''
    """
    Ponto de entrada do robô: {nome_projeto}
    Estruturado com Clean Architecture e acionado via runner do framework pyrpa.
    """
    from pathlib import Path
    import sys

    from pyrpa.core.runner import FluxoRunner
    from pyrpa.core.validator import validar_arquivo_fluxo


    def main() -> None:
        raiz = Path(__file__).resolve().parent
        if str(raiz) not in sys.path:
            sys.path.insert(0, str(raiz))

        caminho_fluxo = raiz / "metadados" / "fluxo.yaml"
        esquema = validar_arquivo_fluxo(caminho_fluxo)
        print(f"Iniciando execução do fluxo: {{esquema.fluxo.nome}} (v{{esquema.fluxo.versao}})")
        print(f"Total de etapas registradas: {{len(esquema.fluxo.passos)}}")

        runner = FluxoRunner()
        resultado = runner.executar(caminho_fluxo, diretorio_projeto=raiz)

        if resultado.sucesso:
            print(f"\\n[SUCESSO] Robô finalizado com êxito em {{resultado.duracao_total_segundos}}s!")
        else:
            print(f"\\n[FALHA] Execução interrompida: {{resultado.erro}}")
            sys.exit(1)


    if __name__ == "__main__":
        main()
    ''').strip()
    (raiz / "main.py").write_text(conteudo_main, encoding="utf-8")

    return raiz
