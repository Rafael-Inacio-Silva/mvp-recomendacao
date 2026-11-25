"""Testes da recomendação de restaurantes: pipeline, modelo, validação e API."""

import math
import os

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import api
from cidades import ARQUIVO_TRATADO
from modelo.restaurantes import montar_indice, pesos_efetivos, recomendar_restaurantes
from modelo.validacao_restaurantes import validar_busca
from pipeline.restaurantes import extrair_etiquetas, tratar_valores

precisa_do_catalogo = pytest.mark.skipif(not os.path.exists(ARQUIVO_TRATADO), reason="execute preparar_restaurantes.py antes")


def catalogo(*linhas):
    """Catálogo pequeno: (nome, culinária, nota, frete, tempo)."""
    return pd.DataFrame([
        {"cidade": "teste", "nome": nome, "culinaria": culinaria, "nota": nota, "frete": frete, "tempo": tempo,
         "faixa_preco": 1, "pedido_minimo": 20.0, "etiquetas": ""}
        for nome, culinaria, nota, frete, tempo in linhas
    ])


def nomes(resultado):
    return [restaurante["nome"] for restaurante in resultado]


# ---------------------------------------------------------------- pipeline


def test_etiquetas_uteis_viram_palavras_e_codigos_de_campanha_saem():
    assert extrair_etiquetas("NOVO $$ PRATOS_VEGETARIANOS_FEV21 $$ BOMEBARATO_CUPOM $$ BOM_BARATO") == "vegetariano; bom e barato"
    assert extrair_etiquetas("CPGN_1811_BLK_NOV $$ JETSKI_BURGER_20AGO") == ""
    assert extrair_etiquetas(float("nan")) == ""


def test_tratamento_de_valores_invalidos():
    bruto = pd.DataFrame({
        "rating": [0.0, 4.5, 4.0, 5.0],
        "delivery_time": [30, -1, 300, 40],
        "minimumOrderValue": [20.0, 15.0, 15.0, 99999999.99],
    })
    tratado = tratar_valores(bruto)
    # Tempo impossível sai da base; nota 0 e pedido mínimo absurdo viram ausentes
    assert list(tratado["delivery_time"]) == [30, 40]
    assert math.isnan(tratado["rating"].iloc[0])
    assert math.isnan(tratado["minimumOrderValue"].iloc[1])


# ---------------------------------------------------------------- modelo


def test_so_a_culinaria_escolhida_e_no_maximo_dez():
    linhas = [(f"Pizzaria {n}", "Pizza", 4.5, 5.0, 40) for n in range(15)] + [("Sushi Bar", "Japonesa", 5.0, 0.0, 20)]
    resultado = recomendar_restaurantes(montar_indice(catalogo(*linhas)), culinaria="Pizza")
    assert len(resultado) == 10
    assert {restaurante["culinaria"] for restaurante in resultado} == {"Pizza"}


def test_frete_e_tempo_menores_vem_primeiro():
    indice = montar_indice(catalogo(("Caro e lento", "Pizza", 4.5, 15.0, 70), ("Barato e rápido", "Pizza", 4.5, 0.0, 20)))
    assert nomes(recomendar_restaurantes(indice)) == ["Barato e rápido", "Caro e lento"]


def test_sem_avaliacao_entra_com_o_primeiro_quartil():
    indice = montar_indice(catalogo(("A", "Pizza", 4.0, 5.0, 40), ("B", "Pizza", 5.0, 5.0, 40), ("Novo", "Pizza", None, 5.0, 40)))
    novo = next(restaurante for restaurante in recomendar_restaurantes(indice) if restaurante["nome"] == "Novo")
    assert not novo["avaliado"] and novo["nota"] is None
    assert novo["partes"]["avaliacao"] == pytest.approx(indice["nota_sem_avaliacao"] / 5)
    assert novo["explicacao"].startswith("Sem avaliação")


def test_texto_livre_favorece_quem_combina():
    indice = montar_indice(catalogo(("Casa do Sushi", "Japonesa", 4.0, 8.0, 50), ("Temakeria Boa", "Japonesa", 4.0, 8.0, 50)))
    resultado = recomendar_restaurantes(indice, culinaria="Japonesa", preferencia="sushi")
    assert nomes(resultado)[0] == "Casa do Sushi"
    assert resultado[0]["explicacao"].endswith("combina com “sushi”")
    assert not resultado[1]["combina_com_busca"]


def test_mesmo_nome_aparece_uma_vez_a_melhor_unidade():
    indice = montar_indice(catalogo(("Rede X", "Lanches", 4.0, 15.0, 70), ("rede x ", "Lanches", 4.0, 0.0, 20)))
    resultado = recomendar_restaurantes(indice)
    assert len(resultado) == 1 and resultado[0]["frete"] == 0.0


def test_empate_decidido_pela_nota_e_depois_pelo_nome():
    indice = montar_indice(catalogo(("B", "Pizza", 4.0, 5.0, 40), ("C", "Pizza", 5.0, 5.0, 40), ("A", "Pizza", 4.0, 5.0, 40)))
    # Só o frete pesa, e os três têm o mesmo frete: a nota desempata, e depois o nome
    assert nomes(recomendar_restaurantes(indice, pesos={"conteudo": 0, "avaliacao": 0, "frete": 1, "entrega": 0})) == ["C", "A", "B"]


