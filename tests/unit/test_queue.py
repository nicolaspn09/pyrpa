from pyrpa.domain.queue import FilaTrabalho, StatusItemFila


def test_fila_trabalho_ciclo_completo():
    fila = FilaTrabalho(nome_fila="faturamento_lote")

    dados_lote = [
        {"id": "DOC-1", "cliente": "Empresa A", "valor": 500},
        {"id": "DOC-2", "cliente": "Empresa B", "valor": -10},  # Valor inválido (erro de negócio)
        {"id": "DOC-3", "cliente": "Empresa C", "valor": 1200},
    ]

    fila.enfileirar_lote(dados_lote)
    metricas_iniciais = fila.obter_metricas()
    assert metricas_iniciais["total"] == 3
    assert metricas_iniciais["pendente"] == 3

    # Processa item 1 -> Sucesso
    item1 = fila.proximo_pendente()
    assert item1 is not None
    assert item1.id == "DOC-1"
    fila.marcar_sucesso(item1.id, {"nota_emitida": "NF-999"})

    # Processa item 2 -> Falha de negócio (não reprocessa)
    item2 = fila.proximo_pendente()
    assert item2 is not None
    assert item2.id == "DOC-2"
    fila.marcar_falha(item2.id, "Valor não pode ser negativo", eh_falha_sistema=False)

    # Processa item 3 -> Sucesso
    item3 = fila.proximo_pendente()
    assert item3 is not None
    assert item3.id == "DOC-3"
    fila.marcar_sucesso(item3.id)

    # Não há mais itens pendentes
    assert fila.proximo_pendente() is None

    metricas_finais = fila.obter_metricas()
    assert metricas_finais["sucesso"] == 2
    assert metricas_finais["falha_negocio"] == 1
    assert metricas_finais["pendente"] == 0
