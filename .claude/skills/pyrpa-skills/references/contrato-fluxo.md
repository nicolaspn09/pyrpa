# Contrato do `metadados/fluxo.yaml`

Validado por Pydantic v2 (`pyrpa/models/schema.py`). Violar qualquer regra faz o `pyrpa validate` falhar.

```yaml
fluxo:
  nome: "robo_cotacao"
  versao: "1.0.0"
  passos:
    - id: "passo_1"
      nome: "Buscar cotação do dólar"
      provider: "http"
      target: "application.buscar_cotacao.BuscarCotacaoUseCase"
    - id: "passo_2"
      nome: "Enviar cotação por e-mail"
      provider: "notifier"
      target: "application.enviar_email.EnviarEmailUseCase"
```

Indentação: 2 espaços para `fluxo:` → `nome`/`versao`/`passos`; `- id:` dentro de `passos` com 4 espaços e os demais campos do passo com 6 (como no arquivo gerado pelo `init`). Mantenha a indentação que já existe no arquivo.

## Campos

| Campo | Regra |
|---|---|
| `fluxo.nome` | apenas `[a-zA-Z0-9_-]` |
| `fluxo.versao` | formato `N.N.N` (padrão `1.0.0`) |
| `fluxo.passos` | lista com **pelo menos 1** passo |
| `passo.id` | apenas `[a-zA-Z0-9_-]`; **único** no arquivo. Continue a sequência `passo_N` a partir do maior N já usado |
| `passo.nome` | 3 a 100 caracteres; texto legível (aparece nos logs e na tabela do `run`) |
| `passo.provider` | um de: `playwright`, `selenium`, `undetected_chromedriver`, `pandas`, `database`, `pdf`, `ai`, `http`, `storage`, `notifier`, `custom`. Padrão: `custom`. **Nunca invente outro valor.** |
| `passo.target` | caminho de importação Python `pacote.modulo.Classe`, na forma `application.<arquivo>.<Classe>UseCase` |

## Qual `provider` usar

O `provider` descreve a ferramenta principal do passo. É informativo para logs e auditoria (o runner não muda de comportamento por causa dele).

| O passo principalmente... | provider |
|---|---|
| navega em site com Playwright / Selenium / undetected | `playwright` / `selenium` / `undetected_chromedriver` |
| lê ou grava planilha (Excel/CSV/JSON) com pandas | `pandas` (ou `storage` para arquivos/ZIP em geral) |
| lê ou grava em banco | `database` |
| extrai dados de PDF | `pdf` |
| consulta um modelo de IA | `ai` |
| chama uma API HTTP | `http` |
| envia e-mail ou webhook | `notifier` |
| aplica regra de negócio pura / outro | `custom` |

## Relação `target` ↔ arquivo

`application.buscar_cotacao.BuscarCotacaoUseCase` ⇒ arquivo `application/buscar_cotacao.py` com a classe `BuscarCotacaoUseCase`. O arquivo precisa existir e a classe precisa herdar `BaseUseCase`, senão o `run` falha em tempo de execução (o `validate` confere só o formato do `target`, não se o arquivo existe).

## Conferência antes de entregar

- IDs únicos e na ordem de execução desejada (a ordem do arquivo é a ordem de execução).
- Todo `target` tem seu arquivo `.py` correspondente.
- Nenhum passo de demonstração (`ExtrairDadosUseCase`, `ProcessarDadosUseCase`) sobrando, a menos que seja de fato usado.
- `pyrpa validate metadados/fluxo.yaml` sem erros.
