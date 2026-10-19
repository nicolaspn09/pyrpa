import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from pyrpa.infrastructure.browser import (
    BrowserAdapterException,
    BrowserConfig,
    BrowserSession,
    get_browser,
)
from pyrpa.infrastructure.database import (
    DatabaseAdapterException,
    DatabaseConfig,
    get_db_session,
)
from pyrpa.infrastructure.http_client import HttpClientAdapter
from pyrpa.infrastructure.logger import RPAAuditLogger
from pyrpa.infrastructure.notifier import EmailConfig, NotifierAdapter, NotifierConfig
from pyrpa.infrastructure.storage import StorageAdapter


def test_logger_estruturado_deve_gravar_em_arquivo(tmp_path: Path):
    log_file = tmp_path / "logs" / "audit.log"
    logger = RPAAuditLogger(nome_robo="robo_teste", caminho_arquivo=log_file, formato_json=True)
    logger.definir_etapa("etapa_extracao")
    logger.info("Teste de auditoria RPA")
    logger.fechar()

    assert log_file.is_file()
    conteudo = log_file.read_text(encoding="utf-8").strip()
    log_json = json.loads(conteudo)
    assert log_json["robo"] == "robo_teste"
    assert log_json["etapa"] == "etapa_extracao"
    assert "Teste de auditoria RPA" in log_json["mensagem"]


def test_database_session_deve_executar_e_comitar(tmp_path: Path):
    db_file = tmp_path / "banco_teste.db"
    config = DatabaseConfig(db_url=f"sqlite:///{db_file}")

    with get_db_session(config) as session:
        session.executar("CREATE TABLE itens (id TEXT PRIMARY KEY, valor REAL)")
        session.executar("INSERT INTO itens (id, valor) VALUES (?, ?)", ("item_1", 99.5))

    with get_db_session(config) as session:
        registros = session.buscar_todos("SELECT * FROM itens")
        assert len(registros) == 1
        assert registros[0]["id"] == "item_1"
        assert registros[0]["valor"] == 99.5


def test_database_session_deve_fazer_rollback_em_erro(tmp_path: Path):
    db_file = tmp_path / "banco_rollback.db"
    config = DatabaseConfig(db_url=f"sqlite:///{db_file}")

    with get_db_session(config) as session:
        session.executar("CREATE TABLE contas (id TEXT PRIMARY KEY, saldo REAL)")
        session.executar("INSERT INTO contas (id, saldo) VALUES (?, ?)", ("c1", 100.0))

    with pytest.raises(DatabaseAdapterException):
        with get_db_session(config) as session:
            session.executar("INSERT INTO contas (id, saldo) VALUES (?, ?)", ("c2", 200.0))
            session.executar("INSTRUCAO_INVALIDA_SQL")

    with get_db_session(config) as session:
        registros = session.buscar_todos("SELECT * FROM contas")
        assert len(registros) == 1
        assert registros[0]["id"] == "c1"


def test_browser_session_modo_simulacao():
    config = BrowserConfig(engine="simulacao", browser_type="chrome", modo_simulacao=True)
    with get_browser(config) as browser:
        assert browser.esta_fechado is False
        browser.navegar("https://empresa.com.br/login")
        assert len(browser.historico_urls) == 1
        assert browser.historico_urls[0] == "https://empresa.com.br/login"

    assert browser.esta_fechado is True


def test_browser_session_deve_falhar_com_engine_invalido():
    config = BrowserConfig(engine="motor_inexistente", browser_type="chrome")
    with pytest.raises(BrowserAdapterException):
        with get_browser(config):
            pass


