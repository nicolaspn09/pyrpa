import json
from pathlib import Path
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
from pyrpa.infrastructure.logger import RPAAuditLogger
from pyrpa.infrastructure.notifier import NotifierAdapter, NotifierConfig
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
            # Força erro de sintaxe SQL para provocar rollback da transação
            session.executar("INSTRUCAO_INVALIDA_SQL")

    with get_db_session(config) as session:
        registros = session.buscar_todos("SELECT * FROM contas")
        # O registro c2 não deve existir devido ao rollback
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


def test_notifier_adapter_silencioso_quando_sem_webhook():
    notifier = NotifierAdapter(NotifierConfig(webhook_url=None))
    resultado = notifier.enviar_alerta_webhook("Alerta", "Robô finalizou")
    assert resultado is False
