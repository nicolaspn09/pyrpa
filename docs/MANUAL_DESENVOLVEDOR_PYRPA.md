# Manual do Desenvolvedor - pyrpa

> **Framework de Scaffolding, Clean Architecture e Orquestração Declarativa para RPA Corporativo**  
> *IFSC - Câmpus Tubarão | Análise e Desenvolvimento de Sistemas | TCC II*  
> *Autores: Kauê Cunha Baesso e Nícolas Paulo Nasário*  
> *Orientador: Prof. Tiago Guimarães Moraes*

---

## 1. Visão Geral

O **`pyrpa`** é um framework opinativo em Python (>= 3.10) projetado para resolver a fragilidade técnica, o acoplamento excessivo e a falta de padronização no desenvolvimento de Robôs de Automação de Processos (RPA).

### Pilares Fundamentais:
1. **Clean Architecture Obrigatória**: O domínio do robô (`domain/`) e os casos de uso (`application/`) nunca importam ou dependem diretamente de bibliotecas de automação ou bancos de dados (`infrastructure/`).
2. **Orquestração Declarativa em YAML**: Todo fluxo de execução é descrito em um contrato rigoroso em `metadados/fluxo.yaml`, validado por schemas Pydantic v2.
3. **Compilação Nativa para Apache Airflow**: Qualquer robô desenvolvido localmente pode ser compilado em uma DAG de produção (`dags/dag_<nome>.py`) com agendamento Cron automático.
4. **Resiliência e Governança**: Fechamento garantido de navegadores (sem processos órfãos do Chrome), transações de banco com rollback automático e log estruturado em JSON para auditoria.

---

## 2. Guia de Comandos e Opções da CLI

A CLI do `pyrpa` foi desenhada para ser intuitiva, rápida e totalmente em português. Ela suporta tanto subcomandos diretos quanto flags com traço duplo (`--`), atendendo a diferentes preferências de digitação.

### 2.0. Flags Globais e Atalhos
* `pyrpa --version` ou `pyrpa -v`: Exibe a versão instalada do framework.
* `pyrpa --help`: Exibe a lista completa de comandos e opções disponíveis.
* `pyrpa --info`: Atalho para abrir o catálogo interativo de conectores e módulos.
* `pyrpa --doctor`: Atalho para rodar a varredura de saúde do ambiente.
* `pyrpa --validate`: Atalho para validar o `metadados/fluxo.yaml` do projeto atual.
* `pyrpa --run`: Atalho para executar o fluxo do projeto atual.
* `pyrpa --compile`: Atalho para compilar o fluxo do projeto atual para Apache Airflow.

---

### 2.1. `pyrpa info` (ou `pyrpa --info`)
Exibe o catálogo interativo de todos os conectores disponíveis, tecnologias integradas, casos de uso corporativos e tabela rápida de comandos.

```bash
pyrpa info
# ou
pyrpa --info
```

---

### 2.2. `pyrpa doctor` (ou `pyrpa --doctor`)
Realiza uma varredura completa na máquina e no ambiente virtual do Python, verificando:
- Versão do interpretador Python (>= 3.10).
- Presença dos binários de navegadores instalados no host (Google Chrome/Chromium, Microsoft Edge, Mozilla Firefox em Windows, Linux e macOS).
- Pacotes de núcleo instalados (Typer, Rich, Pydantic, PyYAML, Python-Dotenv).
- Conectores opcionais instalados (Playwright, Selenium, SQLAlchemy, Pandas, PyPDF, OpenAI).
- Validade do projeto local (se executado dentro de uma pasta de robô).

```bash
pyrpa doctor
# ou
pyrpa --doctor
```

---

### 2.3. `pyrpa init <nome_do_projeto>`
Inicializa um novo robô com a estrutura de Clean Architecture pronta para execução.

#### Modos de uso:
1. **Modo Interativo** (quando chamado sem flags):
   O assistente pergunta no terminal quais tecnologias o robô precisará utilizar.
   ```bash
   pyrpa init meu_robo
   ```

2. **Modo Rápido com a flag `--modulos` ou `-m`**:
   Permite informar diretamente quais módulos incluir:
   ```bash
   # Robô focado apenas em banco de dados
   pyrpa init robo_financeiro -m banco

   # Robô com Web e Banco de Dados
   pyrpa init robo_compras -m web,banco

   # Robô completo com todos os conectores (Web, Banco, Excel, PDF, IA, E-mail)
   pyrpa init robo_completo -m completo
   ```

3. **Opções adicionais**:
   - `--destino` ou `-d`: Especifica uma pasta customizada para a geração do projeto.
   - `--forcar` ou `-f`: Permite sobrescrever arquivos se a pasta já existir.
   - `--sem-instalar`: Pula a verificação/instalação automática de dependências via `pip`.

> **Instalação Automática:** ao finalizar a criação das pastas e gerar o `requirements.txt` descomentado com os módulos escolhidos, o `pyrpa init` verifica e instala automaticamente qualquer biblioteca faltante no ambiente Python ativo.

