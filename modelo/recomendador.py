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
    """Converte as regras formatadas em uma lista, com o antecedente como conjunto de itens."""
    lista = regras.to_dict("records")
    for regra in lista:
        regra["antecedente"] = set(regra["antecedente"].split(SEPARADOR_ITENS))
    return lista


def carregar_regras(caminho):
    """Lê as regras salvas e retorna a lista usada pelo recomendador."""
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

    # Regras com o antecedente contido no carrinho e o item sugerido fora dele (RN-02)
    aplicaveis = [
        regra for regra in regras
        if regra["antecedente"] <= carrinho and regra["consequente"] not in carrinho
    ]

    # Ordem por confiança, com desempate pelo lift (RN-05)
    principal, desempate = ORDENACAO[criterio]
    aplicaveis.sort(key=lambda regra: (regra[principal], regra[desempate]), reverse=True)

    sugestoes = []
    for regra in aplicaveis:
        # Melhor regra de cada item sugerido
        if regra["consequente"] in [sugestao["item"] for sugestao in sugestoes]:
            continue

        sugestoes.append({
            "item": regra["consequente"],
            "origem": "regra",
            "antecedente": sorted(regra["antecedente"]),
            "suporte": regra["suporte"],
            "confianca": regra["confianca"],
            "lift": regra["lift"],
        })
        if len(sugestoes) == maximo:
            break

    # Vagas restantes com os mais pedidos fora do carrinho e das sugestões (RN-06)
    if completar or not sugestoes:
        ja_usados = carrinho | {sugestao["item"] for sugestao in sugestoes}
        sugestoes += sugerir_populares(ja_usados, populares, maximo - len(sugestoes))

    return sugestoes
