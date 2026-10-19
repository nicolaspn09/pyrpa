from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, Generator, List, Optional, Tuple


class DatabaseAdapterException(Exception):
    """Exceção lançada em falhas de conexão ou transação de banco de dados."""
    pass


@dataclass
class DatabaseConfig:
    """Configuração de conexão carregada a partir de variáveis de ambiente (.env)."""
    db_url: str = "sqlite:///dados_rpa.db"
    timeout_segundos: int = 30

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        url = os.getenv("DB_URL", "sqlite:///dados_rpa.db")
        timeout = int(os.getenv("DB_TIMEOUT", "30"))
        return cls(db_url=url, timeout_segundos=timeout)


class DatabaseSession:
    """
    Sessão transacional unificada para operações SQL em automações RPA.
    Suporta SQLite nativo (zero dependências externas) e motores SQLAlchemy (PostgreSQL, SQL Server, MySQL).
    """

    def __init__(self, conexao: Any, eh_sqlalchemy: bool = False) -> None:
        self._conexao = conexao
        self._eh_sqlalchemy = eh_sqlalchemy
        self._cursor: Optional[ sqlite3.Cursor ] = None

    def executar(self, query: str, parametros: Tuple[Any, ...] = ()) -> Any:
        """Executa uma instrução SQL parametrizada de forma segura contra SQL Injection."""
        if self._eh_sqlalchemy:
            from sqlalchemy import text
            return self._conexao.execute(text(query), parametros)
        self._cursor = self._conexao.cursor()
        self._cursor.execute(query, parametros)
        return self._cursor

    def buscar_todos(self, query: str, parametros: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        """Executa um SELECT e retorna os registros como lista de dicionários."""
        cursor = self.executar(query, parametros)
        if self._eh_sqlalchemy:
            colunas = list(cursor.keys())
            return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
        colunas = [col[0] for col in (cursor.description or [])]
        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]

    def commit(self) -> None:
        self._conexao.commit()

    def rollback(self) -> None:
        self._conexao.rollback()

    def fechar(self) -> None:
        self._conexao.close()


@contextmanager
def get_db_session(
    config: Optional[DatabaseConfig] = None,
) -> Generator[DatabaseSession, None, None]:
    """
    Context Manager transacional (with get_db_session() as session:).
    Garante commit automático em caso de sucesso, rollback imediato em exceções
    e fechamento determinístico da conexão no bloco finally.
    """
    cfg = config or DatabaseConfig.from_env()
    url = cfg.db_url

    sessao: Optional[DatabaseSession] = None
    try:
        if url.startswith("sqlite:///") or url == ":memory:":
            caminho_db = ":memory:" if url == ":memory:" else url.replace("sqlite:///", "", 1)
            if caminho_db != ":memory:":
                Path(caminho_db).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(caminho_db, timeout=cfg.timeout_segundos)
            sessao = DatabaseSession(conn, eh_sqlalchemy=False)
        else:
            try:
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
            except ImportError as exc:
                raise DatabaseAdapterException(
                    "Para conectar a bancos corporativos externos (PostgreSQL/SQLServer/MySQL), "
                    "instale o pacote 'sqlalchemy' no ambiente."
                ) from exc
            engine = create_engine(url, pool_pre_ping=True)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            sessao = DatabaseSession(SessionLocal(), eh_sqlalchemy=True)

        yield sessao
        sessao.commit()
    except DatabaseAdapterException:
        if sessao is not None:
            sessao.rollback()
        raise
    except Exception as exc:
        if sessao is not None:
            sessao.rollback()
        raise DatabaseAdapterException(f"Erro na transação de banco de dados: {exc}") from exc
    finally:
        if sessao is not None:
            sessao.fechar()
