"""Sugestões de itens para um carrinho a partir das regras de associação."""

import pandas as pd

from modelo.regras import CAMINHO_PEDIDOS_LIMPOS, CAMINHO_REGRAS

MAXIMO_SUGESTOES = 3
SEPARADOR_ITENS = " + "


def carregar_regras(caminho=CAMINHO_REGRAS):
    """Lê as regras salvas, com o antecedente como conjunto de itens."""
    regras = pd.read_csv(caminho)
    regras["antecedente"] = regras["antecedente"].str.split(SEPARADOR_ITENS, regex=False).apply(set)
    return regras


def carregar_populares(caminho=CAMINHO_PEDIDOS_LIMPOS):
    """Retorna os itens do mais pedido para o menos pedido."""
    pedidos = pd.read_csv(caminho)
    return pedidos["item"].value_counts().index.tolist()


def recomendar(carrinho, regras, populares, maximo=MAXIMO_SUGESTOES):
    """Retorna até `maximo` sugestões para o carrinho, cada uma com a regra que a gerou."""
    carrinho = set(carrinho)

    # Regras com o antecedente contido no carrinho
    aplicaveis = regras[regras["antecedente"].apply(lambda itens: itens <= carrinho)]

    # Sem itens que já estão no carrinho (RN-02)
    aplicaveis = aplicaveis[~aplicaveis["consequente"].isin(carrinho)]

    # Ordem por lift, com desempate pela confiança (RN-05)
    aplicaveis = aplicaveis.sort_values(["lift", "confianca"], ascending=False)

    # Melhor regra de cada item sugerido
    aplicaveis = aplicaveis.drop_duplicates(subset="consequente")

    sugestoes = []
    for regra in aplicaveis.head(maximo).itertuples():
        sugestoes.append({
            "item": regra.consequente,
            "origem": "regra",
            "antecedente": sorted(regra.antecedente),
            "suporte": regra.suporte,
            "confianca": regra.confianca,
            "lift": regra.lift,
        })

    # Sem regra aplicável: itens mais pedidos fora do carrinho (RN-06)
    if not sugestoes:
        for item in populares:
            if item not in carrinho:
                sugestoes.append({"item": item, "origem": "popular"})
            if len(sugestoes) == maximo:
                break

    return sugestoes
