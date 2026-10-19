from dataclasses import dataclass
import json
import os
from typing import Any, Dict, Optional
import urllib.request


@dataclass
class NotifierConfig:
    """Configuração de alertas e webhooks corporativos carregada via .env."""
    webhook_url: Optional[str] = None
    timeout_segundos: int = 10

    @classmethod
    def from_env(cls) -> "NotifierConfig":
        return cls(
            webhook_url=os.getenv("WEBHOOK_URL") or None,
            timeout_segundos=int(os.getenv("WEBHOOK_TIMEOUT", "10")),
        )


class NotifierAdapter:
    """
    Adaptador de mensageria e alertas corporativos (Microsoft Teams, Slack, Discord ou Webhook genérico).
    Utiliza biblioteca padrão (urllib.request) para não impor dependências externas desnecessárias.
    """

    def __init__(self, config: Optional[NotifierConfig] = None) -> None:
        self.config = config or NotifierConfig.from_env()

    def enviar_alerta_webhook(self, titulo: str, mensagem: str, extras: Optional[Dict[str, Any]] = None) -> bool:
        """
        Envia um payload JSON para o webhook configurado.
        Se nenhuma URL estiver configurada, opera em modo silencioso retornando False.
        """
        if not self.config.webhook_url:
            return False

        payload = {
            "titulo": titulo,
            "mensagem": mensagem,
            "detalhes": extras or {},
        }
        dados_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.config.webhook_url,
            data=dados_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.config.timeout_segundos) as resp:
            return 200 <= resp.status < 300
