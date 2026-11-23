"""Testes do controller: rotas, status HTTP e formato das respostas, sem chamar o LLM."""

import pytest
from fastapi.testclient import TestClient

import api
from servicos.chat import ServicoChat
from tests.conftest import precisa_dos_dados

pytestmark = precisa_dos_dados


@pytest.fixture
def cliente():
    return TestClient(api.app)


def campos_e_codigos(resposta):
    return [(item["field"], item["code"]) for item in resposta.json()["errors"]]


def test_saude(cliente):
    assert cliente.get("/api/saude").json() == {"status": "ok"}


def test_lojas(cliente):
    lojas = [loja["loja"] for loja in cliente.get("/api/lojas").json()]
    assert lojas == ["mexicano", "indiano"]


def test_cardapio(cliente):
    resposta = cliente.get("/api/lojas/mexicano/cardapio")
    assert resposta.status_code == 200
    assert len(resposta.json()["itens"]) == 45


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
            {"field": "carrinho[0]", "code": "unknown_item", "message": "Item fora do cardápio da loja."},
            {"field": "carrinho[1]", "code": "null", "message": "Campo obrigatório não informado."},
        ],
    }


def test_loja_desconhecida(cliente):
    resposta = cliente.get("/api/lojas/japones/cardapio")
    assert resposta.status_code == 404
    assert campos_e_codigos(resposta) == [("loja", "not_found")]


@pytest.mark.parametrize("rota", ["sugestoes", "chat"])
def test_corpo_que_nao_e_objeto(cliente, rota):
    resposta = cliente.post(f"/api/lojas/mexicano/{rota}", json=["Nachos"])
    assert resposta.status_code == 400
    assert campos_e_codigos(resposta) == [("corpo", "invalid_type")]


def test_json_invalido(cliente):
    resposta = cliente.post(
        "/api/lojas/mexicano/sugestoes", content="{carrinho", headers={"Content-Type": "application/json"}
    )
    assert resposta.status_code == 400
    assert campos_e_codigos(resposta) == [("corpo", "invalid_type")]


def test_rota_e_metodo_inexistentes(cliente):
    assert campos_e_codigos(cliente.get("/api/pedidos")) == [("rota", "not_found")]
    assert cliente.put("/api/lojas").status_code == 405


def test_chat_sem_chave_da_openai(cliente, monkeypatch):
    monkeypatch.setattr(api, "servico_chat", ServicoChat())
    monkeypatch.setattr("servicos.chat.criar_cliente", lambda: None)

    resposta = cliente.post("/api/lojas/mexicano/chat", json={"conversa_id": "conversa-0001", "mensagem": "Oi"})
    assert resposta.status_code == 503
    assert campos_e_codigos(resposta) == [("assistente", "unavailable")]


def test_encerrar_chat(cliente):
    assert cliente.delete("/api/lojas/indiano/chat/conversa-0001").json() == {"ok": True}

    resposta = cliente.delete("/api/lojas/indiano/chat/abc")
    assert resposta.status_code == 400
    assert campos_e_codigos(resposta) == [("conversa_id", "invalid_type")]
