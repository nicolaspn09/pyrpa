from dataclasses import dataclass
import json
import os
import re
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error


class AiException(Exception):
    """Exceção lançada em falhas de comunicação ou processamento cognitivo via IA."""
    pass


@dataclass
class AiConfig:
    """Configuração para integração com modelos de linguagem (LLMs) em automações cognitivas."""
    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.0
    timeout_segundos: int = 30
    modo_simulacao: bool = False

    @classmethod
    def from_env(cls) -> "AiConfig":
        key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY") or None
        simulacao = os.getenv("AI_SIMULACAO", "false").lower() in ("true", "1", "yes")
        # Se nenhuma chave foi fornecida no ambiente, entra em modo simulação automaticamente
        if not key:
            simulacao = True
        return cls(
            api_key=key,
            model=os.getenv("AI_MODEL", "gpt-4o-mini"),
            base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1"),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.0")),
            timeout_segundos=int(os.getenv("AI_TIMEOUT", "30")),
            modo_simulacao=simulacao,
        )


class AiClientAdapter:
    """
    Adaptador de Inteligência Artificial para Automações Cognitivas (RPA + IA).
    Permite classificação de textos/e-mails, extração estruturada de documentos
    e tomada de decisão com prompts declarativos.
    """

    def __init__(self, config: Optional[AiConfig] = None) -> None:
        self.config = config or AiConfig.from_env()

    def consultar(self, prompt: str, instrucao_sistema: Optional[str] = None) -> str:
        """Envia uma mensagem direta ao modelo de IA e retorna a resposta textual."""
        if self.config.modo_simulacao or not self.config.api_key:
            return f"[SIMULAÇÃO IA] Resposta gerada para: {prompt[:40]}..."

        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        mensagens = []
        if instrucao_sistema:
            mensagens.append({"role": "system", "content": instrucao_sistema})
        mensagens.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model,
            "messages": mensagens,
            "temperature": self.config.temperature,
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.config.timeout_segundos) as resp:
                dados = json.loads(resp.read().decode("utf-8"))
                return dados["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            raise AiException(f"Erro na chamada da API de IA ({self.config.model}): {exc}") from exc

    def classificar(self, texto: str, categorias: List[str]) -> str:
        """
        Classifica um texto livre (ex: e-mail, chamado, reclamação)
        em uma das categorias predefinidas para decisão de fluxo no robô.
        """
        if self.config.modo_simulacao or not self.config.api_key:
            return categorias[0] if categorias else "INDEFINIDO"

        prompt = (
            f"Analise o texto a seguir e classifique-o EXATAMENTE em uma das seguintes categorias: "
            f"{', '.join(categorias)}.\n"
            f"Responda APENAS com o nome exato da categoria escolhida, sem pontuação ou comentários.\n\n"
            f"Texto: \"{texto}\""
        )
        resposta = self.consultar(prompt, instrucao_sistema="Você é um classificador rigoroso de processos corporativos.")
        for cat in categorias:
            if cat.lower() in resposta.lower():
                return cat
        return categorias[0]

    def extrair_json(self, texto: str, schema_esperado: Dict[str, str]) -> Dict[str, Any]:
        """
        Extrai informações estruturadas de textos não-padronizados (ex: PDFs, e-mails, notas)
        retornando um dicionário Python estritamente tipado.
        """
        if self.config.modo_simulacao or not self.config.api_key:
            # Em modo simulação/testes, gera um dicionário de exemplo baseado no schema esperado
            return {campo: f"[Valor Extraído: {tipo}]" for campo, tipo in schema_esperado.items()}

        prompt = (
            f"Extraia as informações do texto abaixo seguindo estritamente a estrutura JSON solicitada.\n"
            f"Campos esperados e seus tipos/descrições:\n"
            f"{json.dumps(schema_esperado, indent=2, ensure_ascii=False)}\n\n"
            f"Retorne APENAS o objeto JSON válido, sem marcadores markdown adicionais.\n\n"
            f"Texto de entrada:\n\"{texto}\""
        )
        resposta = self.consultar(prompt, instrucao_sistema="Você é um extrator de dados estruturados que responde exclusivamente em formato JSON.")

        # Limpa possíveis blocos markdown ```json
        resposta_limpa = re.sub(r"^```(?:json)?\s*", "", resposta.strip(), flags=re.MULTILINE)
        resposta_limpa = re.sub(r"```$", "", resposta_limpa.strip(), flags=re.MULTILINE)

        try:
            return json.loads(resposta_limpa)
        except json.JSONDecodeError as exc:
            raise AiException(f"O modelo não retornou um JSON válido: {resposta}") from exc
