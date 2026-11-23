"""Testes da validação do carrinho (RN-09)."""

import copy

import pytest

from modelo.validacao import validar_carrinho

CARDAPIO = ["Bowl de Frango", "Água Mineral", "Nachos"]


def test_carrinho_valido_com_nomes_normalizados():
    resultado = validar_carrinho(["  bowl de frango ", "ÁGUA MINERAL"], CARDAPIO)
    assert resultado == {"ok": True, "value": ["Bowl de Frango", "Água Mineral"]}


def test_item_repetido_conta_uma_vez():
    # RN-01
    resultado = validar_carrinho(["Nachos", "nachos", "Nachos"], CARDAPIO)
    assert resultado == {"ok": True, "value": ["Nachos"]}


@pytest.mark.parametrize("carrinho, codigo", [
    (None, "null"),
    ("Nachos", "invalid_type"),
    ({"item": "Nachos"}, "invalid_type"),
    (42, "invalid_type"),
    ([], "empty"),
])
def test_carrinho_invalido(carrinho, codigo):
    assert validar_carrinho(carrinho, CARDAPIO) == {
        "ok": False,
        "errors": [{"field": "carrinho", "code": codigo}],
    }


def test_todos_os_erros_dos_itens_em_ordem():
    resultado = validar_carrinho(["Nachos", None, 7, "   ", "Pizza", True], CARDAPIO)
    assert resultado == {
        "ok": False,
        "errors": [
            {"field": "carrinho[1]", "code": "null"},
            {"field": "carrinho[2]", "code": "invalid_type"},
            {"field": "carrinho[3]", "code": "empty"},
            {"field": "carrinho[4]", "code": "unknown_item"},
            {"field": "carrinho[5]", "code": "invalid_type"},
        ],
    }


def test_nao_altera_a_entrada_nem_repete_o_valor_recebido():
    carrinho = ["Pizza de Calabresa", " nachos "]
    copia = copy.deepcopy(carrinho)
    resultado = validar_carrinho(carrinho, CARDAPIO)

    assert carrinho == copia
    assert "Pizza de Calabresa" not in str(resultado)
