from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class ChaveContextoNaoEncontradaException(KeyError):
    """Exceção lançada quando uma chave obrigatória não está presente no ContextoExecucao."""
    pass


@dataclass
class ResultadoPasso:
    """
    Representa o retorno padronizado de qualquer etapa (UseCase) executada pelo robô.
    Garante rastreabilidade e contrato uniforme entre a camada de aplicação e o runner.
    """
    sucesso: bool
    mensagem: str = ""
    dados: Optional[Dict[str, Any]] = field(default_factory=dict)
    duracao_segundos: float = 0.0


class ContextoExecucao:
    """
    Repositório de estado em memória compartilhado entre os passos de uma execução.
    Elimina o uso de variáveis globais e o acoplamento direto entre casos de uso.
    """

    def __init__(self, dados_iniciais: Optional[Dict[str, Any]] = None) -> None:
        self._estado: Dict[str, Any] = dict(dados_iniciais) if dados_iniciais else {}
        self._historico_passos: Dict[str, ResultadoPasso] = {}

    def definir(self, chave: str, valor: Any) -> None:
        """Armazena ou atualiza um valor no contexto compartilhado."""
        if not chave or not isinstance(chave, str):
            raise ValueError("A chave do contexto deve ser uma string não vazia.")
        self._estado[chave] = valor

    def obter(self, chave: str, padrao: Any = None) -> Any:
        """Recupera um valor do contexto ou retorna o valor padrão caso não exista."""
        return self._estado.get(chave, padrao)

    def obter_obrigatorio(self, chave: str) -> Any:
        """
        Recupera um valor obrigatório do contexto.
        Lança ChaveContextoNaoEncontradaException se a chave não tiver sido preenchida por um passo anterior.
        """
        if chave not in self._estado:
            raise ChaveContextoNaoEncontradaException(
                f"A chave obrigatória '{chave}' não foi encontrada no ContextoExecucao."
            )
        return self._estado[chave]

    def contem(self, chave: str) -> bool:
        """Verifica se uma chave existe no contexto atual."""
        return chave in self._estado

    def obter_todos(self) -> Dict[str, Any]:
        """Retorna uma cópia rasa de todos os dados armazenados no contexto."""
        return dict(self._estado)

    def registrar_resultado_passo(self, passo_id: str, resultado: ResultadoPasso) -> None:
        """Registra o resultado de uma etapa no histórico da sessão de execução."""
        self._historico_passos[passo_id] = resultado

    @property
    def historico_passos(self) -> Dict[str, ResultadoPasso]:
        """Retorna o histórico de resultados de cada passo executado."""
        return dict(self._historico_passos)

    def limpar(self) -> None:
        """Reinicia o estado e o histórico do contexto."""
        self._estado.clear()
        self._historico_passos.clear()


class BaseUseCase(ABC):
    """
    Contrato base abstrato para todos os Casos de Uso da camada application/.
    Impede que regras de negócio sejam implementadas fora do padrão arquitetural.
    """

    @abstractmethod
    def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
        """
        Executa a lógica de negócio da etapa.

        :param contexto: Instância de ContextoExecucao compartilhada entre os passos do fluxo.
        :return: Instância de ResultadoPasso indicando sucesso/falha e metadados.
        """
        raise NotImplementedError("Todo UseCase deve implementar o método 'executar'.")
