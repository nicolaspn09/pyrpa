# 🤖 pyrpa

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/architecture-Clean%20Architecture-brightgreen.svg)](#-arquitetura-gerada)
[![Validation](https://img.shields.io/badge/validation-Pydantic%20v2-purple.svg)](https://docs.pydantic.dev/latest/)
[![CLI Framework](https://img.shields.io/badge/CLI-Typer%20%2B%20Rich-orange.svg)](https://typer.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-12%2F12%20passing-success.svg)](#-testes-e-qualidade)
[![License](https://img.shields.io/badge/license-MIT-informational.svg)](LICENSE)

> **CLI Opinativa para Gestão de Projetos de Robotic Process Automation (RPA) em Python Corporativo com Clean Architecture e Orquestração Declarativa.**

---

## 📌 Visão Geral

Estudos de mercado (Ernst & Young, Deloitte) apontam que entre **30% e 50% dos projetos corporativos de automação falham ao tentar escalar**. A raiz desse gargalo é o **alto débito técnico**: scripts construídos sem padrões estruturais (*code smells* em até 98% dos repositórios não padronizados), onde lógicas de negócio estão misturadas com código de infraestrutura (drivers de navegadores, bibliotecas de scraping e conexões de banco de dados).

O **`pyrpa`** nasce para resolver esse problema através da **padronização arquitetural obrigatória**:
- **Força a Clean Architecture**: Desacopla estritamente regras de domínio das bibliotecas voláteis de automação (Playwright, Selenium, Pandas).
- **Orquestração Declarativa**: Cada robô possui um arquivo `metadados/fluxo.yaml` que atua como grafo de execução validado por contratos Pydantic v2.
- **Preparado para Apache Airflow**: Os metadados declarativos eliminam acoplamento e facilitam a conversão nativa em DAGs do Airflow.
- **Auditoria & Observabilidade**: Impede duplicidade de IDs e garante rastreabilidade em logs estruturados corporativos.

---

## 🏛 Arquitetura Gerada nos Projetos-Filhos

Ao rodar `pyrpa init <nome_do_projeto>`, o esqueleto gerado segue estritamente o isolamento das 4 camadas da Arquitetura Limpa:

```text
<nome_do_projeto>/
├── domain/            # Regras de cálculo, entidades e validações puras (Python puro, zero dependências externas)
├── application/       # Casos de uso (UseCases) e lógica de orquestração interna do robô
├── infrastructure/    # Adaptadores externos: drivers (Playwright, Selenium), bancos SQL e chamadas de API
├── interfaces/        # Ponto de entrada, controladores CLI locais e adapters de log
├── metadados/
│   └── fluxo.yaml     # Grafo declarativo de execução e catálogo de providers
├── requirements.txt   # Dependências mínimas versionadas do projeto gerado
├── .env               # Variáveis de ambiente isoladas (HEADLESS, credenciais, timeouts)
├── .gitignore         # Blindagem preventiva contra vazamento de credenciais e caches
└── main.py            # Ponto de entrada instanciado pelo framework
```

### Regra de Dependência
```
interfaces ──▶ application ──▶ domain ◀── infrastructure
```
- **`domain`** não conhece nenhuma outra camada.
- **`application`** contém os casos de uso que implementam interfaces/protocolos abstratos.
- **`infrastructure`** implementa os detalhes concretos (ex: como abrir o Chrome via Playwright).

---

## 📜 Contrato Declarativo (`metadados/fluxo.yaml`)

O grafo de execução do robô é estruturado e validado defensivamente via Pydantic v2 contra o `FluxoSchema`:

```yaml
fluxo:
  nome: "robo_faturamento"
  versao: "1.0.0"
  passos:
    - id: "passo_1"
      nome: "Extrair Dados"
      provider: "playwright" # playwright, selenium, pandas ou custom
      target: "application.extracao.ExtrairDadosUseCase"
    - id: "passo_2"
      nome: "Processar Dados"
      provider: "pandas"
      target: "application.processamento.ProcessarDadosUseCase"
```

### Validações Automáticas de Contrato
- **Unicidade de IDs**: O Pydantic rejeita arquivos com passos contendo IDs repetidos, prevenindo colisões no Apache Airflow e em coletores de logs.
- **Formato Canônico do Target**: O campo `target` exige regex de módulo Python válido (`pacote.modulo.ClasseUseCase`).
- **Sanitização de Nomes**: Nomes de projetos e IDs aceitam apenas caracteres seguros (`^[a-zA-Z0-9_-]+$`).

---

## 🚀 Instalação e Inicialização

### Pré-requisitos
- Python **3.11** ou superior
- Pip ou Poetry

### Instalação em Modo de Desenvolvimento
Clone o repositório e instale com o entrypoint global:

```powershell
git clone https://github.com/nicolaspn09/pyrpa.git
cd pyrpa
pip install git+https://github.com/nicolaspn09/pyrpa.git
ou
pip install -e .
```

Pronto! O executável `pyrpa` estará disponível globalmente no terminal.

---

## 💻 Guia de Uso da CLI

### 1. Inicializar um Novo Projeto RPA
Cria o esqueleto completo com as camadas da Clean Architecture:

```powershell
# Cria a pasta ./robo_financeiro no diretório atual
pyrpa init robo_financeiro

# Ou especifique um diretório de destino customizado
pyrpa init robo_financeiro --destino C:\Projetos\RPA\robo_financeiro

# Forçar criação mesmo se o diretório não estiver vazio
pyrpa init robo_financeiro --forcar
```

### 2. Validar o Contrato de um Robô Existente
Valida a sintaxe do YAML e as regras de negócio antes de subir para produção ou pipeline de CI/CD:

```powershell
# Valida o fluxo padrão (./metadados/fluxo.yaml)
pyrpa validate

# Valida um arquivo específico
pyrpa validate caminho/para/metadados/fluxo.yaml
```

Se o YAML contiver erros de indentação, chaves duplicadas ou caminhos Python inválidos, a CLI exibirá um painel estilizado com a linha e causa exata do erro.

---

## 🧪 Testes e Qualidade

O framework foi desenvolvido sob metodologia **TDD (Test-Driven Development)** e possui 100% de cobertura nos fluxos críticos:

```powershell
# Executar a suíte completa de testes unitários e de integração
pytest -v
```

```text
tests/unit/test_schema.py      -> Validação de contrato Pydantic, duplicidade de IDs e targets
tests/unit/test_validator.py   -> Parsing seguro com PyYAML, erros de sintaxe e I/O defensivo
tests/unit/test_generator.py   -> Scaffolding da árvore Clean Architecture e proteção de sobrescrita
tests/integration/test_cli.py  -> Comandos Typer 'init' e 'validate' via CliRunner
```

---

## 🎓 Contexto Acadêmico e Autoria

Este projeto faz parte do **Trabalho de Conclusão de Curso (TCC II)** do curso de **Análise e Desenvolvimento de Sistemas (ADS)** do **Instituto Federal de Santa Catarina (IFSC)**.

- **Tema:** *Arquitetura Padronizada para Scripts de Automação Python em Ambientes Corporativos: Proposta de um modelo arquitetural para melhoria de manutenibilidade, escalabilidade e governança*
- **Autores:** 
  - [Kauê Cunha Baesso](https://github.com)
  - [Nícolas Paulo Nasário](https://github.com/nicolaspn09)
- **Orientador:** Prof. Tiago Guimarães Moraes

---

## 📄 Licença

Distribuído sob a licença MIT. Consulte `LICENSE` para mais informações.
