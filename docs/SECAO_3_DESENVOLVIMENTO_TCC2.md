# SEÇÃO 3: DESENVOLVIMENTO DO SISTEMA (TEXTO CONTÍNUO PARA O ARTIGO)

> **Formato:** Texto contínuo em seção única (sem subtópicos 3.1, 3.2), no padrão conciso de artigo científico (8 a 10 páginas).  
> **Indicação das Imagens:** As Figuras 2 e 3 do TCC 1 estão posicionadas exatamente nos seus pontos canônicos de citação no fluxo textual.

---

## 3. DESENVOLVIMENTO DO SISTEMA

Diferentemente de sistemas de informação corporativos convencionais voltados ao usuário final leigo, o artefato computacional concebido neste trabalho configura-se como um framework de suporte à engenharia de software e automação de processos. Por conseguinte, o sistema atende a dois perfis primários de interação: o Desenvolvedor de Automação Robótica de Processos (RPA), que interage diretamente via Interface de Linha de Comando (CLI) e código-fonte, e os Analistas de Negócio (*Product Owners* e gestores de processos), que realizam a governança e o acompanhamento dos fluxos operacionais por meio de metadados declarativos. Esta seção descreve a classificação metodológica da pesquisa, o levantamento de requisitos, a modelagem arquitetural do `pyrpa`, os componentes de software do núcleo, a interface do desenvolvedor (scaffolding e CLI), as tecnologias adotadas e o planejamento detalhado dos instrumentos de validação empírica e usabilidade.

A condução deste trabalho classifica-se como uma pesquisa aplicada quanto à sua natureza, de caráter exploratório e descritivo quanto aos seus objetivos (SOMMERVILLE, 2011). No âmbito da Engenharia de Software, adotou-se o método da *Design Science Research* (DSR), o qual fundamenta a concepção, o desenvolvimento e a avaliação iterativa de um artefato computacional projetado para solucionar uma lacuna pragmática: o acúmulo acelerado de débito técnico em automações corporativas gerado pela ausência de padrões arquiteturais e pela fragilidade de scripts monolíticos (CUNNINGHAM, 1992; ERNST & YOUNG, 2019). O ciclo de desenvolvimento do núcleo do framework orientou-se pelos preceitos do Desenvolvimento Orientado por Testes (*Test-Driven Development* - TDD) (PRESSMAN; MAXIM, 2016). Os cenários de validação sintática e semântica foram formalizados em suítes de testes unitários previamente à codificação das rotinas de processamento, assegurando a cobertura antecipada de exceções de integridade, tais como duplicidade de identificadores de etapas, ambiguidades de importação de módulos e colisões no sistema de arquivos.

A especificação de requisitos derivou da análise comparativa das ferramentas existentes no mercado e da necessidade de estabelecer uma barreira técnica contra acoplamentos indevidos. O Quadro 1 sintetiza os requisitos funcionais (RF) e não funcionais (RNF) que nortearam a implementação do framework.

Quadro 1 – Requisitos Funcionais e Não Funcionais do Framework pyrpa
| Identificador | Categoria | Descrição do Requisito |
| :--- | :--- | :--- |
| **RF01** | Funcional | Disponibilizar uma CLI intuitiva para inicialização automatizada (*scaffolding*) de projetos de automação. |
| **RF02** | Funcional | Interpretar e validar sintática e semanticamente arquivos de metadados declarativos em formato YAML. |
| **RF03** | Funcional | Assegurar a integridade referencial dos nós do fluxo, barrando identificadores duplicados ou ausentes. |
| **RF04** | Funcional | Disponibilizar comando de validação preventiva prévia à execução, emitindo diagnósticos no terminal. |
| **RNF01** | Não Funcional | Impor a separação física e lógica das camadas com base nos princípios da *Clean Architecture*. |
| **RNF02** | Não Funcional | Desenvolver o ecossistema estritamente em Python 3.11+, sem exigir Linguagens de Domínio Específico (DSLs) proprietárias. |
| **RNF03** | Não Funcional | Manter desacoplamento total entre o núcleo do framework e os provedores tecnológicos externos (ex.: Selenium, bancos). |
| **RNF04** | Não Funcional | Assegurar interoperabilidade universal com terminais de sistemas operacionais corporativos (POSIX e Windows CP1252). |
Fonte: Elaborado pelos autores (2026).

A interface física de arquitetura entregue ao desenvolvedor materializa-se na estrutura gerada pelo processo de *scaffolding*. Ao executar o comando de inicialização via CLI, o framework cria automaticamente a árvore de diretórios e arquivos base exibida na Figura 2.

