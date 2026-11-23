"""Testes das ferramentas dos especialistas e da montagem dos prompts, sem chamar o LLM."""

from datetime import datetime

import pytest

from agente.ferramentas import BUSCAR_PRODUTOS, buscar_produtos, executar, itens_que_saem_junto
from agente.orquestrador import ESPECIALISTAS, ESQUEMAS
from agente.prompts import FUSO, descrever_agora, instrucoes_especialista, instrucoes_orquestrador
from dados_loja import carregar_dados_loja
from tests.conftest import precisa_dos_dados

pytestmark = precisa_dos_dados


@pytest.fixture
def mexicano():
    return carregar_dados_loja("mexicano")


@pytest.fixture
def indiano():
    return carregar_dados_loja("indiano")


def itens(resultado):
    return [produto["item"] for produto in resultado["produtos"]]


def test_busca_aceita_plural_e_maiusculas(mexicano):
    assert itens(buscar_produtos(mexicano, "BURRITOS"))[0] == "Burrito de Frango"
    assert buscar_produtos(mexicano, "burritos")["encontrados"] == 6


def test_busca_pela_descricao(mexicano):
    vegetarianos = itens(buscar_produtos(mexicano, "vegetariana"))
    assert "Burrito Vegetariano" in vegetarianos
    assert all("Frango" not in item for item in vegetarianos)


def test_busca_sem_resultado(indiano):
    assert buscar_produtos(indiano, "pizza")["encontrados"] == 0


def test_busca_vazia_devolve_as_categorias(indiano):
    resultado = buscar_produtos(indiano, "  ")
    assert resultado["encontrados"] == 0
    assert "Biryanis" in resultado["categorias"]


def test_combinacoes_com_a_cada_100_pedidos(mexicano):
    resultado = itens_que_saem_junto(mexicano, ["bowl de frango", "Água Mineral"])
    assert resultado["ok"]
    assert resultado["sugestoes"][0] == {
        "item": "Nachos",
        "pedidos_com": ["Bowl de Frango", "Água Mineral"],
        "a_cada_100_pedidos": 43,
    }


def test_combinacoes_com_nome_incompleto_sugere_parecidos(indiano):
    resultado = itens_que_saem_junto(indiano, ["biryani"])
    assert not resultado["ok"]
    # O mais pedido aparece primeiro
    assert resultado["nao_encontrados"][0]["parecidos"][0] == "Biryani de Frango"


def test_executar_com_argumentos_invalidos_nao_lanca_excecao(mexicano):
    assert "erro" in executar(BUSCAR_PRODUTOS, "{nao e json", mexicano)
    assert "erro" in executar(BUSCAR_PRODUTOS, '{"outro": "campo"}', mexicano)


def test_um_especialista_para_cada_ferramenta_do_orquestrador():
    assert [esquema["name"] for esquema in ESQUEMAS] == list(ESPECIALISTAS)
    assert {especialista.nome for especialista in ESPECIALISTAS.values()} == {"cardapio", "combinacoes", "loja"}


def test_prompts_preenchidos_com_a_loja(indiano):
    agora = datetime(2026, 11, 24, 19, 30, tzinfo=FUSO)
    textos = [instrucoes_orquestrador(indiano, agora)]
    textos += [instrucoes_especialista(especialista.nome, indiano, agora) for especialista in ESPECIALISTAS.values()]

    for texto in textos:
        assert "{loja}" not in texto and "{atendente}" not in texto
        assert "Casa Masala Cozinha Indiana" in texto
        assert "terça-feira, 24/11/2026, 19:30" in texto
    assert "Maya" in textos[0]


def test_data_e_hora_em_sao_paulo():
    assert descrever_agora(datetime(2026, 11, 23, 12, 0, tzinfo=FUSO)) == "Agora em São Paulo: segunda-feira, 23/11/2026, 12:00."
