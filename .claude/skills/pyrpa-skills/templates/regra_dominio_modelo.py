"""Modelo de regra de negócio PURA para a camada domain/ do pyrpa.

Regras desta camada:
  - sem acesso a arquivo, rede, banco ou navegador;
  - sem importar bibliotecas externas (requests, pandas, playwright...);
  - sem importar application/ nem infrastructure/;
  - valores de negócio que podem mudar (limites, percentuais) entram como
    parâmetro, nunca escondidos no meio da conta.
"""


def regra_exemplo(valor_atual: float, valor_anterior: float, limite_percentual: float = 5.0) -> bool:
    """Aceita o valor atual se a variação em relação ao anterior for menor que o limite."""
    if valor_anterior == 0:
        return False
    variacao = abs(valor_atual - valor_anterior) / valor_anterior * 100
    return variacao < limite_percentual