Figura 2 – Estrutura de Diretórios gerada pelo Framework
*(INSERIR AQUI A IMAGEM DA ÁRVORE DE DIRETÓRIOS DO TCC 1 - antiga Figura 3)*  
Fonte: Elaborado pelos autores (2026).

A hierarquia apresentada na Figura 2 materializa os preceitos de Martin (2017), garantindo que as regras de negócio alocadas em `domain` e a coordenação dos casos de uso em `application` permaneçam estritamente isoladas das bibliotecas de automação web, banco de dados e APIs externas alocadas em `infrastructure`. A pasta `interfaces` abriga os adaptadores de acionamento (como disparos via terminal ou webhooks), enquanto a pasta `metadados` centraliza a orquestração declarativa do robô no arquivo `fluxo.yaml`.

O comportamento dinâmico do sistema durante o ciclo de execução de uma automação é modelado no Diagrama de Sequência apresentado na Figura 3.

Figura 3 – Diagrama de Sequência do Fluxo de Execução do pyrpa
*(INSERIR AQUI A IMAGEM DO DIAGRAMA DE SEQUÊNCIA DO TCC 1 - antiga Figura 4)*  
Fonte: Elaborado pelos autores (2026).

Conforme evidenciado na Figura 3, o ciclo inicia-se com o envio da instrução de execução via CLI pelo desenvolvedor. O núcleo aciona o componente de validação para verificar a conformidade sintática e semântica do arquivo de metadados `fluxo.yaml`. Uma vez certificado, o motor traduz as declarações YAML em instâncias executáveis das classes correspondentes na camada `application`, permitindo que o robô seja executado localmente ou orquestrado externamente sem que o desenvolvedor precise codificar manualmente laços procedurais de controle de fluxo.

A implementação interna do núcleo do `pyrpa` foi dividida em componentes de software especializados:
1. **Modelagem Declarativa (`pyrpa.models.schema`):** Utiliza tipagem estática e validação em tempo de parsing via Pydantic v2. A entidade `PassoModel` mapeia as etapas individuais, aplicando validadores de campo (`@field_validator`) para certificar que o destino (*target*) atenda às convenções canônicas de importação do Python (PEP 8). A entidade raiz `FluxoSchema` supervisiona o documento completo, utilizando validadores de modelo (`@model_validator`) para garantir que identificadores de tarefas não se repitam, mitigando colisões em pipelines de execução.
2. **Motor de Validação (`pyrpa.core.validator`):** A classe `FluxoValidator` realiza o carregamento seguro dos metadados via `yaml.safe_load`. As falhas operacionais (ausência de arquivo ou sintaxe incorreta) e inconsistências conceituais são interceptadas e encapsuladas na exceção `FluxoInvalidoException`, eliminando saídas ruidosas de rastreamento (*stack traces*) e orientando a correção direta pelo desenvolvedor.
3. **Motor de Geração de Projetos (`pyrpa.core.generator`):** A classe `ProjetoGenerator` executa a montagem física da solução. O motor inclui checagem defensiva contra sobrescrita acidental em diretórios pré-existentes não vazios. Durante a criação, injeta modelos pré-configurados: `fluxo.yaml` (orquestração declarativa), `.env` (gestão segura de credenciais), `.gitignore` (governança de versionamento), `requirements.txt` (especificação de dependências) e `main.py` (ponto de entrada canônico).

O Quadro 2 sintetiza as responsabilidades dos módulos de software do núcleo do framework.

Quadro 2 – Componentes de Software do Núcleo do pyrpa
| Módulo | Classe / Elemento | Responsabilidade na Arquitetura |
| :--- | :--- | :--- |
| `pyrpa.models.schema` | `PassoModel` | Modelagem, sanitização e validação das propriedades individuais de cada etapa. |
| `pyrpa.models.schema` | `FluxoSchema` | Validação semântica global do fluxo e garantia de unicidade de tarefas via *hash sets*. |
| `pyrpa.core.validator` | `FluxoValidator` | Parsing seguro de arquivos YAML e encapsulamento em mensagens amigáveis de erro. |
| `pyrpa.core.generator` | `ProjetoGenerator` | Geração física de diretórios e injeção dos modelos estruturais da Clean Architecture. |
| `pyrpa.cli` | Aplicação Typer / Rich | Roteamento de comandos de terminal, exibição de relatórios tabulares e usabilidade. |
Fonte: Elaborado pelos autores (2026).

A interface de linha de comando foi desenvolvida com a biblioteca Typer, adotando padrões POSIX e fornecendo autodocumentação nativa via terminal. Para assegurar total portabilidade em ambientes corporativos Windows baseados na página de código CP1252, a biblioteca Rich foi configurada com caracteres tipográficos compatíveis (`>>`, `[OK]`), preservando a ergonomia visual de tabelas e painéis sem incorrer em falhas de decodificação. Os comandos principais compreendem o `pyrpa init <nome_projeto> [caminho]`, responsável pelo *scaffolding* completo, e o `pyrpa validate [caminho_yaml]`, que atua como ferramenta de inspeção estática preventiva (*linting*) em esteiras de integração contínua (CI/CD).

