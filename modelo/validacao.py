"""Validação do carrinho antes da recomendação."""


def validar_carrinho(carrinho, itens_do_cardapio):
    """Valida e normaliza o carrinho (RN-09).

    Retorna {"ok": True, "value": [itens]} ou {"ok": False, "errors": [{"field": ..., "code": ...}]}.
    Não lança exceção, não altera a entrada e não repete nos erros o valor recebido.
    """
    erros = []

    def falha():
        return {"ok": False, "errors": erros}

    # Carrinho como um todo
    if carrinho is None:
        erros.append({"field": "carrinho", "code": "null"})
        return falha()

    if not isinstance(carrinho, (list, tuple)):
        erros.append({"field": "carrinho", "code": "invalid_type"})
        return falha()

    if len(carrinho) == 0:
        erros.append({"field": "carrinho", "code": "empty"})
        return falha()

    # Nome oficial de cada item, para comparar sem diferença de maiúsculas
    cardapio = {}
    for nome in itens_do_cardapio:
        if isinstance(nome, str):
            cardapio[nome.strip().lower()] = nome

    itens = []
    for posicao, item in enumerate(carrinho):
        campo = f"carrinho[{posicao}]"

        if item is None:
            erros.append({"field": campo, "code": "null"})
        elif not isinstance(item, str):
            erros.append({"field": campo, "code": "invalid_type"})
        elif not item.strip():
            erros.append({"field": campo, "code": "empty"})
        elif item.strip().lower() not in cardapio:
            erros.append({"field": campo, "code": "unknown_item"})
        else:
            # Item repetido conta uma vez (RN-01)
            nome = cardapio[item.strip().lower()]
            if nome not in itens:
                itens.append(nome)

    if erros:
        return falha()

    return {"ok": True, "value": itens}
