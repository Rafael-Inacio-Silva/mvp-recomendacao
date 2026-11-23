"""Avaliação offline do recomendador com pedidos separados para teste."""

import pandas as pd

from modelo.recomendador import calcular_populares, preparar_regras, recomendar, sugerir_populares
from modelo.regras import CONFIANCA_MINIMA, SUPORTE_MINIMO, calcular_regras, formatar_regras, montar_cestas

PROPORCAO_TESTE = 0.2
SEMENTE = 42


def dividir_pedidos(pedidos, proporcao_teste=PROPORCAO_TESTE, semente=SEMENTE):
    """Separa os pedidos em treino e teste, sem dividir um mesmo pedido entre os dois."""
    ids = pd.Series(pedidos["id_pedido"].unique())
    ids_teste = ids.sample(frac=proporcao_teste, random_state=semente)
    em_teste = pedidos["id_pedido"].isin(ids_teste)
    return pedidos[~em_teste], pedidos[em_teste]


def treinar(treino, suporte_minimo=SUPORTE_MINIMO, confianca_minima=CONFIANCA_MINIMA):
    """Calcula as regras e os itens mais pedidos apenas com os pedidos de treino."""
    regras = calcular_regras(montar_cestas(treino), suporte_minimo, confianca_minima)
    regras = preparar_regras(formatar_regras(regras))
    return regras, calcular_populares(treino)


def montar_casos(teste):
    """Gera um caso por item de cada pedido de teste: o item escondido e o restante como carrinho."""
    casos = []

    for _, itens in teste.groupby("id_pedido")["item"]:
        itens = list(itens)

        # Pedido com um item só não forma carrinho
        if len(itens) < 2:
            continue

        for escondido in itens:
            carrinho = [item for item in itens if item != escondido]
            casos.append((carrinho, escondido))

    return casos


def calcular_percentual(parte, total):
    """Retorna o percentual com uma casa decimal, ou 0 quando não há total."""
    return round(parte / total * 100, 1) if total else 0


def avaliar(casos, regras, populares, completar=True):
    """Compara o recomendador com a referência dos mais pedidos nos casos de teste."""
    acertos_modelo = 0
    acertos_referencia = 0
    cobertos = 0
    acertos_modelo_cobertos = 0
    acertos_referencia_cobertos = 0
    lifts = []

    for carrinho, escondido in casos:
        sugestoes = recomendar(carrinho, regras, populares, completar=completar)
        referencia = sugerir_populares(carrinho, populares)

        acertou_modelo = escondido in [sugestao["item"] for sugestao in sugestoes]
        acertou_referencia = escondido in [sugestao["item"] for sugestao in referencia]
        acertos_modelo += acertou_modelo
        acertos_referencia += acertou_referencia

        # Casos em que pelo menos uma regra se aplicou
        com_regra = [sugestao for sugestao in sugestoes if sugestao["origem"] == "regra"]
        if com_regra:
            cobertos += 1
            acertos_modelo_cobertos += acertou_modelo
            acertos_referencia_cobertos += acertou_referencia
            lifts.extend(sugestao["lift"] for sugestao in com_regra)

    total = len(casos)
    return {
        "casos": total,
        "hit_rate_modelo_%": calcular_percentual(acertos_modelo, total),
        "hit_rate_referencia_%": calcular_percentual(acertos_referencia, total),
        "cobertura_%": calcular_percentual(cobertos, total),
        "hit_rate_modelo_com_regra_%": calcular_percentual(acertos_modelo_cobertos, cobertos),
        "hit_rate_referencia_com_regra_%": calcular_percentual(acertos_referencia_cobertos, cobertos),
        "lift_medio": round(sum(lifts) / len(lifts), 2) if lifts else 0,
    }
