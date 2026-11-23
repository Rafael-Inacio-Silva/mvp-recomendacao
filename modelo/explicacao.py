"""Frase de explicação de cada sugestão, montada a partir da regra que a gerou."""

FRASE_POPULAR = "Um dos itens mais pedidos da casa"
MAXIMO_PALAVRAS = 20


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

    # Confiança da regra como contagem a cada 100 pedidos (RN-07)
    a_cada_100 = round(sugestao["confianca"] * 100)
    antecedente = juntar_itens(sugestao["antecedente"])
    return f"{a_cada_100} de cada 100 pedidos com {antecedente} também têm {sugestao['item']}"
