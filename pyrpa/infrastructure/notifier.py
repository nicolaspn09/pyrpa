from dataclasses import dataclass, field
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
from pathlib import Path
import smtplib
from typing import Any, Dict, List, Optional, Union
import urllib.request


@dataclass
class EmailConfig:
    """Configuração para disparo corporativo de e-mails via SMTP."""
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    remetente_padrao: Optional[str] = None

    @classmethod
    def from_env(cls) -> "EmailConfig":
        return cls(
            smtp_host=os.getenv("SMTP_HOST") or None,
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER") or None,
            smtp_password=os.getenv("SMTP_PASSWORD") or None,
            smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes"),
            remetente_padrao=os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or None,
        )


@dataclass
class NotifierConfig:
    """Configuração geral de mensageria corporativa (Webhooks e E-mail)."""
    webhook_url: Optional[str] = None
    timeout_segundos: int = 10
    email: EmailConfig = field(default_factory=EmailConfig.from_env)

    @classmethod
    def from_env(cls) -> "NotifierConfig":
        return cls(
            webhook_url=os.getenv("WEBHOOK_URL") or None,
            timeout_segundos=int(os.getenv("WEBHOOK_TIMEOUT", "10")),
            email=EmailConfig.from_env(),
        )


class NotifierAdapter:
    """
    Adaptador unificado para alertas e disparadores corporativos:
    - Webhooks JSON (Microsoft Teams, Slack, Discord).
    - E-mails transacionais com anexos e formatação HTML (SMTP).
    """

    def __init__(self, config: Optional[NotifierConfig] = None) -> None:
        self.config = config or NotifierConfig.from_env()

    # --- WEBHOOKS ---
    def enviar_alerta_webhook(self, titulo: str, mensagem: str, extras: Optional[Dict[str, Any]] = None) -> bool:
        """
        Envia payload formatado para o webhook corporativo configurado.
        Retorna False silenciosamente caso o webhook não tenha sido configurado no .env.
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

    # --- DISPARO DE E-MAIL ---
    def enviar_email(
        self,
        destinatarios: Union[str, List[str]],
        assunto: str,
        corpo_html: str,
        anexos: Optional[List[Union[str, Path]]] = None,
        remetente: Optional[str] = None,
    ) -> bool:
        """
        Dispara e-mail com suporte a corpo HTML e múltiplos arquivos anexos (ex: relatórios Excel, PDFs).
        Retorna False se o servidor SMTP não estiver configurado no .env.
        """
        email_cfg = self.config.email
        if not email_cfg.smtp_host:
            return False

        de = remetente or email_cfg.remetente_padrao or "pyrpa-bot@localhost"
        para = [destinatarios] if isinstance(destinatarios, str) else list(destinatarios)

        mensagem = MIMEMultipart()
        mensagem["From"] = de
        mensagem["To"] = ", ".join(para)
        mensagem["Subject"] = assunto

        mensagem.attach(MIMEText(corpo_html, "html", "utf-8"))

        # Anexar arquivos (relatórios Excel, logs, prints)
        if anexos:
            for caminho_anexo in anexos:
                path = Path(caminho_anexo).resolve()
                if path.is_file():
                    with path.open("rb") as f:
                        parte = MIMEBase("application", "octet-stream")
                        parte.set_payload(f.read())
                    encoders.encode_base64(parte)
                    parte.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{path.name}"',
                    )
                    mensagem.attach(parte)

        # Conexão e envio via SMTP
        with smtplib.SMTP(email_cfg.smtp_host, email_cfg.smtp_port, timeout=self.config.timeout_segundos) as server:
            if email_cfg.smtp_use_tls:
                server.starttls()
            if email_cfg.smtp_user and email_cfg.smtp_password:
                server.login(email_cfg.smtp_user, email_cfg.smtp_password)
            server.sendmail(de, para, mensagem.as_string())

        return True
