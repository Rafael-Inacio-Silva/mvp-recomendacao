"""Testes da explicação das sugestões (RN-07, RN-08 e RNF-04)."""

import os

import pytest

from lojas import LOJAS, caminho
from modelo.explicacao import FRASE_POPULAR, MAXIMO_PALAVRAS, explicar
from modelo.recomendador import carregar_regras


def test_frase_da_regra():
    # RN-07
    sugestao = {"item": "Bowl de Frango", "origem": "regra", "antecedente": ["Água Mineral"], "confianca": 0.4225}
    assert explicar(sugestao) == "42 de cada 100 pedidos com Água Mineral também têm Bowl de Frango"


def test_frase_com_varios_itens_no_carrinho():
    # RN-07
    dois = {"item": "Nachos", "origem": "regra", "antecedente": ["Bowl", "Água"], "confianca": 0.43}
    tres = {"item": "Papadum", "origem": "regra", "antecedente": ["A", "B", "C"], "confianca": 0.9}
    assert explicar(dois) == "43 de cada 100 pedidos com Bowl e Água também têm Nachos"
    assert explicar(tres) == "90 de cada 100 pedidos com A, B e C também têm Papadum"


def test_frase_dos_mais_pedidos():
    # RN-08
    assert explicar({"item": "Bowl de Frango", "origem": "popular"}) == FRASE_POPULAR


@pytest.mark.parametrize("loja", list(LOJAS))
def test_frases_reais_com_ate_20_palavras(loja):
    # RNF-04, com as regras geradas por gerar_regras.py
    arquivo = caminho(loja, "regras.csv")
    if not os.path.exists(arquivo):
        pytest.skip(f"{arquivo} não encontrado; execute gerar_regras.py")

    for regra in carregar_regras(arquivo):
        sugestao = {
            "item": regra["consequente"],
            "origem": "regra",
            "antecedente": sorted(regra["antecedente"]),
            "confianca": regra["confianca"],
        }
        assert len(explicar(sugestao).split()) <= MAXIMO_PALAVRAS