def test_storage_adapter_deve_salvar_e_ler_json_e_csv(tmp_path: Path):
    storage = StorageAdapter(tmp_path)
    dados_exemplo = {"cliente": "Empresa Alfa", "faturamento": 50000}

    caminho_json = storage.salvar_json("relatorio.json", dados_exemplo)
    assert caminho_json.is_file()
    recuperado = storage.ler_json("relatorio.json")
    assert recuperado["cliente"] == "Empresa Alfa"

    registros = [
        {"id": "1", "item": "A"},
        {"id": "2", "item": "B"},
    ]
    caminho_csv = storage.salvar_csv("dados.csv", registros)
    assert caminho_csv.is_file()
    lidos_csv = storage.ler_csv("dados.csv")
    assert len(lidos_csv) == 2
    assert lidos_csv[0]["item"] == "A"


def test_storage_adapter_exportar_e_ler_excel(tmp_path: Path):
    storage = StorageAdapter(tmp_path)
    registros = [
        {"codigo": "P01", "produto": "Teclado Mecânico", "preco": 350.0},
        {"codigo": "P02", "produto": "Monitor 27 pol", "preco": 1400.0},
    ]

    caminho_excel = storage.exportar_excel("produtos.xlsx", registros)
    assert caminho_excel.is_file()

    linhas = storage.ler_excel("produtos.xlsx")
    assert len(linhas) == 2
    assert linhas[0]["codigo"] == "P01"
    assert linhas[1]["preco"] == 1400.0

    # Leitor Universal com detecção automática de extensão
    lidos_universal = storage.ler_dados("produtos.xlsx")
    assert len(lidos_universal) == 2


def test_storage_adapter_zip_compactar_e_descompactar(tmp_path: Path):
    storage = StorageAdapter(tmp_path)

    pasta_arquivos = tmp_path / "arquivos_teste"
    pasta_arquivos.mkdir()
    (pasta_arquivos / "doc1.txt").write_text("conteudo 1", encoding="utf-8")
    (pasta_arquivos / "doc2.txt").write_text("conteudo 2", encoding="utf-8")

    caminho_zip = storage.compactar_pasta(pasta_arquivos, "pacote.zip")
    assert caminho_zip.is_file()

    pasta_extraida = storage.descompactar_zip(caminho_zip)
    assert (pasta_extraida / "doc1.txt").is_file()
    assert (pasta_extraida / "doc2.txt").is_file()


def test_notifier_adapter_silencioso_quando_sem_webhook():
    notifier = NotifierAdapter(NotifierConfig(webhook_url=None))
    resultado = notifier.enviar_alerta_webhook("Alerta", "Robô finalizou")
    assert resultado is False


def test_notifier_adapter_email_silencioso_sem_smtp():
    notifier = NotifierAdapter(NotifierConfig(email=EmailConfig(smtp_host=None)))
    resultado = notifier.enviar_email("destinatario@empresa.com", "Assunto", "<b>Corpo</b>")
    assert resultado is False


def test_notifier_adapter_email_envio_com_mock(tmp_path: Path):
    cfg = NotifierConfig(
        email=EmailConfig(
            smtp_host="smtp.empresa.com",
            smtp_port=587,
            smtp_user="bot@empresa.com",
            smtp_password="senha",
            smtp_use_tls=True,
        )
    )
    notifier = NotifierAdapter(cfg)

    anexo = tmp_path / "planilha.xlsx"
    anexo.write_text("dados fake", encoding="utf-8")

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_instance

        sucesso = notifier.enviar_email(
            destinatarios=["gestor@empresa.com"],
            assunto="Relatório de Faturamento RPA",
            corpo_html="<p>Segue relatório em anexo.</p>",
            anexos=[anexo],
        )

        assert sucesso is True
        mock_instance.starttls.assert_called_once()
        mock_instance.login.assert_called_once_with("bot@empresa.com", "senha")
        mock_instance.sendmail.assert_called_once()


def test_http_client_adapter_consulta():
    client = HttpClientAdapter(timeout_padrao=5)
    # Teste com URL inexistente tratada com erro de conexão
    with pytest.raises(ConnectionError):
        client.get("http://localhost:59999/api/inexistente", timeout=1)