---

### 2.4. `pyrpa add <modulo>`
Adiciona dinamicamente um novo conector de infraestrutura e um caso de uso correspondente a um projeto já existente, **sem quebrar o fluxo.yaml** ou os passos anteriores.

Módulos suportados: `web`, `banco`, `excel`, `pdf`, `ia`, `email`.

```bash
# Entra na pasta do seu robô existente
cd meu_robo

# Adiciona o leitor e extrator de PDFs
pyrpa add pdf

# Adiciona conector para modelos de Inteligência Artificial (LLMs)
pyrpa add ia

# Adiciona gerador de planilhas Excel formatadas
pyrpa add excel
```

O comando realiza automaticamente:
1. Injeção do adaptador base em `infrastructure/<modulo>.py`.
2. Criação do caso de uso de exemplo em `application/<modulo>.py`.
3. Inclusão da nova etapa com ID único e provider correto no `metadados/fluxo.yaml`.
4. Revalidação estrutural de todo o contrato do robô.

---

### 2.5. `pyrpa validate [caminho_do_fluxo]`
Valida a integridade do arquivo `fluxo.yaml` contra o schema Pydantic v2 do framework.

```bash
pyrpa validate metadados/fluxo.yaml
```

Verifica:
- Validade da sintaxe YAML.
- Unicidade estrita dos identificadores das etapas (`id`).
- Provedores suportados (`playwright`, `selenium`, `database`, `storage`, `pdf`, `ai`, `notifier`, `custom`).
- Caminhos canônicos dos UseCases em `target`.

---

### 2.6. `pyrpa run [caminho_do_fluxo]`
Executa localmente o fluxo do robô conforme definido no `fluxo.yaml`.

```bash
pyrpa run metadados/fluxo.yaml
```

Recursos do motor de execução (`FluxoRunner`):
- Carregamento automático das variáveis do arquivo `.env` específico do robô antes da execução.
- Instanciação dinâmica dos UseCases via `importlib`.
- Objeto de estado compartilhado (`ContextoExecucao`) que trafega dados entre etapas de forma desacoplada.
- Cronometragem detalhada de cada etapa e exibição de resumo visual via Rich.
- Log de auditoria estruturado registrando tempo, usuário e desfecho de cada etapa.

---

### 2.7. `pyrpa compile [caminho_do_fluxo]`
Lê o contrato `fluxo.yaml` e compila automaticamente uma DAG pronta para deploy no **Apache Airflow**.

```bash
# Pergunta interativamente a periodicidade (Diário, Horário, Semanal, etc.)
pyrpa compile metadados/fluxo.yaml

# Passa a periodicidade diretamente via linha de comando
pyrpa compile metadados/fluxo.yaml --schedule diario
pyrpa compile metadados/fluxo.yaml -s "0 8 * * *"
```

Periodicidades reconhecidas:
- `manual` -> `None` (execução sob demanda)
- `horario` -> `"0 * * * *"` (a cada hora cheia)
- `diario` -> `"0 8 * * *"` (todos os dias às 08:00)
- `semanal` -> `"0 8 * * 1"` (segundas-feiras às 08:00)
- `mensal` -> `"0 8 1 * *"` (dia 1º de cada mês às 08:00)
- Qualquer expressão cron válida (ex: `"*/15 * * * *"`).

---

### 2.8. Assistente Inteligente de Navegação de Pastas
Se qualquer comando de execução, validação ou compilação for acionado de fora da pasta do robô (por exemplo, na pasta pai `Downloads` ou em uma pasta raiz corporativa):
1. O `pyrpa` **não trava** com um erro genérico.
2. Ele varre o diretório atual, identifica os robôs existentes e sugere o comando exato de entrada (`cd <nome_do_robo>`).
3. Também sugere a linha de comando alternativa apontando diretamente para o caminho relativo.

---

## 3. Conectores e Adaptadores de Infraestrutura

Todos os conectores de infraestrutura foram criados seguindo o princípio da **Programação Defensiva** e gerenciamento estrito de recursos:

