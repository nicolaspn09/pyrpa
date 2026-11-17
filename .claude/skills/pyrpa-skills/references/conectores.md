# Conectores de infraestrutura (pyrpa 0.1.0)

Os adaptadores vivem em `pyrpa.infrastructure.*` e o `init` cria em `infrastructure/` do robô um arquivo que os reexporta. No UseCase, importe sempre do projeto: `from infrastructure.<modulo> import ...`.

| Módulo (`add`) | Arquivo | Para quê | Pacotes extras |
|---|---|---|---|
| `web` | `infrastructure/browser.py` | Navegador (Playwright, Selenium, undetected-chromedriver) | playwright **ou** selenium **ou** undetected-chromedriver |
| `banco` | `infrastructure/database.py` | Banco SQL | SQLite: nenhum. Outros: sqlalchemy + driver |
| `excel` | `infrastructure/storage.py` | Excel, CSV, JSON, ZIP | pandas, openpyxl (Excel) |
| `pdf` | `infrastructure/pdf.py` | Texto e campos de PDF | pypdf |
| `ia` | `infrastructure/ai.py` | Consulta a modelos de linguagem | nenhum |
| `email` | `infrastructure/notifier.py` | E-mail (SMTP) e webhook | nenhum |
| (sempre) | `infrastructure/http_client.py` | Chamadas HTTP | nenhum |
| (sempre) | `infrastructure/logger.py` | Log de auditoria | nenhum |
| (domínio) | `pyrpa.domain.queue` | Fila de trabalho com tentativas | nenhum |

## Navegador, `infrastructure/browser.py`

```python
from infrastructure.browser import get_browser, BrowserConfig
cfg = BrowserConfig.from_env()            # lê o .env
with get_browser(cfg) as sessao:          # fecha o navegador sempre, mesmo com erro
    sessao.navegar("https://...")
    page = sessao.driver                  # Playwright Page ou Selenium WebDriver
```

- Variáveis do `.env`: `BROWSER_ENGINE` (`playwright` | `selenium` | `undetected_chromedriver` | `simulacao`; o `init` gera `simulacao`), `BROWSER_TYPE` (`chrome` | `firefox` | `edge`), `HEADLESS` (`true`/`false`), `BROWSER_TIMEOUT_MS` (padrão 15000), `BROWSER_SIMULACAO`.
- Métodos de `BrowserSession`: `navegar(url)`, `driver`, `esta_fechado`, `fechar()`. Cliques, preenchimento e leitura de texto usam o `driver`.
- Em modo `simulacao` o `driver` é só um dicionário: o navegador não abre.

## Banco, `infrastructure/database.py`

```python
from infrastructure.database import get_db_session
with get_db_session() as sessao:          # commit/rollback automáticos
    sessao.executar("INSERT INTO t (id, valor) VALUES (?, ?)", (1, 10.5))
    linhas = sessao.buscar_todos("SELECT * FROM t WHERE id = ?", (1,))   # lista de dicts
```

- `.env`: `DB_URL` (padrão `sqlite:///dados_rpa.db`), `DB_TIMEOUT`.
- Sempre **consulta parametrizada** (`?` e tupla de parâmetros). Nunca monte SQL concatenando texto do usuário.
- Somente SQLite é suportado sem pacotes extras; os demais bancos passam por SQLAlchemy.
- Nunca conecte em banco de produção durante a geração e os testes.

## Arquivos e planilhas, `infrastructure/storage.py`

```python
from pathlib import Path
from infrastructure.storage import StorageAdapter
st = StorageAdapter(Path.cwd())
st.salvar_json("dados.json", dados);  st.ler_json("dados.json")
st.salvar_csv("dados.csv", registros); st.ler_csv("dados.csv")
st.exportar_excel("relatorio.xlsx", registros, nome_aba="Dados")   # pandas + openpyxl
st.ler_excel(...);  st.ler_dados("arquivo.(xlsx|csv|json)")        # leitor universal
st.compactar_pasta("pasta", "saida.zip");  st.descompactar_zip("arq.zip")
```

