from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import List, Optional, Union
import yaml

from pyrpa.core.installer import registrar_dependencias_requirements
from pyrpa.core.validator import validar_arquivo_fluxo


class ModificadorProjetoException(Exception):
    """Exceção lançada em falhas ao adicionar novos módulos a um projeto existente."""
    pass


@dataclass
class ResultadoAdicaoModulo:
    nome_modulo: str
    arquivos_criados: List[str]
    passo_adicionado_id: str
    passo_adicionado_nome: str


MODULOS_SUPORTADOS = {"web", "banco", "excel", "pdf", "ia", "email"}


def adicionar_modulo_projeto(
    nome_modulo: str,
    diretorio_projeto: Optional[Union[str, Path]] = None
) -> ResultadoAdicaoModulo:
    """
    Adiciona um novo conector de infraestrutura e um caso de uso correspondente
    a um projeto RPA já existente, atualizando automaticamente o fluxo.yaml.
    """
    modulo_limpo = nome_modulo.strip().lower()
    if modulo_limpo not in MODULOS_SUPORTADOS:
        raise ModificadorProjetoException(
            f"Módulo desconhecido: '{nome_modulo}'. "
            f"Módulos suportados: {', '.join(sorted(MODULOS_SUPORTADOS))}."
        )

    raiz = Path(diretorio_projeto or Path.cwd()).resolve()
    caminho_fluxo = raiz / "metadados" / "fluxo.yaml"

    if not caminho_fluxo.is_file():
        raise ModificadorProjetoException(
            f"Projeto pyrpa não encontrado em '{raiz}'. "
            "Certifique-se de executar o comando dentro da pasta de um robô que contenha 'metadados/fluxo.yaml'."
        )

    # 1. Carrega o fluxo atual para inspecionar os passos existentes
    esquema = validar_arquivo_fluxo(caminho_fluxo)
    ids_existentes = {p.id for p in esquema.fluxo.passos}

    arquivos_criados = []

    # 2. Configurações específicas de cada módulo
    if modulo_limpo == "web":
        passo_base_id = "etapa_navegacao_web"
        passo_nome = "Navegação e Extração Web"
        provider = "playwright"
        target = "application.navegacao_web.NavegacaoWebUseCase"

        # Injeta adaptador de infra se não existir
        arquivo_infra = raiz / "infrastructure" / "browser.py"
        if not arquivo_infra.is_file():
            arquivo_infra.write_text(
                "from pyrpa.infrastructure.browser import BrowserConfig, BrowserSession, get_browser\n\n"
                "__all__ = ['BrowserConfig', 'BrowserSession', 'get_browser']\n",
                encoding="utf-8"
            )
            arquivos_criados.append("infrastructure/browser.py")

        # Injeta UseCase de exemplo
        arquivo_app = raiz / "application" / "navegacao_web.py"
        codigo_use_case = dedent("""
        from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
        from infrastructure.browser import get_browser, BrowserConfig
        from infrastructure.logger import RPAAuditLogger


        class NavegacaoWebUseCase(BaseUseCase):
            \"\"\"Caso de uso adicionado via 'pyrpa add web'.\"\"\"

            def __init__(self) -> None:
                self.logger = RPAAuditLogger(nome_robo="web")

            def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
                self.logger.info("Executando automação de navegação web...")
                config = BrowserConfig.from_env()

                with get_browser(config) as browser:
                    browser.navegar("https://google.com")
                    self.logger.info("Página inicial acessada com sucesso.")

                contexto.definir("web_status", "concluido")
                return ResultadoPasso(sucesso=True, mensagem="Navegação web concluída com êxito.")
        """).strip()
        arquivo_app.write_text(codigo_use_case, encoding="utf-8")
        arquivos_criados.append("application/navegacao_web.py")

    elif modulo_limpo == "banco":
        passo_base_id = "etapa_banco_dados"
        passo_nome = "Persistência em Banco de Dados"
        provider = "database"
        target = "application.banco_dados.BancoDadosUseCase"

        arquivo_infra = raiz / "infrastructure" / "database.py"
        if not arquivo_infra.is_file():
            arquivo_infra.write_text(
                "from pyrpa.infrastructure.database import DatabaseConfig, DatabaseSession, get_db_session\n\n"
                "__all__ = ['DatabaseConfig', 'DatabaseSession', 'get_db_session']\n",
                encoding="utf-8"
            )
            arquivos_criados.append("infrastructure/database.py")

        arquivo_app = raiz / "application" / "banco_dados.py"
        codigo_use_case = dedent("""
        from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
        from infrastructure.database import get_db_session
        from infrastructure.logger import RPAAuditLogger


        class BancoDadosUseCase(BaseUseCase):
            \"\"\"Caso de uso adicionado via 'pyrpa add banco'.\"\"\"

            def __init__(self) -> None:
                self.logger = RPAAuditLogger(nome_robo="banco")

            def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
                self.logger.info("Acessando banco de dados transacional...")
                with get_db_session() as session:
                    session.executar(
                        \"\"\"
                        CREATE TABLE IF NOT EXISTS log_eventos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            evento TEXT,
                            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        \"\"\"
                    )
                    session.executar("INSERT INTO log_eventos (evento) VALUES (?)", ("Execucao pyrpa add",))

                contexto.definir("banco_status", "gravado")
                return ResultadoPasso(sucesso=True, mensagem="Dados persistidos no banco com sucesso.")
        """).strip()
        arquivo_app.write_text(codigo_use_case, encoding="utf-8")
        arquivos_criados.append("application/banco_dados.py")

    elif modulo_limpo == "excel":
        passo_base_id = "etapa_gerar_excel"
        passo_nome = "Geração de Planilha Excel"
        provider = "storage"
        target = "application.planilha_excel.PlanilhaExcelUseCase"

        arquivo_infra = raiz / "infrastructure" / "storage.py"
        if not arquivo_infra.is_file():
            arquivo_infra.write_text(
                "from pyrpa.infrastructure.storage import StorageAdapter\n\n"
                "__all__ = ['StorageAdapter']\n",
                encoding="utf-8"
            )
            arquivos_criados.append("infrastructure/storage.py")

        arquivo_app = raiz / "application" / "planilha_excel.py"
        codigo_use_case = dedent("""
        from pathlib import Path
        from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
        from infrastructure.storage import StorageAdapter
        from infrastructure.logger import RPAAuditLogger


        class PlanilhaExcelUseCase(BaseUseCase):
            \"\"\"Caso de uso adicionado via 'pyrpa add excel'.\"\"\"

            def __init__(self) -> None:
                self.logger = RPAAuditLogger(nome_robo="excel")

            def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
                storage = StorageAdapter(Path.cwd())
                dados = [
                    {"codigo": "A1", "item": "Faturamento Servicos", "total": 15000.00},
                    {"codigo": "A2", "item": "Licenciamento RPA", "total": 4200.00},
                ]
                caminho = storage.exportar_excel("relatorio_pyrpa.xlsx", dados)
                self.logger.info(f"Planilha Excel gerada com sucesso em: {caminho}")

                contexto.definir("caminho_excel", str(caminho))
                return ResultadoPasso(
                    sucesso=True,
                    mensagem=f"Planilha gerada em: {caminho.name}",
                    dados={"arquivo": str(caminho)}
                )
        """).strip()
        arquivo_app.write_text(codigo_use_case, encoding="utf-8")
        arquivos_criados.append("application/planilha_excel.py")

    elif modulo_limpo == "pdf":
        passo_base_id = "etapa_leitura_pdf"
        passo_nome = "Extração de Dados em PDF"
        provider = "pdf"
        target = "application.leitura_pdf.LeituraPdfUseCase"

        arquivo_infra = raiz / "infrastructure" / "pdf.py"
        if not arquivo_infra.is_file():
            arquivo_infra.write_text(
                "from pyrpa.infrastructure.pdf import PdfAdapter, PdfExtracaoException\n\n"
                "__all__ = ['PdfAdapter', 'PdfExtracaoException']\n",
                encoding="utf-8"
            )
            arquivos_criados.append("infrastructure/pdf.py")

        arquivo_app = raiz / "application" / "leitura_pdf.py"
        codigo_use_case = dedent("""
        from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
        from infrastructure.pdf import PdfAdapter
        from infrastructure.logger import RPAAuditLogger


        class LeituraPdfUseCase(BaseUseCase):
            \"\"\"Caso de uso adicionado via 'pyrpa add pdf'.\"\"\"

            def __init__(self) -> None:
                self.logger = RPAAuditLogger(nome_robo="pdf")

            def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
                self.logger.info("Pronto para leitura de documentos fiscais e boletos em PDF.")
                adapter = PdfAdapter()
                # Exemplo: dados_pdf = adapter.extrair_campos_padrao('caminho_do_arquivo.pdf')

                contexto.definir("pdf_status", "pronto")
                return ResultadoPasso(sucesso=True, mensagem="Conector de PDF inicializado com sucesso.")
        """).strip()
        arquivo_app.write_text(codigo_use_case, encoding="utf-8")
        arquivos_criados.append("application/leitura_pdf.py")

    elif modulo_limpo == "ia":
        passo_base_id = "etapa_inteligencia_artificial"
        passo_nome = "Processamento Cognitivo com IA"
        provider = "ai"
        target = "application.processamento_ia.ProcessamentoIaUseCase"

        arquivo_infra = raiz / "infrastructure" / "ai.py"
        if not arquivo_infra.is_file():
            arquivo_infra.write_text(
                "from pyrpa.infrastructure.ai import AiClientAdapter, AiConfig, AiException\n\n"
                "__all__ = ['AiClientAdapter', 'AiConfig', 'AiException']\n",
                encoding="utf-8"
            )
            arquivos_criados.append("infrastructure/ai.py")

        arquivo_app = raiz / "application" / "processamento_ia.py"
        codigo_use_case = dedent("""
        from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
        from infrastructure.ai import AiClientAdapter
        from infrastructure.logger import RPAAuditLogger


        class ProcessamentoIaUseCase(BaseUseCase):
            \"\"\"Caso de uso adicionado via 'pyrpa add ia'.\"\"\"

            def __init__(self) -> None:
                self.logger = RPAAuditLogger(nome_robo="ia")

            def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
                self.logger.info("Acionando conector cognitivo de IA...")
                ai = AiClientAdapter()
                resposta = ai.consultar("Resuma a importância da padronização em RPA corporativo.")
                self.logger.info(f"Resposta obtida: {resposta[:60]}...")

                contexto.definir("ia_resposta", resposta)
                return ResultadoPasso(sucesso=True, mensagem="Processamento de IA concluído com êxito.")
        """).strip()
        arquivo_app.write_text(codigo_use_case, encoding="utf-8")
        arquivos_criados.append("application/processamento_ia.py")

    elif modulo_limpo == "email":
        passo_base_id = "etapa_envio_email"
        passo_nome = "Disparo de E-mail Corporativo"
        provider = "notifier"
        target = "application.envio_email.EnvioEmailUseCase"

        arquivo_infra = raiz / "infrastructure" / "notifier.py"
        if not arquivo_infra.is_file():
            arquivo_infra.write_text(
                "from pyrpa.infrastructure.notifier import NotifierConfig, NotifierAdapter, EmailConfig\n\n"
                "__all__ = ['NotifierConfig', 'NotifierAdapter', 'EmailConfig']\n",
                encoding="utf-8"
            )
            arquivos_criados.append("infrastructure/notifier.py")

        arquivo_app = raiz / "application" / "envio_email.py"
        codigo_use_case = dedent("""
        from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
        from infrastructure.notifier import NotifierAdapter
        from infrastructure.logger import RPAAuditLogger


        class EnvioEmailUseCase(BaseUseCase):
            \"\"\"Caso de uso adicionado via 'pyrpa add email'.\"\"\"

            def __init__(self) -> None:
                self.logger = RPAAuditLogger(nome_robo="email")

            def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
                self.logger.info("Preparando disparo de e-mail de notificação...")
                notifier = NotifierAdapter()
                # notifier.enviar_email(destinatarios="gestor@empresa.com", assunto="Robô Concluído", corpo_html="<p>OK</p>")

                contexto.definir("email_status", "notificado")
                return ResultadoPasso(sucesso=True, mensagem="Etapa de e-mail configurada com sucesso.")
        """).strip()
        arquivo_app.write_text(codigo_use_case, encoding="utf-8")
        arquivos_criados.append("application/envio_email.py")

    # 3. Garante ID único para a nova etapa no fluxo.yaml
    passo_final_id = passo_base_id
    contador = 2
    while passo_final_id in ids_existentes:
        passo_final_id = f"{passo_base_id}_{contador}"
        contador += 1

    # 4. Adiciona o passo no metadados/fluxo.yaml preservando formato
    dados_yaml = yaml.safe_load(caminho_fluxo.read_text(encoding="utf-8"))
    novo_passo_dict = {
        "id": passo_final_id,
        "nome": passo_nome,
        "provider": provider,
        "target": target,
    }
    dados_yaml["fluxo"]["passos"].append(novo_passo_dict)

    # Reescreve com formatação limpa e indentação padronizada de 2 espaços
    caminho_fluxo.write_text(yaml.dump(dados_yaml, allow_unicode=True, sort_keys=False), encoding="utf-8")
    arquivos_criados.append("metadados/fluxo.yaml (atualizado)")

    # 5. Atualiza requirements.txt e valida o fluxo com o validador oficial
    registrar_dependencias_requirements(raiz / "requirements.txt", {modulo_limpo})
    validar_arquivo_fluxo(caminho_fluxo)

    return ResultadoAdicaoModulo(
        nome_modulo=modulo_limpo,
        arquivos_criados=arquivos_criados,
        passo_adicionado_id=passo_final_id,
        passo_adicionado_nome=passo_nome,
    )
