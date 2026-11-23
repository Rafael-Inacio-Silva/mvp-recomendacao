"""Sugestões de itens para um carrinho a partir das regras de associação."""

import pandas as pd

MAXIMO_SUGESTOES = 3
SEPARADOR_ITENS = " + "

# Ordem das sugestões: critério principal e desempate
ORDENACAO = {
    "confianca": ["confianca", "lift"],
    "lift": ["lift", "confianca"],
}


def preparar_regras(regras):
    """Converte o antecedente das regras formatadas em conjunto de itens."""
    regras = regras.copy()
    regras["antecedente"] = regras["antecedente"].str.split(SEPARADOR_ITENS, regex=False).apply(set)
    return regras


def carregar_regras(caminho):
    """Lê as regras salvas, com o antecedente como conjunto de itens."""
    return preparar_regras(pd.read_csv(caminho))


def calcular_populares(pedidos):
    """Retorna os itens do mais pedido para o menos pedido."""
    return pedidos["item"].value_counts().index.tolist()


def carregar_populares(caminho):
    """Lê a base limpa e retorna os itens do mais pedido para o menos pedido."""
    return calcular_populares(pd.read_csv(caminho))


def sugerir_populares(carrinho, populares, maximo=MAXIMO_SUGESTOES):
    """Retorna os itens mais pedidos que não estão no carrinho."""
    sugestoes = []
    for item in populares:
        if len(sugestoes) == maximo:
            break
        if item not in carrinho:
            sugestoes.append({"item": item, "origem": "popular"})
    return sugestoes


def recomendar(carrinho, regras, populares, maximo=MAXIMO_SUGESTOES, criterio="confianca", completar=True):
    """Retorna até `maximo` sugestões para o carrinho, cada uma com a regra que a gerou.

    `criterio="lift"` e `completar=False` reproduzem as primeiras versões, usadas na avaliação.
    """
    carrinho = set(carrinho)

    # Regras com o antecedente contido no carrinho
    aplicaveis = regras[regras["antecedente"].apply(lambda itens: itens <= carrinho)]

    # Sem itens que já estão no carrinho (RN-02)
    aplicaveis = aplicaveis[~aplicaveis["consequente"].isin(carrinho)]

    # Ordem por confiança, com desempate pelo lift (RN-05)
    aplicaveis = aplicaveis.sort_values(ORDENACAO[criterio], ascending=False)

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

    # Vagas restantes com os mais pedidos fora do carrinho e das sugestões (RN-06)
    if completar or not sugestoes:
        ja_usados = carrinho | {sugestao["item"] for sugestao in sugestoes}
        sugestoes += sugerir_populares(ja_usados, populares, maximo - len(sugestoes))

    return sugestoes
