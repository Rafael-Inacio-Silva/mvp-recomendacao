"""Frase de explicação de cada sugestão, montada a partir da regra que a gerou."""

FRASE_POPULAR = "Um dos itens mais pedidos da casa"


def juntar_itens(itens):
    """Junta os nomes em texto: 'A', 'A e B' ou 'A, B e C'."""
    itens = list(itens)
    if len(itens) == 1:
        return itens[0]
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def explicar(sugestao):
    """Retorna a frase da sugestão (RN-07 e RN-08)."""
    # Sugestão dos mais vendidos, sem regra (RN-08)
    if sugestao["origem"] == "popular":
        return FRASE_POPULAR

    # Itens do carrinho que formam a regra e item sugerido (RN-07)
    escolhidos = juntar_itens(sugestao["antecedente"])
    return f"Já que você escolheu {escolhidos}, que tal incluir {sugestao['item']} no pedido?"
