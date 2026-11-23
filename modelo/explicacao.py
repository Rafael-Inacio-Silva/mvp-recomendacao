"""Frase de explicação de cada sugestão, montada a partir da regra que a gerou."""

import os

import pandas as pd

FRASE_POPULAR = "Um dos itens mais pedidos da casa"


def carregar_cardapio(caminho):
    """Retorna o dicionário item -> forma na frase; vazio quando o arquivo não existe."""
    if not os.path.exists(caminho):
        return {}
    cardapio = pd.read_csv(caminho)
    return dict(zip(cardapio["item"], cardapio["na_frase"]))


def juntar_itens(itens):
    """Junta os nomes em texto: 'A', 'A e B' ou 'A, B e C'."""
    itens = list(itens)
    if len(itens) == 1:
        return itens[0]
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def explicar(sugestao, cardapio=None):
    """Retorna a frase da sugestão (RN-07 e RN-08).

    Com o cardápio da etapa 6, os itens aparecem com artigo; sem ele, com o nome do cardápio.
    """
    cardapio = cardapio or {}

    # Sugestão dos mais vendidos, sem regra (RN-08)
    if sugestao["origem"] == "popular":
        return FRASE_POPULAR

    # Itens do carrinho que formam a regra e item sugerido (RN-07)
    escolhidos = juntar_itens(cardapio.get(item, item) for item in sugestao["antecedente"])
    sugerido = cardapio.get(sugestao["item"], sugestao["item"])
    return f"Já que você escolheu {escolhidos}, que tal incluir {sugerido} no pedido?"
