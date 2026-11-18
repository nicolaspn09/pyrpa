# 🤖 pyrpa

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/architecture-Clean%20Architecture-brightgreen.svg)](#-arquitetura-gerada-nos-projetos-filhos)
[![Validation](https://img.shields.io/badge/validation-Pydantic%20v2-purple.svg)](https://docs.pydantic.dev/latest/)
[![CLI Framework](https://img.shields.io/badge/CLI-Typer%20%2B%20Rich-orange.svg)](https://typer.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-69%2F69%20passing-success.svg)](#-testes-e-qualidade)
[![License](https://img.shields.io/badge/license-MIT-informational.svg)](LICENSE)

> **CLI Opinativa para Gestão de Projetos de Robotic Process Automation (RPA) em Python Corporativo com Clean Architecture e Orquestração Declarativa.**

---

## 📌 Visão Geral

Estudos de mercado (Ernst & Young, Deloitte) apontam que entre **30% e 50% dos projetos corporativos de automação falham ao tentar escalar**. A raiz desse gargalo é o **alto débito técnico**: scripts construídos sem padrões estruturais (*code smells* em até 98% dos repositórios não padronizados), onde lógicas de negócio estão misturadas com código de infraestrutura (drivers de navegadores, bibliotecas de scraping e conexões de banco de dados).

O **`pyrpa`** resolve esse problema através da **padronização arquitetural obrigatória**:
- **Força a Clean Architecture**: Desacopla estritamente regras de domínio (`domain/` e `application/`) das bibliotecas voláteis de infraestrutura (`infrastructure/`).
- **Orquestração Declarativa**: Cada robô possui um contrato `metadados/fluxo.yaml` validado por schemas Pydantic v2.
- **Execução Local + Apache Airflow**: Roda localmente com `pyrpa run` (carregando o `.env` automaticamente) ou compila nativamente em DAGs do Airflow com `pyrpa compile`.
- **Dependências Prontas e Verificação Automática**: Instala automaticamente todas as bibliotecas dos conectores escolhidos (`pandas`, `openpyxl`, `pypdf`, `sqlalchemy`, `playwright`, `selenium`, `openai`, `python-dotenv`).
- **Auditoria & Observabilidade**: Impede duplicidade de IDs e garante rastreabilidade com logs estruturados.

> 📖 **Documentação Técnica Completa:** consulte [docs/MANUAL_DESENVOLVEDOR_PYRPA.md](docs/MANUAL_DESENVOLVEDOR_PYRPA.md).

---

## 🚀 Instalação (Linux, macOS e Windows)

### Pré-requisitos
- **Python 3.10 ou superior** (compatível nativamente com Ubuntu 22.04+, Debian 12+, macOS e Windows 10/11).
- `git` (opcional, se clonar o repositório).

> **Importante:** O nome do pacote oficial no PyPI é **`pyrpa-framework`** (nunca rode `pip install pyrpa`, pois `pyrpa` no PyPI é outra biblioteca de terceiros). Se já instalou errado antes, remova com `pip uninstall pyrpa -y`.

### Opção 1: Via PyPI Oficial (Mais Rápida — Sem `venv` e Sem Git)

```bash
pip install pyrpa-framework
pyrpa doctor
```

*Já baixa automaticamente todas as 13 bibliotecas necessárias (conectores Web, PDF, Excel, Banco, IA e CLI).*

**Se aparecer algum aviso no seu computador:**
- **Windows** (caso `pip` ou `pyrpa` não seja reconhecido nesta janela): use `python -m pip install pyrpa-framework` e depois `python -m pyrpa doctor` (ou abra um novo terminal).
- **Linux / Ubuntu 23.04+ / 24.04+** (caso dê erro de proteção do sistema `externally-managed-environment`): use `pip3 install --break-system-packages pyrpa-framework` (se faltar o `pip3`, rode `sudo apt update && sudo apt install -y python3-pip`).

---

### Opção 2: Instalador Automático com Ambiente Virtual Isolado (`.venv`, via GitHub)

Recomendado se você preferir isolar as bibliotecas do seu sistema ou for contribuir com o código-fonte:

#### 🐧 Linux / Ubuntu / macOS
```bash
git clone https://github.com/nicolaspn09/pyrpa.git
cd pyrpa
bash instalar.sh
```

#### 🪟 Windows (PowerShell ou Prompt de Comando)
```powershell
git clone https://github.com/nicolaspn09/pyrpa.git
cd pyrpa
.\instalar.bat
```
*(Ou dê 2 cliques no arquivo `instalar.bat` dentro da pasta baixada).*

> **Dica se o comando `pyrpa` não for reconhecido no terminal:** utilize `python -m pyrpa doctor` (ou `python3 -m pyrpa doctor` no Linux). O módulo `python -m pyrpa` responde exatamente aos mesmos comandos (`init`, `add`, `validate`, `run`, `compile`).

---

## 💻 Guia Completo de Comandos da CLI

```powershell
# Ver ajuda completa, versão, catálogo interativo e saúde do sistema
pyrpa --help
pyrpa --version
pyrpa info
pyrpa doctor

# 1. Criar um novo projeto RPA (verifica e instala libs faltantes automaticamente)
pyrpa init robo_completo -m completo     # Todos os conectores
pyrpa init robo_compras -m web,banco     # Apenas módulos selecionados
pyrpa init meu_robo                      # Menu interativo no terminal
pyrpa init robo_pasta -d C:\Projetos\robo --forcar

# 2. Adicionar um conector extra depois de criado (web, banco, excel, pdf, ia, email)
cd robo_compras
pyrpa add pdf
pyrpa add excel

# 3. Validar o contrato declarativo YAML (Pydantic v2)
pyrpa validate

# 4. Executar o robô localmente (lê o .env da pasta do robô automaticamente)
pyrpa run
# Ou diretamente via Python:
python main.py

# 5. Compilar o fluxo.yaml para uma DAG do Apache Airflow
pyrpa compile -s diario                  # manual | horario | diario | semanal | mensal | "cron"
```

---

## 🏛 Arquitetura Gerada nos Projetos-Filhos

Ao rodar `pyrpa init <nome_do_projeto>`, a árvore gerada segue o isolamento da Arquitetura Limpa:

```text
<nome_do_projeto>/
├── domain/            # Regras de cálculo, entidades e filas (zero dependências externas)
├── application/       # Casos de uso (UseCases) herdando de BaseUseCase
├── infrastructure/    # Adaptadores defensivos (browser, database, storage, pdf, ai, notifier, http_client, logger)
├── interfaces/        # Controladores locais e pontos de entrada
├── metadados/
│   └── fluxo.yaml     # Grafo declarativo de execução validado pelo Pydantic
├── dags/              # DAGs Python compiladas para o Apache Airflow
├── relatorios/        # Planilhas Excel exportadas
├── logs/              # Logs estruturados de auditoria
├── requirements.txt   # Dependências ativas descomentadas (sem colisão com PyPI)
├── .env               # Variáveis de ambiente locais (lidas automaticamente pelo FluxoRunner)
├── .gitignore         # Proteção contra vazamento de credenciais e caches
└── main.py            # Ponto de entrada de execução direta
```

---

## 🧪 Testes e Qualidade

O framework possui **69 testes unitários e de integração** automatizados com `pytest`:

```bash
# Executar toda a suíte
pytest -v
```

* `tests/integration/test_cli.py` — Testes ponta a ponta da CLI (`--version`, `info`, `doctor`, `init`, `add`, `validate`, `run`, `compile` e dica de navegação).
* `tests/unit/test_schema.py` & `test_validator.py` — Contratos Pydantic v2, regex e leitura segura de YAML.
* `tests/unit/test_generator.py`, `test_modifier.py` & `test_installer.py` — Scaffolding Clean Architecture, inclusão modular e instalação automática de dependências.
* `tests/unit/test_runner.py`, `test_compiler.py` & `test_contracts.py` — Execução com `.env`, compartilhamento de contexto e compilação Airflow.
* `tests/unit/test_infrastructure.py`, `test_doctor.py`, `test_ai.py`, `test_pdf.py` & `test_queue.py` — Adaptadores de infraestrutura, diagnóstico SO/navegadores e fila transacional.

---

## 🎓 Contexto Acadêmico e Autoria

Projeto desenvolvido como **Trabalho de Conclusão de Curso (TCC II)** do curso de **Tecnologia em Análise e Desenvolvimento de Sistemas (ADS)** do **Instituto Federal de Santa Catarina (IFSC — Câmpus Tubarão)**.

- **Autores:** Kauê Cunha Baesso e [Nícolas Paulo Nasário](https://github.com/nicolaspn09)
- **Orientador:** Prof. Tiago Guimarães Moraes
- **Licença:** MIT
