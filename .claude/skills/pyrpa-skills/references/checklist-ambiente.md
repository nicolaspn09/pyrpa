# Checklist de ambiente

Objetivo: deixar o computador pronto **antes** de gerar ou rodar o robô, sem surpresas no meio do caminho.
O script `scripts/verificar_ambiente.py` executa estas verificações e imprime o comando de correção de cada item. Ele **só lê**: quem aplica as correções é você, depois do "ok" do usuário.

## Como usar

1. Rode o script com os módulos do pedido:
   ```
   python scripts/verificar_ambiente.py --modulos web,excel,email --projeto <pasta-do-robo>
   ```
   (`--projeto` é opcional; use quando o projeto já existe. `--engine selenium` troca o motor web; o padrão é `playwright`. `--json` devolve o resultado em JSON.)
2. Traduza o resultado para o usuário: o que está pronto, o que falta, por que precisa.
3. Peça **um "ok" para o conjunto**. Aplique os comandos na ordem abaixo, usando o Python do ambiente virtual.
4. Rode o script de novo e depois `pyrpa doctor`. Avance só sem `[FALTA]`.

Legenda: `[OK]` pronto · `[FALTA]` impede de seguir · `[AVISO]` não impede, mas merece atenção · `[INFO]` só informação.

## Itens, em ordem de correção

### A. Base

| # | Item | Como verificar | Se faltar |
|---|---|---|---|
| A1 | Python 3.11 ou superior | `python --version` | **Não instale por conta própria.** Explique ao usuário que precisa do Python 3.11+ (python.org ou o procedimento da empresa) e pare. |
| A2 | Ambiente virtual do projeto (`.venv`) | o script confere se está dentro de um venv | `python -m venv .venv`. Daí em diante, use `.venv\Scripts\python` (Windows) ou `.venv/bin/python` (Linux/macOS) em todos os comandos. |
| A3 | `pip` funcionando | `python -m pip --version` | `python -m ensurepip --upgrade` |

### B. O framework

| # | Item | Como verificar | Se faltar |
|---|---|---|---|
| B1 | `pyrpa` instalado | `pyrpa --version` | Instale a partir do repositório do framework: `python -m pip install -e <pasta-do-repositorio-pyrpa>` (se já está clonado) ou `python -m pip install git+https://github.com/nicolaspn09/pyrpa.git` (exige acesso ao repositório; o login é feito pelo usuário na janela do Git, nunca no chat). O pyrpa não está no PyPI: não use `pip install pyrpa`. |
| B2 | Versão do pyrpa conhecida | o script imprime a versão | Se for diferente de `0.1.0`, avise o usuário (a skill foi escrita para a 0.1.0). |
| B3 | Núcleo: `typer`, `rich`, `pydantic>=2`, `pyyaml`, `jinja2`, `python-dotenv` | importação | `python -m pip install typer rich "pydantic>=2" pyyaml jinja2 python-dotenv` (normalmente já vem com o pyrpa). |

### C. Pacotes por módulo (só os que o pedido usa)

| Módulo | Pacotes | Comando | Observação |
|---|---|---|---|
| `excel` | pandas, openpyxl | `python -m pip install pandas openpyxl` | Sem eles, `StorageAdapter.exportar_excel/ler_excel` falha. **O passo de demonstração do `init` também usa Excel.** |
| `pdf` | pypdf | `python -m pip install pypdf` | |
| `web` (Playwright, padrão) | playwright + navegador do Playwright | `python -m pip install playwright` e depois `python -m playwright install chromium` | Os navegadores do Playwright são baixados à parte (centenas de MB): avise o usuário antes. |
| `web` (Selenium) | selenium + navegador instalado no computador (Chrome, Edge ou Firefox) | `python -m pip install selenium` | O Selenium costuma baixar o driver sozinho; precisa de internet na primeira execução. |
| `web` (anti-detecção) | undetected-chromedriver + Chrome instalado | `python -m pip install undetected-chromedriver selenium` | Use só se o pedido exigir. |
| `banco` | SQLite já vem com o Python. Para PostgreSQL/SQL Server/MySQL: `sqlalchemy` + o driver do banco | `python -m pip install sqlalchemy` e o driver (ex.: `psycopg2-binary` para PostgreSQL, `pyodbc` para SQL Server) | Pergunte qual banco é antes de instalar o driver. |
| `ia` | nenhum pacote (usa a biblioteca padrão) | , | Precisa de chave no `.env` (ver D). |
| `email` | nenhum pacote (usa a biblioteca padrão) | , | Precisa de SMTP no `.env` (ver D). |
| HTTP | nenhum pacote | , | |

Dependências do projeto gerado: confira se `requirements.txt` do robô lista o que o pedido usa (o `init` já inclui pandas, openpyxl e pypdf; Playwright, Selenium e SQLAlchemy vêm comentados). Descomente ou acrescente **só o necessário**.

### D. Projeto e configuração (`--projeto`)

| # | Item | Como verificar | Se faltar |
|---|---|---|---|
| D1 | `metadados/fluxo.yaml` | arquivo existe e passa em `pyrpa validate` | Crie com `pyrpa init`, ou corrija o fluxo (passo 4 da skill). |
| D2 | `.env` na raiz do robô | arquivo existe | `pyrpa init` já o cria. Se faltar, crie a partir do modelo do passo 3. **Nunca** coloque o `.env` no Git (o `.gitignore` gerado já o ignora). |
| D3 | Chaves necessárias para os módulos usados | o script só informa **se a chave está preenchida, nunca o valor** | O **usuário** preenche. `email`: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` (e `SMTP_PORT`, `SMTP_FROM` se for o caso). `ia`: `AI_API_KEY` (ou `AI_SIMULACAO=true` para testar sem chave). `banco`: `DB_URL` (o padrão é um SQLite local). Webhook opcional: `WEBHOOK_URL`. |
| D4 | Modo de simulação do navegador | `BROWSER_ENGINE` no `.env` | O `init` gera `BROWSER_ENGINE=simulacao`: o navegador **não abre de verdade**. Para rodar de verdade, o motor deve ser `playwright`, `selenium` ou `undetected_chromedriver` (com `BROWSER_TYPE` = `chrome`, `edge` ou `firefox` e `HEADLESS=false` se o usuário quiser ver a tela). Pergunte antes de mudar. |

### E. Prova final

`pyrpa doctor` (rode dentro da pasta do robô para ele conferir também o projeto). Deve terminar sem `[FALHA]`. Avisos de conectores que o pedido **não** usa podem ser ignorados.

## Regras de ouro do checklist

- Instale **só** o que o diagnóstico apontou como `[FALTA]` para os módulos do pedido.
- Sempre com o Python do `.venv`. Nunca no Python global do computador.
- Um "ok" do usuário para o conjunto, mostrando a lista de pacotes e o tamanho aproximado dos downloads maiores (Playwright).
- Nada de segredo no chat. O usuário edita o `.env`.
- Se o computador não tiver acesso à internet ou ao repositório do pyrpa, pare e explique o que o usuário precisa pedir à equipe técnica.
