from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import traceback


class JsonEstruturadoFormatter(logging.Formatter):
    """
    Formatador de logs em JSON estruturado para observabilidade e governança em RPA.
    Inclui timestamp ISO-8601, nível, nome do robô, etapa atual e rastreio de exceção.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nivel": record.levelname,
            "robo": getattr(record, "robo", record.name),
            "etapa": getattr(record, "etapa", "geral"),
            "mensagem": record.getMessage(),
        }
        if record.exc_info:
            log_obj["excecao"] = "".join(traceback.format_exception(*record.exc_info)).strip()
        return json.dumps(log_obj, ensure_ascii=False)


class RPAAuditLogger:
    """
    Adaptador de logging estruturado que mantém o contexto da etapa atual do robô
    e grava simultaneamente no console e em arquivo de auditoria.
    """

    def __init__(
        self,
        nome_robo: str = "pyrpa_bot",
        nivel: str = "INFO",
        caminho_arquivo: Optional[Path] = None,
        formato_json: bool = False,
    ) -> None:
        self.nome_robo = nome_robo
        self.etapa_atual = "inicializacao"
        self.logger = logging.getLogger(f"pyrpa.{nome_robo}")
        self.logger.setLevel(getattr(logging, nivel.upper(), logging.INFO))
        self.logger.propagate = False

        if self.logger.handlers:
            self.logger.handlers.clear()

        formatter: logging.Formatter
        if formato_json:
            formatter = JsonEstruturadoFormatter()
        else:
            formatter = logging.Formatter(
                fmt="%(asctime)s | [%(levelname)s] | [%(etapa)s] | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        if caminho_arquivo is not None:
            caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(caminho_arquivo, encoding="utf-8")
            file_handler.setFormatter(JsonEstruturadoFormatter() if formato_json else formatter)
            self.logger.addHandler(file_handler)

    def definir_etapa(self, etapa: str) -> None:
        """Define o identificador da etapa em execução para enriquecer os registros de log."""
        self.etapa_atual = etapa

    def _extra(self, etapa: Optional[str] = None) -> Dict[str, str]:
        return {"robo": self.nome_robo, "etapa": etapa or self.etapa_atual}

    def info(self, mensagem: str, etapa: Optional[str] = None) -> None:
        self.logger.info(mensagem, extra=self._extra(etapa))

    def warning(self, mensagem: str, etapa: Optional[str] = None) -> None:
        self.logger.warning(mensagem, extra=self._extra(etapa))

    def error(self, mensagem: str, etapa: Optional[str] = None, exc_info: bool = False) -> None:
        self.logger.error(mensagem, extra=self._extra(etapa), exc_info=exc_info)

    def fechar(self) -> None:
        """Fecha e libera os handlers de arquivo abertos."""
        for handler in list(self.logger.handlers):
            handler.close()
            self.logger.removeHandler(handler)
