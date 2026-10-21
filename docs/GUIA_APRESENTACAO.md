# 📘 Guia de Apresentação e Arquitetura — pyrpa

Este documento serve como roteiro prático e conceitual para apresentar o framework **`pyrpa`** de forma simples, clara e sem jargões complicados.

---

## 🧭 PARTE 1: Como o `pyrpa` foi Construído por Dentro
O framework é composto por apenas **4 arquivos principais**. Pense neles como 4 profissionais com papéis bem definidos trabalhando em equipe:

```text
pyrpa/
├── models/
│   └── schema.py       # 1. O Fiscal de Regras
├── core/
│   ├── validator.py    # 2. O Leitor / Inspetor
│   └── generator.py    # 3. O Construtor da Casa
└── cli.py              # 4. A Voz e a Tela do Terminal
```

---

### 1. `pyrpa/models/schema.py` — O Fiscal de Regras
* **O que ele é:** O manual de regras de trânsito do robô.
* **Explicação Simples:** Ele diz o que pode e o que não pode estar escrito dentro do arquivo `fluxo.yaml`. 
* **O que ele fiscaliza:**
  - O nome do robô não pode ter espaços nem caracteres especiais.
  - Cada passo precisa ter um nome legível e uma ferramenta associada (Playwright, Selenium, Pandas).
  - **A trava principal:** Ele proíbe dois passos de terem o mesmo código identificador (`id: "passo_1"` duplicado), para que o robô não confunda as etapas na hora de executar ou registrar o histórico de logs.

---

### 2. `pyrpa/core/validator.py` — O Leitor e Inspetor de Arquivos
* **O que ele é:** O assistente que abre a carta e lê para o Fiscal.
* **Explicação Simples:** Ele acessa o arquivo físico `fluxo.yaml` no disco do computador com segurança.
* **O que ele faz:**
  - Confere se o arquivo realmente existe na pasta.
  - Checa se o texto do arquivo está com a formatação correta (sem erros de indentação ou espaços errados).
  - Entrega os dados mastigados para o `schema.py` conferir.
  - Se houver algum erro, em vez de deixar o programa travar com uma tela assustadora de erro do Python, ele gera uma mensagem limpa e amigável avisando exatamente onde está o problema.

---

### 3. `pyrpa/core/generator.py` — O Construtor da Casa
* **O que ele é:** A máquina de criar projetos. É o motor por trás do comando `pyrpa init`.
* **Explicação Simples:** Quando você pede um robô novo, ele cria o esqueleto de pastas e gera os arquivos iniciais.
* **O que ele faz:**
  - Cria as pastas organizadas da Arquitetura Limpa (`domain`, `application`, etc.).
  - **Proteção:** Confere se a pasta onde você quer criar já existe e tem coisas dentro (para não apagar arquivos de ninguém por engano).
  - Já escreve os arquivos de partida prontos: o mapa do robô (`fluxo.yaml`), o botão de ligar (`main.py`), as configurações protegidas (`.env`) e as bibliotecas necessárias (`requirements.txt`).

---

### 4. `pyrpa/cli.py` — A Voz e a Tela do Terminal
* **O que ele é:** O recepcionista que atende quem digita comandos no CMD.
* **Explicação Simples:** Ele escuta os comandos que você digita no terminal (`pyrpa init` ou `pyrpa validate`) e desenha as respostas na tela.
* **O que ele faz:**
  - Cria os comandos executáveis do terminal.
  - Usa a biblioteca **Rich** para desenhar as tabelas coloridas, caixas de sucesso e painéis explicativos de erro que você vê na tela preta do CMD.

---

## 📂 PARTE 2: As Pastas que o `pyrpa` Gera (O Projeto-Filho)

Quando um desenvolvedor roda `pyrpa init`, ele recebe um projeto com 4 camadas independentes, seguindo a **Clean Architecture (Arquitetura Limpa)**:

```text
robo_faturamento/
├── domain/            # 1. As Regras de Negócio Puras
├── application/       # 2. O Roteiro do Robô
├── infrastructure/    # 3. As Ferramentas Externas
├── interfaces/        # 4. A Entrada / Terminal
├── metadados/
│   └── fluxo.yaml     # 5. O Mapa Declarativo das Etapas
├── .env               # 6. O Cofre de Senhas e Links
├── requirements.txt   # 7. As Bibliotecas Necessárias
├── .gitignore         # 8. A Proteção do Git
└── main.py            # 9. O Botão de Ligar
```

---

### Por que cada pasta existe?

