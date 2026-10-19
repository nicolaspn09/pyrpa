from dataclasses import dataclass
import json
import time
from typing import Any, Dict, Optional, Union
import urllib.parse
import urllib.request
import urllib.error


@dataclass
class HttpResponse:
    """Resposta padronizada de chamadas HTTP para o ecossistema RPA."""
    status_code: int
    headers: Dict[str, str]
    corpo: str

    def json(self) -> Any:
        return json.loads(self.corpo)

    @property
    def sucesso(self) -> bool:
        return 200 <= self.status_code < 300


class HttpClientAdapter:
    """
    Cliente HTTP genérico com tratamento de retries automáticos e timeouts
    para consumo de APIs em automações RPA (ex: Receita Federal, CEP, ERPs, Webhooks).
    Utiliza biblioteca padrão (urllib) para dispensar dependências externas pesadas.
    """

    def __init__(self, timeout_padrao: int = 30, max_retries: int = 3) -> None:
        self.timeout_padrao = timeout_padrao
        self.max_retries = max_retries

    def requisitar(
        self,
        metodo: str,
        url: str,
        parametros: Optional[Dict[str, Any]] = None,
        json_dados: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> HttpResponse:
        cabecalhos = dict(headers or {})
        cabecalhos.setdefault("User-Agent", "pyrpa-bot/0.1.0")

        url_final = url
        if parametros:
            query_string = urllib.parse.urlencode(parametros)
            separador = "&" if "?" in url else "?"
            url_final = f"{url}{separador}{query_string}"

        dados_corpo: Optional[bytes] = None
        if json_dados is not None:
            cabecalhos["Content-Type"] = "application/json"
            dados_corpo = json.dumps(json_dados, ensure_ascii=False).encode("utf-8")

        tempo_limite = timeout or self.timeout_padrao

        tentativas = 0
        ultimo_erro: Optional[Exception] = None

        while tentativas < self.max_retries:
            tentativas += 1
            try:
                req = urllib.request.Request(
                    url_final,
                    data=dados_corpo,
                    headers=cabecalhos,
                    method=metodo.upper(),
                )
                with urllib.request.urlopen(req, timeout=tempo_limite) as resp:
                    corpo_str = resp.read().decode("utf-8", errors="replace")
                    headers_dict = {k: v for k, v in resp.headers.items()}
                    return HttpResponse(status_code=resp.status, headers=headers_dict, corpo=corpo_str)

            except urllib.error.HTTPError as exc:
                corpo_str = exc.read().decode("utf-8", errors="replace")
                headers_dict = {k: v for k, v in exc.headers.items()}
                # Se for erro transitório do servidor (502, 503, 504), tenta novamente
                if exc.code in {500, 502, 503, 504} and tentativas < self.max_retries:
                    time.sleep(1.0 * tentativas)
                    ultimo_erro = exc
                    continue
                return HttpResponse(status_code=exc.code, headers=headers_dict, corpo=corpo_str)

            except (urllib.error.URLError, TimeoutError) as exc:
                ultimo_erro = exc
                if tentativas < self.max_retries:
                    time.sleep(1.0 * tentativas)
                    continue
                raise ConnectionError(f"Falha de conexão com a API '{url}': {exc}") from exc

        raise ConnectionError(f"Falha na requisição HTTP após {self.max_retries} tentativas: {ultimo_erro}")

    def get(self, url: str, parametros: Optional[Dict[str, Any]] = None, **kwargs: Any) -> HttpResponse:
        return self.requisitar("GET", url, parametros=parametros, **kwargs)

    def post(self, url: str, json_dados: Optional[Any] = None, **kwargs: Any) -> HttpResponse:
        return self.requisitar("POST", url, json_dados=json_dados, **kwargs)