def test_pesos_somam_um_e_sem_texto_o_conteudo_sai():
    assert pesos_efetivos(None, "") == pytest.approx({"conteudo": 0, "avaliacao": 0.5, "frete": 0.25, "entrega": 0.25})
    assert sum(pesos_efetivos({"conteudo": 2, "avaliacao": 1, "frete": 1, "entrega": 0}, "sushi").values()) == pytest.approx(1)
    assert pesos_efetivos({"conteudo": 1, "avaliacao": 0, "frete": 0, "entrega": 0}, "") == {
        "conteudo": 0.0, "avaliacao": 1.0, "frete": 0.0, "entrega": 0.0}


# ---------------------------------------------------------------- validação


def test_busca_valida_normaliza_culinaria_e_texto():
    resultado = validar_busca(" japonesa ", "  sushi ", {"frete": 1, "entrega": 2}, ["Japonesa", "Pizza"])
    assert resultado == {"ok": True, "value": {
        "culinaria": "Japonesa", "preferencia": "sushi",
        "pesos": {"conteudo": 0.0, "avaliacao": 0.0, "frete": 1.0, "entrega": 2.0}}}


def test_busca_invalida_lista_todos_os_erros_em_ordem():
    pesos = {"conteudo": True, "avaliacao": float("nan"), "frete": -1, "entrega": None, "cor": 1}
    resultado = validar_busca(" ", "x" * 201, pesos, ["Pizza"])
    assert resultado == {"ok": False, "errors": [
        {"field": "culinaria", "code": "empty"},
        {"field": "preferencia", "code": "too_long"},
        {"field": "pesos.conteudo", "code": "invalid_type"},
        {"field": "pesos.avaliacao", "code": "not_finite"},
        {"field": "pesos.frete", "code": "out_of_range"},
        {"field": "pesos.entrega", "code": "null"},
        {"field": "pesos.cor", "code": "unknown_field"},
    ]}


@pytest.mark.parametrize("culinaria, codigo", [(5, "invalid_type"), ("Sushi", "unknown_cuisine")])
def test_culinaria_invalida(culinaria, codigo):
    assert validar_busca(culinaria, None, None, ["Japonesa"])["errors"] == [{"field": "culinaria", "code": codigo}]


def test_pesos_todos_zero_ou_formato_errado():
    zeros = {"conteudo": 0, "avaliacao": 0, "frete": 0, "entrega": 0}
    assert validar_busca(None, None, zeros, [])["errors"] == [{"field": "pesos", "code": "out_of_range"}]
    assert validar_busca(None, None, [1, 2], [])["errors"] == [{"field": "pesos", "code": "invalid_type"}]


# ---------------------------------------------------------------- API


@pytest.fixture
def cliente():
    return TestClient(api.app)


@precisa_do_catalogo
def test_cidades_e_culinarias(cliente):
    cidades = [cidade["cidade"] for cidade in cliente.get("/api/restaurantes/cidades").json()]
    assert cidades == ["belo-horizonte", "sao-paulo", "rio-de-janeiro"]
    culinarias = cliente.get("/api/restaurantes/belo-horizonte/culinarias").json()["culinarias"]
    assert culinarias[0] == {"culinaria": "Lanches", "restaurantes": 2443}


@precisa_do_catalogo
def test_recomendacoes(cliente):
    resposta = cliente.post("/api/restaurantes/belo-horizonte/recomendacoes", json={"culinaria": "Japonesa", "preferencia": "sushi"})
    corpo = resposta.json()
    assert resposta.status_code == 200
    assert len(corpo["restaurantes"]) == 10
    assert corpo["pesos"] == {"conteudo": 0.4, "avaliacao": 0.3, "frete": 0.15, "entrega": 0.15}
    assert all(restaurante["culinaria"] == "Japonesa" for restaurante in corpo["restaurantes"])
    pontuacoes = [restaurante["pontuacao"] for restaurante in corpo["restaurantes"]]
    assert pontuacoes == sorted(pontuacoes, reverse=True)


@precisa_do_catalogo
@pytest.mark.parametrize("culinaria, loja, nome", [
    ("Mexicana", "mexicano", "Sabor na Mesa Cozinha Mexicana"),
    ("Indiana", "indiano", "Casa Masala Cozinha Indiana"),
])
def test_lojas_parceiras_no_top_10_com_link(cliente, culinaria, loja, nome):
    corpo = cliente.post("/api/restaurantes/sao-paulo/recomendacoes", json={"culinaria": culinaria}).json()
    parceiros = [r for r in corpo["restaurantes"] if r["loja"]]
    assert [(r["loja"], r["nome"]) for r in parceiros] == [(loja, nome)]


@precisa_do_catalogo
def test_cidade_nao_atendida_e_busca_invalida(cliente):
    resposta = cliente.get("/api/restaurantes/curitiba/culinarias")
    assert resposta.status_code == 404
    assert resposta.json()["errors"][0]["code"] == "not_found"

    resposta = cliente.post("/api/restaurantes/sao-paulo/recomendacoes", json={"culinaria": "Sushi"})
    assert resposta.status_code == 400
    assert resposta.json()["errors"] == [
        {"field": "culinaria", "code": "unknown_cuisine", "message": "Culinária não encontrada nesta cidade."}]