| Pasta / Arquivo | O que fica dentro? | Por que fica separado? |
| :--- | :--- | :--- |
| **`domain/`** | Regras de cálculo, fórmulas e validações puras (ex: como calcular o imposto da nota). | **Zero dependências externas.** Não usa internet, nem banco de dados. É matemática e regra pura da empresa. |
| **`application/`** | O roteiro do robô (os Casos de Uso). | Diz a ordem das tarefas: *1º Baixar a nota*, *2º Calcular imposto*, *3º Enviar e-mail*. |
| **`infrastructure/`** | As ferramentas pesadas: navegadores (Playwright/Selenium), conexões SQL e APIs. | **Muda o tempo todo.** Se a empresa trocar o Chrome pelo Edge ou o banco SQL por Oracle, você só altera essa pasta, sem estragar a regra do negócio. |
| **`interfaces/`** | Controladores e telas locais. | Onde ficam os comandos para acionar o robô manualmente pelo terminal se necessário. |
| **`metadados/fluxo.yaml`** | O mapa com a lista de etapas do robô em texto simples. | Permite que qualquer pessoa ou o **Apache Airflow** saiba o que o robô faz sem precisar ler código Python. |
| **`.env`** | Usuários, senhas, chaves de API e links. | **Segurança.** As senhas nunca devem ficar escritas direto no código. |
| **`.gitignore`** | Lista de arquivos bloqueados. | Garante que ninguém envie o arquivo de senhas (`.env`) ou arquivos temporários para o GitHub. |
| **`main.py`** | O ponto de partida do robô. | Já vem pronto para ler o `fluxo.yaml` e dar a partida no robô. |

---

## 💻 PARTE 3: Passo a Passo no Terminal (Criando e Rodando em Outra Pasta)

Siga este roteiro no Prompt de Comando (**CMD**) para fazer uma demonstração ao vivo:

### Passo 1: Abra o CMD e vá para a sua Área de Trabalho (Desktop)
Assim o professor vê a pasta do robô surgindo ao vivo fora do projeto do framework:

```cmd
cd "C:\Users\nicol\Desktop"
```

---

### Passo 2: Crie o novo robô com o `pyrpa`
Digite o comando de criação:

```cmd
pyrpa init robo_faturamento
```
*(O terminal exibirá a tabela colorida confirmando as camadas arquiteturais geradas).*

---

### Passo 3: Mostre a estrutura de pastas gerada
Peça para o CMD desenhar a árvore do robô na tela:

```cmd
tree /F robo_faturamento
```
*(Você verá todas as pastas e arquivos organizados listados na tela).*

---

### Passo 4: Valide o fluxo do robô
Use o comando de validação para mostrar que o arquivo YAML está correto:

```cmd
pyrpa validate robo_faturamento\metadados\fluxo.yaml
```
*(O terminal exibirá uma tabela verde com o Passo 1 [Extrair Dados / Playwright] e o Passo 2 [Processar Dados / Pandas]).*

---

### Passo 5: Dê a partida no robô!
Entre na pasta do robô e execute o botão de início:

```cmd
cd robo_faturamento
python main.py
```

O terminal vai responder na hora:
```text
Iniciando execução do fluxo: robo_faturamento (v1.0.0)
Total de etapas registradas: 2
```

---

## 🚀 PARTE 4: Roadmap de Evolução (Trabalhos Futuros para o TCC)

Apresente estes pontos ao professor como os próximos passos de evolução do framework:

### 1. Inicialização Interativa por Perfil de Automação
Em vez de um `requirements.txt` estático, o `pyrpa init` perguntará o tipo de automação para instalar apenas o necessário:
- **Perfil Web:** Playwright + Selenium + Undetected-Chromedriver (suporte a Chrome, Firefox e Edge com bypass anti-bot).
- **Perfil Banco de Dados:** `SQLAlchemy` nativo com conexão configurada via `DATABASE_URL` no `.env` (PostgreSQL, SQL Server, Oracle, MySQL).
- **Perfil Documentos / OCR:** Bibliotecas para processamento inteligente de PDFs (`pdfplumber`, `pypdf`).

### 2. Isolamento Automático de Ambiente (`.venv` e Docker)
- Criação automática do ambiente virtual isolado (`python -m venv .venv`) para evitar conflitos de versões entre robôs no mesmo servidor.
- Geração de um `Dockerfile` base pronto para subir o robô para contêineres na nuvem ou Kubernetes.

### 3. Integração com IA e Protocolo MCP (Model Context Protocol)
- **Robôs Inteligentes:** Adaptadores para modelos de IA tomarem decisões complexas em regras de negócio não determinísticas.
- **Robô como Ferramenta MCP:** Permitir que IAs corporativas (Slack, Teams, Claude, Gemini) acionem as etapas do `pyrpa` sob demanda de forma segura.

---

## 🎯 Resumo de Bolso para Falar com o Professor

> *"Professor, o que nós construímos aqui resolve um problema muito comum em empresas: robôs feitos sem padrão que quebram à toa."*
>
> *"Com o **pyrpa**, o programador usa uma única linha (`pyrpa init`) e já recebe a arquitetura limpa pronta, com regras de negócio blindadas das ferramentas web, configurações seguras no `.env` e as etapas descritas num arquivo simples (`fluxo.yaml`)."*
>
> *"E como visão de futuro do TCC, estamos expandindo os adaptadores da infraestrutura para suportar múltiplos navegadores, bancos de dados via SQLAlchemy, isolamento automático de `.venv` e integração com agentes de IA via MCP."*