A seleção de tecnologias orientou-se por critérios de desempenho computacional, maturidade no ecossistema Python e ausência de sobrecarga nos robôs finais. O Quadro 3 detalha a pilha adotada.

Quadro 3 – Pilha Tecnológica do Núcleo do Framework
| Tecnologia | Versão Mínima | Função Primária | Justificativa Técnica |
| :--- | :--- | :--- | :--- |
| **Python** | 3.11+ | Linguagem Base | Otimizações de desempenho do interpretador, tipagem estática nativa e tratamento estruturado de exceções. |
| **Typer** | 0.9+ | Framework de CLI | Criação declarativa de comandos baseada em anotações de tipo (*type hints*) com autocompletar integrado. |
| **Rich** | 13.0+ | Renderização Visual | Exibição de tabelas e diagnósticos formatados no terminal com tratamento de codificação. |
| **Pydantic** | 2.5+ | Validação de Dados | Validação de alta performance com motor compilado em Rust (*pydantic-core*). |
| **PyYAML** | 6.0+ | Parser de Metadados | Padrão consolidado para interpretação segura (`safe_load`) de arquivos de orquestração. |
| **pytest** | 7.4+ | Testes Automatizados | Suíte para execução de testes unitários e de integração com suporte a *fixtures*. |
Fonte: Elaborado pelos autores (2026).

Para aferir a eficácia da arquitetura proposta na contenção do débito técnico e verificar sua aceitação prática, o processo de validação empírica — cujos resultados serão discutidos na Seção 4 — foi planejado sob três frentes complementares: confiabilidade computacional, estudo de caso comparativo e teste de usabilidade multidisciplinar.

A validação de confiabilidade computacional será aferida quantitativamente por meio da execução da suíte automatizada de testes com `pytest` e da extensão `pytest-cov`, mensurando a cobertura de código, o tempo de resposta do *scaffolding* e a assertividade na captura de anomalias sintáticas. O estudo de caso comparativo consistirá na implementação de um mesmo processo corporativo real (extração e consolidação de relatórios financeiros via web) sob duas abordagens: uma tradicional baseada em script monolítico e outra governada pelo `pyrpa`. Ambas serão submetidas a alterações controladas de ambiente (como modificação de seletores na interface e reordenação de atividades) para mensurar a Localidade de Mudança (*Locality of Change*), o número de arquivos impactados e o grau de acoplamento do código.

Por fim, o teste de usabilidade multidisciplinar será conduzido com desenvolvedores de RPA e analistas de negócio, avaliando tanto a experiência técnica de desenvolvimento quanto a capacidade de auditoria e governança proporcionada pelos metadados declarativos. O Quadro 4 resume o protocolo e as métricas planejadas para esta avaliação.

Quadro 4 – Planejamento do Teste de Usabilidade Multidisciplinar
| Grupo de Avaliação | Perfil Amostral | Tarefas Submetidas | Instrumento de Coleta | Métricas Avaliadas |
| :--- | :--- | :--- | :--- | :--- |
| **Grupo Técnico** | Desenvolvedores de RPA e Engenheiros de Software | 1. Inicializar um projeto via CLI (`pyrpa init`).<br>2. Adicionar uma nova etapa no `fluxo.yaml` e implementar seu código.<br>3. Identificar um erro de validação forçado via `pyrpa validate`. | Questionário baseado na escala SUS (*System Usability Scale*) e escala Likert (1 a 5). | Facilidade de aprendizado (*learnability*), clareza dos erros da CLI, ergonomia da árvore de pastas e tempo de setup. |
| **Grupo de Negócio** | Analistas de Processos e *Product Owners* | 1. Interpretar a sequência de atividades de um robô lendo o `fluxo.yaml`.<br>2. Alterar a prioridade ou ordem de uma atividade diretamente nos metadados sem apoio técnico. | Questionário qualitativo semiestruturado e escala Likert de percepção de clareza. | Legibilidade do fluxo declarativo, grau de dependência técnica para auditoria e confiança na governança do processo. |
Fonte: Elaborado pelos autores (2026).

A coleta de dados ocorrerá por meio da observação do tempo de execução das tarefas e da aplicação dos questionários logo após os experimentos. A correlação entre o escore SUS obtido com os desenvolvedores e os relatos qualitativos dos analistas de processos fornecerá o embasamento empírico necessário para avaliar o impacto do `pyrpa` na sustentabilidade das automações corporativas.