`registros` é uma lista de dicionários. Relatórios Excel vão para a pasta de relatórios do projeto.

## PDF, `infrastructure/pdf.py`

```python
from infrastructure.pdf import PdfAdapter
pdf = PdfAdapter()
texto  = pdf.extrair_texto("nota.pdf")
paginas = pdf.extrair_paginas("nota.pdf")
campos = pdf.extrair_campos_padrao("nota.pdf")    # CNPJ, CPF, datas, valores em R$, linha digitável
```

Só PDFs com texto (não faz OCR de imagem escaneada). Erros viram `PdfExtracaoException`.

## IA, `infrastructure/ai.py`

```python
from infrastructure.ai import AiClientAdapter
ia = AiClientAdapter()                  # configuração do .env
resposta = ia.consultar("Resuma...", instrucao_sistema="Você é...")
categoria = ia.classificar(texto, ["fatura", "contrato", "outro"])
dados = ia.extrair_json(texto, {"cnpj": "str", "valor": "float"})
```

- `.env`: `AI_API_KEY` (ou `OPENAI_API_KEY`), `AI_MODEL` (padrão `gpt-4o-mini`), `AI_BASE_URL` (padrão OpenAI), `AI_TEMPERATURE`, `AI_TIMEOUT`, `AI_SIMULACAO`.
- Sem chave, o adaptador cai em **resposta simulada**. Se o resultado depender de IA, diga ao usuário que a resposta pode ser simulada.
- Nunca envie ao serviço de IA dados pessoais ou sigilosos reais sem o usuário confirmar que isso é permitido pela política da empresa.

## E-mail e webhook, `infrastructure/notifier.py`

```python
from infrastructure.notifier import NotifierAdapter
n = NotifierAdapter()
n.enviar_email(["destino@exemplo.com"], "Assunto", "<p>Corpo HTML</p>", anexos=["relatorio.xlsx"])
n.enviar_alerta_webhook("Título", "Mensagem")
```

- `.env`: `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_FROM`; `WEBHOOK_URL`, `WEBHOOK_TIMEOUT`.
- `enviar_email` devolve `False` se o SMTP não estiver configurado. **Trate esse retorno** (não considere o passo bem-sucedido se o e-mail não saiu).
- Em testes, use só endereços indicados pelo usuário para teste. Nunca dispare e-mail para destinatários reais sem confirmação.

## HTTP, `infrastructure/http_client.py`

```python
from infrastructure.http_client import HttpClientAdapter
http = HttpClientAdapter(timeout_padrao=30, max_retries=3)
resp = http.get("https://...", parametros={"q": "x"})
if resp.sucesso: dados = resp.json()
resp = http.post("https://...", json_dados={"a": 1})
```

Usa a biblioteca padrão, com tentativas automáticas. A URL vem do usuário.

## Log de auditoria, `infrastructure/logger.py`

```python
from infrastructure.logger import RPAAuditLogger
log = RPAAuditLogger(nome_robo="meu_robo")
log.info("..."); log.warning("..."); log.error("...", exc_info=True)
```

Gera log estruturado em JSON na pasta `logs/` do robô. Nunca registre senhas, tokens ou dados pessoais no log.

## Fila de trabalho, `pyrpa.domain.queue`

`FilaTrabalho` com `enfileirar`, `enfileirar_lote`, `proximo_pendente`, `marcar_sucesso`, `marcar_falha` (com número máximo de tentativas) e `obter_metricas`. Útil quando o robô processa uma lista de itens e precisa registrar sucesso e falha por item.

## `pyrpa add <modulo>`

Cria `infrastructure/<modulo>.py` (se faltar), um UseCase de **exemplo** em `application/<modulo>.py` e um passo novo no `fluxo.yaml`, e revalida. O código de exemplo é só um ponto de partida: substitua pela lógica real do pedido e confira a ordem do passo.