| Conector | Arquivo Base | Principais Recursos |
| :--- | :--- | :--- |
| **Web** | `infrastructure/browser.py` | Suporte a Playwright, Selenium, Undetected-Chromedriver e modo Simulação (`BROWSER_ENGINE`). Context manager `with get_browser() as browser:` com encerramento forçado do processo ao sair do bloco. |
| **Banco de Dados** | `infrastructure/database.py` | Conexões relacionais para PostgreSQL, SQLite e SQL Server. Gerenciador de contexto `with get_db_session() as session:` com rollback automático em caso de exceção. |
| **Planilhas & Arquivos** | `infrastructure/storage.py` | Leitor universal de arquivos (Excel, CSV, JSON), exportação de relatórios `.xlsx` estilizados via Pandas/OpenPyXL e compressão ZIP. |
| **PDF** | `infrastructure/pdf.py` | Extração de texto por páginas e expressões regulares nativas para detecção de CNPJs, CPFs, datas, valores monetários e linha digitável de boletos. |
| **Inteligência Artificial** | `infrastructure/ai.py` | Cliente agnóstico para LLMs (OpenAI, Groq, Ollama) com fallback inteligente (simulação controlada) para desenvolvimento e testes sem quebrar a pipeline. |
| **Notificações** | `infrastructure/notifier.py` | Envio de e-mails corporativos via SMTP autenticado com suporte a HTML e anexos, além de Webhooks para Microsoft Teams e Slack. |
| **Cliente HTTP / APIs** | `infrastructure/http_client.py` | Cliente encapsulado com timeout e tratamento padronizado de respostas para consumo de APIs REST. |
| **Auditoria e Logs** | `infrastructure/logger.py` | Logger JSON estruturado e formatado no terminal, registrando timestamps, etapas, status e metadados para conformidade de governança corporativa. |

---

## 4. Arquitetura de Pastas e Clean Architecture

Ao criar um robô com `pyrpa init`, a seguinte estrutura é gerada:

```text
meu_robo/
├── domain/                      <- Camada mais interna (regras puras)
│   ├── contracts.py             <- ContextoExecucao, BaseUseCase, ResultadoPasso
│   └── queue.py                 <- Gestão transacional de itens de fila
├── application/                 <- Casos de Uso do Robô
│   ├── extracao.py              <- Etapa 1: Herda de BaseUseCase
│   └── processamento.py         <- Etapa 2: Herda de BaseUseCase
├── infrastructure/              <- Conectores e Adaptadores de Tecnologia
│   ├── browser.py               <- Wrapper Web defensivo
│   ├── database.py              <- Sessão transacional de banco
│   ├── storage.py               <- Leitura e exportação de dados (Excel/CSV/JSON)
│   ├── pdf.py                   <- Extração de dados de PDFs
│   ├── ai.py                    <- Processamento cognitivo via LLM
│   ├── notifier.py              <- SMTP e Webhooks
│   └── logger.py                <- Log estruturado de auditoria
├── metadados/
│   └── fluxo.yaml               <- Contrato declarativo de orquestração
├── dags/                        <- Saída da compilação para o Airflow
│   └── dag_meu_robo.py
├── .env                         <- Variáveis de ambiente locais (protegidas no .gitignore)
├── .gitignore                   <- Bloqueio contra vazamento de credenciais e bancos locais
├── requirements.txt             <- Dependências do projeto
└── main.py                      <- Ponto de entrada de execução local
```

### Regra de Ouro da Clean Architecture:
- Os arquivos dentro de `domain/` e `application/` **não conhecem** bibliotecas externas como `playwright`, `selenium`, `pandas` ou `sqlalchemy`.
- Se um caso de uso precisa acessar um banco ou navegador, ele recebe a interface ou consome o adaptador da camada `infrastructure/`.

---

## 5. Exemplo de Implementação de um Caso de Uso

Veja como é simples e limpa a escrita de um caso de uso corporativo:

```python
from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
from infrastructure.browser import get_browser, BrowserConfig
from infrastructure.logger import RPAAuditLogger

class ColetarCotacoesUseCase(BaseUseCase):
    def __init__(self) -> None:
        self.logger = RPAAuditLogger(nome_robo="robo_financeiro")

    def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
        self.logger.info("Iniciando coleta de cotações...")

        # 1. Recupera configuração do navegador
        config = BrowserConfig.from_env()

        # 2. Utiliza o context manager para garantir fechamento seguro
        with get_browser(config) as browser:
            browser.navegar("https://exemplo.com/cotacoes")
            dolar = browser.extrair_texto("#valor-dolar")
            self.logger.info(f"Cotação capturada: R$ {dolar}")

        # 3. Disponibiliza o dado para as próximas etapas
        contexto.definir("cotacao_dolar", float(dolar.replace(",", ".")))

        return ResultadoPasso(
            sucesso=True,
            mensagem="Cotação coletada com sucesso.",
            dados={"dolar": dolar}
        )
```

---

## 6. Boas Práticas Recomendadas

1. **Nunca use variáveis globais entre etapas**:  
   Utilize sempre o `contexto.definir(chave, valor)` e `contexto.obter(chave)` para garantir que o robô possa ser testado de forma isolada.
2. **Sempre use gerenciadores de contexto (`with`)**:  
   Isso previne vazamento de memória e evita que processos zumbis do Chrome ou conexões presas no banco de dados travem o servidor de produção.
3. **Mantenha o `.env` fora do Git**:  
   Nunca comite senhas, tokens ou URLs de bancos de dados. Utilize o `.env.example` para documentar as chaves necessárias.
4. **Valide antes de rodar**:  
   Execute `pyrpa validate` antes de submeter novos fluxos para a esteira de CI/CD.
