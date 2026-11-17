# Camadas e UseCases

## Regra de dependência

```
interfaces ──▶ application ──▶ domain ◀── infrastructure
```

| Camada | Pode conter | Não pode |
|---|---|---|
| `domain/` | Regras de negócio **puras** (cálculo, validação, entidades). Funções e classes sem efeito colateral. | Ler/gravar arquivo, rede, banco, navegador. Importar bibliotecas externas (`requests`, `pandas`, `playwright`...). Importar `application` ou `infrastructure`. |
| `application/` | Um UseCase por passo (herda `BaseUseCase`). **Orquestra**: lê o contexto, chama `domain` e os adaptadores de `infrastructure`, grava o contexto, devolve `ResultadoPasso`. | Lógica de negócio (vai para `domain`). Chamar diretamente `playwright`, `selenium`, `pandas`, `sqlalchemy`, `pypdf`, `smtplib`. |
| `infrastructure/` | Tudo que toca o mundo externo: navegador, banco, arquivos, e-mail, HTTP, PDF, IA. | Regras de negócio. Importar `application`. |
| `interfaces/` | Pontos de entrada (terminal, webhook). | Regra de negócio. |

Os arquivos `infrastructure/*.py` gerados pelo `init` são **reexportações** dos adaptadores do pacote `pyrpa.infrastructure.*` (por exemplo, `infrastructure/storage.py` reexporta `StorageAdapter`). O UseCase importa dali: `from infrastructure.storage import StorageAdapter`.

## Contratos do framework (`pyrpa.domain.contracts`)

```python
from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
```

**`BaseUseCase`**: classe base abstrata. Implementar `executar(self, contexto: ContextoExecucao) -> ResultadoPasso`.

**`ResultadoPasso`**: `sucesso: bool`, `mensagem: str = ""`, `dados: dict | None`, `duracao_segundos: float` (o runner preenche a duração).

**`ContextoExecucao`**: estado compartilhado entre os passos.

| Método | Uso |
|---|---|
| `definir(chave, valor)` | grava (chave = string não vazia) |
| `obter(chave, padrao=None)` | lê, com padrão se não existir |
| `obter_obrigatorio(chave)` | lê; lança `ChaveContextoNaoEncontradaException` se um passo anterior não gravou |
| `contem(chave)` | verifica existência |
| `obter_todos()` | cópia de todos os dados |
| `historico_passos` | resultados dos passos já executados |

Sem variáveis globais entre passos: tudo passa pelo contexto.

## Como o runner trata o resultado

- `sucesso=True` → segue para o próximo passo.
- `sucesso=False` **ou** exceção no `executar` → o fluxo **para** e o `run` mostra a falha do passo.
- Se o `executar` devolver outra coisa que não `ResultadoPasso`, o runner trata como sucesso e guarda o retorno bruto: **não faça isso**, sempre devolva `ResultadoPasso`.

## Modelo de UseCase

Use `templates/usecase_modelo.py` como ponto de partida. Pontos obrigatórios:

1. Nome do arquivo em `snake_case` e da classe terminando em `UseCase`, batendo com o `target` do `fluxo.yaml`.
2. Docstring curta com as chaves do contexto que o passo **lê** e **grava**.
3. Logger de auditoria: `RPAAuditLogger(nome_robo="...")` (`info`, `warning`, `error`).
4. Falhas previstas viram `ResultadoPasso(sucesso=False, mensagem="...")` com mensagem útil para quem não programa. Evite engolir exceções com `except: pass`.
5. Recursos externos sempre com `with` (`get_browser`, `get_db_session`) para garantir o fechamento.

## Regra de negócio fica no `domain`

Exemplo: "só aceitar a cotação se a variação for menor que 5%".

```python
# domain/regras_cotacao.py  (puro, sem imports externos)
def variacao_aceitavel(valor_atual: float, valor_anterior: float, limite_percentual: float = 5.0) -> bool:
    if valor_anterior == 0:
        return False
    variacao = abs(valor_atual - valor_anterior) / valor_anterior * 100
    return variacao < limite_percentual
```

O UseCase só chama `variacao_aceitavel(...)`. Valores de negócio que podem mudar (o 5%, por exemplo) devem ser **parâmetros** (argumento, `.env` ou contexto), não números escondidos no meio do código.

## Site ou sistema específico: adaptador do projeto

Para interagir com uma página, crie um adaptador em `infrastructure/` com métodos de alto nível e use o `driver` do `BrowserSession` lá dentro (Playwright `page` ou Selenium `WebDriver`):

```python
# infrastructure/portal_cotacoes.py
from infrastructure.browser import get_browser, BrowserConfig

class PortalCotacoes:
    def obter_dolar(self) -> float:
        with get_browser(BrowserConfig.from_env()) as sessao:
            sessao.navegar("<URL informada pelo usuário>")
            page = sessao.driver            # Playwright: page.inner_text("...")
            texto = page.inner_text("#valor-dolar")
        return float(texto.replace(",", "."))
```

O UseCase chama `PortalCotacoes().obter_dolar()`. Assim, se o site mudar, só o adaptador muda (é a "localidade de mudança" que o framework busca). A URL e os seletores vêm do usuário: **nunca invente**. Se o motor for `simulacao`, o `driver` não é uma página real; avise o usuário e trate esse caso no adaptador ou rode com o motor correto.

## Passo a passo ao implementar um UseCase

1. Escreva (ou localize) a regra pura em `domain/` e teste-a rápido com dados fictícios.
2. Escreva o adaptador necessário em `infrastructure/`, se não bastar o do framework.
3. Escreva o UseCase em `application/`: ler contexto → chamar adaptador/regra → gravar contexto → devolver `ResultadoPasso`.
4. Registre o passo no `fluxo.yaml` e rode `pyrpa validate`.
5. Depois de todos os passos prontos, `pyrpa run` com dados de teste.
