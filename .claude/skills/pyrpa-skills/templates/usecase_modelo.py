"""Modelo de UseCase do pyrpa. Copie para application/<nome_do_passo>.py e adapte.

Substitua NomeDoPasso pelo nome real. O arquivo e a classe precisam bater com o
`target` do metadados/fluxo.yaml, por exemplo:
    target: "application.nome_do_passo.NomeDoPassoUseCase"
"""
from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
from infrastructure.logger import RPAAuditLogger

# Regra de negócio PURA vem de domain/ (sem acesso a arquivo, rede ou banco):
# from domain.regra_dominio_modelo import regra_exemplo

# Adaptadores de infraestrutura (do framework ou do projeto) vêm de infrastructure/:
# from infrastructure.storage import StorageAdapter


class NomeDoPassoUseCase(BaseUseCase):
    """Uma frase dizendo o que este passo faz (uma única responsabilidade).

    Lê do contexto:   "chave_de_entrada"  (gravada por um passo anterior)
    Grava no contexto: "chave_de_saida"
    """

    def __init__(self) -> None:
        self.logger = RPAAuditLogger(nome_robo="nome_do_passo")

    def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
        self.logger.info("Iniciando o passo...")

        # 1. Ler o que o passo anterior produziu. obter_obrigatorio falha com
        #    mensagem clara se a chave não existir.
        entrada = contexto.obter_obrigatorio("chave_de_entrada")

        # 2. Orquestrar: chamar a regra de domain e/ou um adaptador de infrastructure.
        #    Nenhuma lógica de negócio aqui e nenhuma biblioteca externa chamada direto.
        resultado = entrada  # troque pela chamada real

        # 3. Falha prevista: devolva sucesso=False com mensagem que quem não
        #    programa consiga entender. O fluxo para neste ponto.
        if not resultado:
            return ResultadoPasso(
                sucesso=False,
                mensagem="Não foi possível obter o resultado deste passo.",
            )

        # 4. Gravar para os próximos passos.
        contexto.definir("chave_de_saida", resultado)

        self.logger.info("Passo concluído.")
        return ResultadoPasso(
            sucesso=True,
            mensagem="Passo concluído com sucesso.",
            dados={"resumo": "o que o passo produziu"},
        )
