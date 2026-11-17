---
name: pyrpa-skills
description: Cria, altera e executa automações RPA em Python com o framework pyrpa (Clean Architecture + fluxo.yaml) a partir de um pedido em linguagem natural. Antes de gerar código, confere e prepara o ambiente por um checklist (Python, venv, pyrpa, pacotes de cada módulo, navegador, .env). Depois cria o projeto com pyrpa init/add, implementa os UseCases (BaseUseCase, ContextoExecucao, ResultadoPasso), valida com pyrpa validate, executa com pyrpa run e, se pedido, compila para Airflow. Use quando o usuário pedir um robô/automação pyrpa, mencionar fluxo.yaml ou pyrpa, ou quiser preparar o computador para isso.
---

# pyrpa-skills

Versão da skill: **2.0**. Escrita sobre o pyrpa **0.1.0** (`origin/main`, commit `a47340c`: CLI com `init`, `add`, `validate`, `run`, `compile`, `info`, `doctor`).
Se o `pyrpa --version` for outro, avise o usuário antes de seguir: os nomes de comandos e contratos abaixo podem ter mudado.

A skill traduz um pedido em linguagem natural ("leia as notas em PDF e mande um resumo por e-mail") em um projeto pyrpa que respeita a arquitetura do framework. **Quem define a estrutura é o framework; a skill só conduz o assistente a usá-lo corretamente.** O usuário pode ser um analista sem conhecimento de Python: fale em português simples e evite jargão (veja "Como conversar").

## Arquivos desta skill

Leia cada um **no momento indicado**, não todos de uma vez.

| Arquivo | Quando ler |
|---|---|
| `references/checklist-ambiente.md` | Passo 2 (preparar o ambiente) |
| `scripts/verificar_ambiente.py` | Passo 2 (roda o checklist; só lê, não instala) |
| `references/contrato-fluxo.md` | Passo 4 (escrever o `fluxo.yaml`) |
| `references/camadas-e-usecases.md` | Passo 5 (implementar) |
| `references/conectores.md` | Passo 5, ao usar navegador, banco, Excel, PDF, IA, e-mail ou HTTP |
| `templates/usecase_modelo.py`, `templates/regra_dominio_modelo.py` | Passo 5 (ponto de partida) |

## Escopo

- Fluxos **sequenciais** de baixa complexidade (o `FluxoRunner` executa os passos na ordem do arquivo; não há ramificação nem paralelismo).
- Sem integrações que exijam credenciais que o usuário não tenha informado. Se o pedido exigir algo fora disso, diga claramente que a parte fica com a equipe técnica.
- Dados de teste sempre fictícios. Nunca use dados reais de empresa durante a geração.

## Fluxo de trabalho

Siga a ordem. Cada etapa existe por um motivo (ver "O que a skill nunca faz").

### 1. Entender e decompor o pedido

1. Decomponha o pedido em passos curtos e sequenciais, **cada um com uma única responsabilidade** (ex.: "buscar cotação" → "formatar mensagem" → "enviar e-mail"). Cada passo vira um UseCase.
2. Para cada passo, anote o **módulo** necessário: `web`, `banco`, `excel`, `pdf`, `ia`, `email`, ou nenhum (regra pura).
3. Se algo estiver ambíguo (fonte dos dados, formato da saída, destinatários, periodicidade), **pergunte antes de gerar código**, no máximo 3 perguntas por vez, com opções quando possível. Nunca invente credenciais, URLs de destino, endpoints, tokens ou e-mails.
4. Confirme a lista de passos com o usuário em linguagem simples antes de continuar.

### 2. Preparar o ambiente (checklist)

Leia `references/checklist-ambiente.md` e rode:

```
python <pasta-da-skill>/scripts/verificar_ambiente.py --modulos <lista> [--projeto <pasta>]
```

- `<lista>` são os módulos do passo 1, separados por vírgula (ex.: `web,excel,email`).
- O script **só diagnostica**: mostra cada item como `[OK]`, `[FALTA]` ou `[AVISO]` e o comando exato que resolve.
- Mostre ao usuário o resultado em linguagem simples (o que está pronto, o que falta e por que precisa).
- **Peça um único "ok" para o conjunto de ajustes** (ex.: "vou criar a pasta de ambiente isolado e instalar 3 pacotes: pandas, openpyxl, pypdf. Posso?") e só então execute os comandos propostos, **sempre dentro de um ambiente virtual do projeto** (`.venv`), nunca no Python global.
- Depois de aplicar, **rode o script de novo**, e em seguida `pyrpa doctor`. Só avance quando não restar nenhum `[FALTA]`. Se algo não puder ser resolvido por você (instalar o Python, navegador, liberar rede), explique o passo para o usuário e pare ali.
- Segredos (senha SMTP, chave de IA, string do banco) **nunca são pedidos no chat**. O usuário preenche o `.env` por conta própria; você só informa quais chaves precisam existir.

