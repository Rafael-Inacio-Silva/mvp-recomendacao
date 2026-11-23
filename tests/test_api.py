"""Testes das rotas da API que não chamam o LLM."""

import pytest
from fastapi.testclient import TestClient

from api import app
from tests.conftest import precisa_dos_dados

pytestmark = precisa_dos_dados


@pytest.fixture
def cliente():
    return TestClient(app)


def test_saude(cliente):
    assert cliente.get("/api/saude").json() == {"status": "ok"}


def test_lojas(cliente):
    lojas = [loja["loja"] for loja in cliente.get("/api/lojas").json()]
    assert lojas == ["mexicano", "indiano"]


def test_cardapio_com_todos_os_itens_e_descricao(cliente):
    resposta = cliente.get("/api/lojas/mexicano/cardapio").json()
    assert len(resposta["itens"]) == 45
    assert resposta["itens"][0]["item"] == "Bowl de Frango"
    assert resposta["itens"][0]["descricao"]


def test_loja_desconhecida(cliente):
    assert cliente.get("/api/lojas/japones/cardapio").status_code == 404


def test_sugestoes_com_frase(cliente):
    resposta = cliente.post("/api/lojas/mexicano/sugestoes", json={"carrinho": [" bowl de frango", "Água Mineral"]})
    corpo = resposta.json()

    assert resposta.status_code == 200
    assert corpo["carrinho"] == ["Bowl de Frango", "Água Mineral"]
    assert len(corpo["sugestoes"]) == 3
    assert corpo["sugestoes"][0]["frase"].startswith("Já que você escolheu um bowl de frango e uma água mineral")


def test_sugestoes_barradas_pelo_validador(cliente):
    resposta = cliente.post("/api/lojas/indiano/sugestoes", json={"carrinho": ["Pizza", None]})
    assert resposta.status_code == 400
    assert resposta.json() == {
        "ok": False,
        "errors": [
            {"field": "carrinho[0]", "code": "unknown_item"},
            {"field": "carrinho[1]", "code": "null"},
        ],
    }


@pytest.mark.parametrize("rota", ["sugestoes", "chat", "chat/reiniciar"])
def test_corpo_que_nao_e_objeto(cliente, rota):
    resposta = cliente.post(f"/api/lojas/mexicano/{rota}", json=["Nachos"])
    assert resposta.status_code == 400
    assert resposta.json()["errors"] == [{"field": "corpo", "code": "invalid_type"}]


def test_chat_valida_antes_de_chamar_o_assistente(cliente):
    resposta = cliente.post("/api/lojas/mexicano/chat", json={"conversa_id": "abc", "mensagem": "   "})
    assert resposta.status_code == 400
    assert resposta.json()["errors"] == [
        {"field": "conversa_id", "code": "invalid_type"},
        {"field": "mensagem", "code": "empty"},
    ]


def test_chat_mensagem_longa_demais(cliente):
    resposta = cliente.post("/api/lojas/mexicano/chat", json={"conversa_id": "conversa-0001", "mensagem": "a" * 1001})
    assert resposta.json()["errors"] == [{"field": "mensagem", "code": "too_long"}]


def test_reiniciar_chat(cliente):
    resposta = cliente.post("/api/lojas/indiano/chat/reiniciar", json={"conversa_id": "conversa-0001"})
    assert resposta.json() == {"ok": True}
