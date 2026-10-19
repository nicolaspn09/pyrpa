from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class StatusItemFila(str, Enum):
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    SUCESSO = "SUCESSO"
    FALHA_NEGOCIO = "FALHA_NEGOCIO"
    FALHA_SISTEMA = "FALHA_SISTEMA"


@dataclass
class ItemFila:
    """Item individual de uma fila de processamento transacional em RPA."""
    id: str
    dados: Dict[str, Any]
    status: StatusItemFila = StatusItemFila.PENDENTE
    tentativas: int = 0
    erro: Optional[str] = None
    resposta: Optional[Dict[str, Any]] = None
    data_criacao: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_conclusao: Optional[datetime] = None


class FilaTrabalho:
    """
    Gerenciador de fila de itens de trabalho com proteção contra falhas (Transactional Pattern).
    Permite que o robô processe centenas de registros isoladamente sem que a falha de um
    item interrompa o lote inteiro.
    """

    def __init__(self, nome_fila: str = "padrao", max_tentativas: int = 3) -> None:
        self.nome_fila = nome_fila
        self.max_tentativas = max_tentativas
        self._itens: Dict[str, ItemFila] = {}

    def enfileirar(self, item_id: str, dados: Dict[str, Any]) -> ItemFila:
        """Adiciona um novo registro à fila para processamento."""
        item = ItemFila(id=item_id, dados=dados)
        self._itens[item_id] = item
        return item

    def enfileirar_lote(self, lista_dados: List[Dict[str, Any]], campo_id: str = "id") -> List[ItemFila]:
        """Enfileira uma lista de dicionários em lote."""
        resultado = []
        for idx, dados in enumerate(lista_dados):
            item_id = str(dados.get(campo_id, f"item_{idx + 1}"))
            resultado.append(self.enfileirar(item_id, dados))
        return resultado

    def proximo_pendente(self) -> Optional[ItemFila]:
        """Recupera o próximo item disponível para processamento e marca como PROCESSANDO."""
        for item in self._itens.values():
            if item.status == StatusItemFila.PENDENTE:
                item.status = StatusItemFila.PROCESSANDO
                item.tentativas += 1
                return item
        return None

    def marcar_sucesso(self, item_id: str, resposta: Optional[Dict[str, Any]] = None) -> None:
        """Marca o item como concluído com sucesso."""
        if item_id in self._itens:
            item = self._itens[item_id]
            item.status = StatusItemFila.SUCESSO
            item.resposta = resposta
            item.data_conclusao = datetime.now(timezone.utc)

    def marcar_falha(
        self,
        item_id: str,
        motivo_erro: str,
        eh_falha_sistema: bool = False,
    ) -> None:
        """
        Registra falha no item.
        Diferencia erro de negócio (ex: saldo insuficiente, CPF inválido)
        de erro de sistema (ex: portal fora do ar, timeout).
        """
        if item_id in self._itens:
            item = self._itens[item_id]
            item.erro = motivo_erro
            if eh_falha_sistema and item.tentativas < self.max_tentativas:
                # Permite reprocessamento se for falha transitória de infraestrutura
                item.status = StatusItemFila.PENDENTE
            else:
                item.status = (
                    StatusItemFila.FALHA_SISTEMA if eh_falha_sistema else StatusItemFila.FALHA_NEGOCIO
                )
                item.data_conclusao = datetime.now(timezone.utc)

    def obter_metricas(self) -> Dict[str, int]:
        """Calcula o resumo consolidado do lote processado."""
        metricas = {
            "total": len(self._itens),
            "sucesso": 0,
            "falha_negocio": 0,
            "falha_sistema": 0,
            "pendente": 0,
            "processando": 0,
        }
        for item in self._itens.values():
            if item.status == StatusItemFila.SUCESSO:
                metricas["sucesso"] += 1
            elif item.status == StatusItemFila.FALHA_NEGOCIO:
                metricas["falha_negocio"] += 1
            elif item.status == StatusItemFila.FALHA_SISTEMA:
                metricas["falha_sistema"] += 1
            elif item.status == StatusItemFila.PENDENTE:
                metricas["pendente"] += 1
            elif item.status == StatusItemFila.PROCESSANDO:
                metricas["processando"] += 1
        return metricas

    def todos_itens(self) -> List[ItemFila]:
        return list(self._itens.values())