O checklist roda **em toda automação**, esteja o ambiente pronto ou não. Na primeira vez costuma haver itens `[FALTA]`; nas seguintes, normalmente tudo vem `[OK]`: então diga isso em uma linha ("ambiente já está pronto") e siga **sem pedir ok nem instalar nada**. Só se aplica correção ao que realmente faltar. Repita o checklist também quando um passo novo exigir um módulo novo.

### 3. Criar ou atualizar o projeto

- **Projeto novo:** `pyrpa init <nome> --destino <pasta> --modulos <lista>`.
  - **Sempre informe `--modulos`** (o `init` pergunta no terminal se faltar, o que trava a execução automatizada). Use só os módulos de que o pedido precisa; `completo` apenas se de fato todos forem usados.
  - O `init` cria **dois passos de demonstração** (`passo_1` Extrair Dados e `passo_2` Processar Dados, com dados fictícios, banco SQLite e planilha Excel). **Substitua-os pelos passos reais** e apague `application/extracao.py` e `application/processamento.py` se não forem usados. Nunca entregue um robô que ainda executa a demonstração.
- **Projeto existente** (já há `metadados/fluxo.yaml`): **não rode `init` de novo.** Para um módulo novo use `pyrpa add <web|banco|excel|pdf|ia|email>`; para passos próprios, edite o `fluxo.yaml` (passo 4). O `add` cria um UseCase **de exemplo** e um passo novo: edite o código para a lógica real e confira a posição do passo no fluxo.

### 4. Declarar os passos no `fluxo.yaml`

Leia `references/contrato-fluxo.md`. Em resumo: cada passo tem `id` único, `nome` (3 a 100 caracteres), `provider` (da lista do contrato) e `target` (`application.<arquivo>.<Classe>UseCase`). Respeite a indentação existente do arquivo.

### 5. Implementar os UseCases

Leia `references/camadas-e-usecases.md` (e `references/conectores.md` se usar um conector). Resumo da regra:

```
interfaces ──▶ application ──▶ domain ◀── infrastructure
```

- `domain/`: regras puras (cálculo, validação). Sem acesso a arquivo, rede ou banco, e sem bibliotecas externas.
- `application/`: um UseCase por passo, herdando `BaseUseCase`. **Orquestra**: chama `domain` e os adaptadores de `infrastructure`. Não contém chamadas diretas a `playwright`, `selenium`, `pandas`, `sqlalchemy` etc.
- `infrastructure/`: tudo que toca o mundo externo. Reutilize os adaptadores do pyrpa (`get_browser`, `get_db_session`, `StorageAdapter`, `PdfAdapter`, `AiClientAdapter`, `NotifierAdapter`, `HttpClientAdapter`, `RPAAuditLogger`). Para um site ou sistema específico, crie um adaptador do projeto (ex.: `infrastructure/portal_cotacoes.py`) com métodos de alto nível, e o UseCase chama esse método.
- Os passos se comunicam só pelo `ContextoExecucao` (`contexto.definir(...)`, `contexto.obter(...)`, `contexto.obter_obrigatorio(...)`). Documente na docstring de cada UseCase quais chaves ele **lê** e **grava**.
- Cada UseCase devolve um `ResultadoPasso(sucesso, mensagem, dados)`. Se `sucesso=False` ou se lançar exceção, o runner **interrompe o fluxo**.

### 6. Validar

```
pyrpa validate metadados/fluxo.yaml
```

Corrija todo erro apontado. Não entregue um fluxo que não passa.

Atenção: o `validate` confere o **formato** do `fluxo.yaml` (ids únicos, provider válido, `target` bem formado), mas **não** confere se o arquivo e a classe do `target` existem. Antes de seguir, confirme você mesmo que cada `target` tem o seu `.py` em `application/` com a classe herdando `BaseUseCase`; o erro só apareceria no `pyrpa run`.

### 7. Executar e conferir

```
pyrpa run metadados/fluxo.yaml
```

