from pyrpa.infrastructure.ai import AiClientAdapter, AiConfig


def test_ai_adapter_modo_simulacao():
    config = AiConfig(modo_simulacao=True, api_key=None)
    client = AiClientAdapter(config)

    resposta = client.consultar("Qual o valor total da nota?")
    assert "[SIMULAÇÃO IA]" in resposta

    categoria = client.classificar(
        "Gostaria de cancelar minha assinatura imediatamente.",
        ["CANCELAMENTO", "DUVIDA_FINANCEIRA", "SUPORTE_TECNICO"]
    )
    assert categoria in ["CANCELAMENTO", "DUVIDA_FINANCEIRA", "SUPORTE_TECNICO"]

    schema = {
        "cnpj": "string com o CNPJ",
        "valor_total": "número decimal do valor",
        "vencimento": "data de vencimento",
    }
    dados = client.extrair_json("Texto da fatura", schema)
    assert "cnpj" in dados
    assert "valor_total" in dados
    assert "vencimento" in dados
