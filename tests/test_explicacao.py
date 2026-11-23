"""Testes da explicação das sugestões (RN-07 e RN-08)."""

from modelo.explicacao import FRASE_POPULAR, explicar


def test_frase_da_regra():
    # RN-07
    sugestao = {"item": "Bowl de Frango", "origem": "regra", "antecedente": ["Água Mineral"]}
    assert explicar(sugestao) == "Já que você escolheu Água Mineral, que tal incluir Bowl de Frango no pedido?"


def test_frase_com_varios_itens_no_carrinho():
    # RN-07
    dois = {"item": "Nachos", "origem": "regra", "antecedente": ["Bowl de Frango", "Água Mineral"]}
    tres = {"item": "Papadum", "origem": "regra", "antecedente": ["A", "B", "C"]}
    assert explicar(dois) == "Já que você escolheu Bowl de Frango e Água Mineral, que tal incluir Nachos no pedido?"
    assert explicar(tres) == "Já que você escolheu A, B e C, que tal incluir Papadum no pedido?"


def test_frase_dos_mais_pedidos():
    # RN-08
    assert explicar({"item": "Bowl de Frango", "origem": "popular"}) == FRASE_POPULAR