- O comando executa de verdade. Rode apenas com dados fictícios ou de teste, e só depois que o usuário confirmar que está tudo certo para executar.
- Confira a tabela de resultado (cada passo com `[OK]`/`[FALHA]`, duração e mensagem).
- O `pyrpa run` carrega automaticamente o `.env` do robô (via `python-dotenv`), então as chaves preenchidas ali já valem na execução.
- Se falhar por pacote ausente, volte ao passo 2.
- **Informe o que foi simulado.** O `.env` gerado traz `BROWSER_ENGINE=simulacao` (o navegador não abre de verdade) e o adaptador de IA cai em simulação sem chave. Se o resultado depender disso, diga ao usuário e explique o que precisa mudar no `.env` para rodar de verdade.

### 8. Compilar para o Airflow (somente se o usuário pedir)

```
pyrpa compile metadados/fluxo.yaml --schedule <manual|horario|diario|semanal|mensal|"expressão cron">
```

- **Sempre informe `--schedule`** (senão o comando pergunta no terminal).
- Gera `dags/dag_<nome>.py`. O Airflow não precisa estar instalado para compilar, e **você não instala o Airflow**. Publicar a DAG é responsabilidade da equipe técnica.

### 9. Entregar

Entregue um resumo curto, em linguagem simples:
1. O que o robô faz, passo a passo (nomes dos passos, sem jargão).
2. O que foi testado e com que resultado (`validate`, `run`).
3. O que foi simulado ou ficou pendente (ex.: "a chave da IA ainda não foi preenchida no `.env`").
4. Onde estão os arquivos e como rodar de novo (`pyrpa run`).
5. Versões usadas (a saída do script mostra Python e pyrpa), para o registro de reprodutibilidade.
6. Lembrete: a revisão da equipe técnica vem **antes** de qualquer uso em produção.

## O que a skill nunca faz

- Inventar credenciais, tokens, URLs de destino, endpoints ou dados externos: pergunta.
- Pedir senha, token ou chave no chat.
- Pular o checklist de ambiente, o `pyrpa validate` ou escrever o fluxo sem validar.
- Instalar pacotes fora de um ambiente virtual do projeto, ou sem o "ok" do usuário ao conjunto de ajustes.
- Rodar `pip install` de pacotes que o checklist não pediu.
- Colocar lógica de negócio em `infrastructure/`, ou acesso a rede/arquivo/banco em `domain/`.
- Importar `infrastructure` de dentro de `domain`, ou `application` de dentro de `domain`/`infrastructure`.
- Criar um UseCase "que faz tudo": um passo = uma responsabilidade.
- Deixar os passos de demonstração do `init` no robô entregue.
- Escrever um orquestrador próprio (`main.py` com laço de passos): a execução é do `pyrpa run`.
- Rodar `init` em pasta que já tem `metadados/fluxo.yaml`.
- Usar dados reais da empresa em testes, ou executar o robô contra sistemas de produção.
- Afirmar que algo "funciona" sem ter rodado `pyrpa validate` e `pyrpa run`; se não rodou, diga.

## Como conversar com o usuário

- Português simples, frases curtas. Troque: *UseCase* → "etapa do robô"; *fluxo.yaml* → "o roteiro do robô"; *venv* → "uma pasta de ambiente isolada para o robô"; *dependências* → "programas de apoio".
- Mostre o `fluxo.yaml` traduzido: "1) busca a cotação, 2) monta a mensagem, 3) envia o e-mail".
- No máximo 3 perguntas por vez, com opções. Peça "ok" explícito antes de instalar, de executar o robô e de qualquer ação com efeito externo (enviar e-mail, gravar em banco).
- Seja honesto sobre o que não foi testado ou falhou.

## Limitações conhecidas (pyrpa 0.1.0)

- Execução **sequencial**: sem ramificações, laços de fluxo ou paralelismo no `fluxo.yaml`.
- O `BrowserSession` expõe `navegar`, `driver` e `fechar`; interações na página (clicar, preencher, ler texto) usam o `driver` (Playwright `page` ou Selenium `WebDriver`). Não existe `extrair_texto` no navegador, embora o manual do desenvolvedor o cite.
- Catálogo do `pyrpa add`: `web`, `banco`, `excel`, `pdf`, `ia`, `email`. Outros casos usam `provider: custom` e adaptador próprio.
- Os adaptadores de IA e de e-mail só funcionam de verdade com a configuração correspondente no `.env`.
- A DAG do Airflow é gerada, mas esta skill não a publica nem a executa.
