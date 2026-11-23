"""Testes da camada de serviço, chamada direto, sem HTTP e sem o LLM."""

import pytest

from servicos import recomendacao
from servicos.chat import ServicoChat
from servicos.erros import EntradaInvalida, NaoEncontrado
from tests.conftest import precisa_dos_dados

pytestmark = precisa_dos_dados


def campos_e_codigos(excecao):
    return [(item["field"], item["code"]) for item in excecao.value.erros]


def test_cardapio_do_mais_pedido_para_o_menos_pedido():
    itens = recomendacao.ver_cardapio("mexicano")["itens"]
    assert itens[0]["item"] == "Bowl de Frango"
    assert itens[0]["descricao"]


def test_loja_desconhecida():
    with pytest.raises(NaoEncontrado):
        recomendacao.sugerir("japones", ["Nachos"])


def test_carrinho_invalido_com_codigo_e_texto():
    with pytest.raises(EntradaInvalida) as excecao:
        recomendacao.sugerir("mexicano", [])
    assert excecao.value.erros == [{"field": "carrinho", "code": "empty", "message": "Campo vazio."}]


def test_chat_valida_antes_de_chamar_o_assistente():
    with pytest.raises(EntradaInvalida) as excecao:
        ServicoChat().responder("mexicano", "abc", "   ")
    assert campos_e_codigos(excecao) == [("conversa_id", "invalid_type"), ("mensagem", "empty")]


def test_chat_mensagem_longa_demais():
    with pytest.raises(EntradaInvalida) as excecao:
        ServicoChat().responder("mexicano", "conversa-0001", "a" * 1001)
    assert campos_e_codigos(excecao) == [("mensagem", "too_long")]
