"""Testes da montagem do assistente (fontes de dados e prompts), sem chamar o LLM."""

from datetime import datetime

import pytest

from agente.fontes import texto_cardapio, texto_combinacoes, texto_loja
from agente.orquestrador import ANALISTAS, ESQUEMAS
from agente.prompts import FUSO, descrever_agora, instrucoes_analista, instrucoes_orquestrador
from dados_loja import carregar_dados_loja
from tests.conftest import precisa_dos_dados

pytestmark = precisa_dos_dados


@pytest.fixture
def indiano():
    return carregar_dados_loja("indiano")


def test_um_analista_para_cada_ferramenta_do_orquestrador():
    assert [esquema["name"] for esquema in ESQUEMAS] == list(ANALISTAS)
    assert [analista.nome for analista in ANALISTAS.values()] == ["cardapio", "combinacoes", "loja"]


def test_cardapio_com_todos_os_itens_do_mais_pedido_para_o_menos_pedido():
    linhas = texto_cardapio("mexicano").splitlines()
    assert len(linhas) == 1 + 45
    assert linhas[1].startswith("Bowl de Frango | Bowls | ")


def test_combinacoes_com_a_cada_100_pedidos():
    texto = texto_combinacoes("mexicano")
    assert "- pedidos com Nachos + Água Mineral → Bowl de Frango: 79 de cada 100 pedidos" in texto
    assert "Itens mais pedidos da casa, em ordem: Bowl de Frango, Burrito de Frango" in texto


def test_combinacoes_com_todas_as_regras(indiano):
    linhas = [linha for linha in texto_combinacoes("indiano").splitlines() if linha.startswith("- pedidos com")]
    assert len(linhas) == len(indiano.regras)


def test_loja_com_o_documento_da_empresa():
    assert texto_loja("indiano").startswith("# Casa Masala Cozinha Indiana")


def test_prompts_preenchidos_com_a_loja_os_dados_e_a_hora(indiano):
    agora = datetime(2026, 11, 24, 19, 30, tzinfo=FUSO)
    textos = [instrucoes_orquestrador(indiano, agora)]
    for analista in ANALISTAS.values():
        textos.append(instrucoes_analista(analista.nome, indiano, analista.fonte("indiano"), agora))

    for texto in textos:
        assert "{loja}" not in texto and "{atendente}" not in texto
        assert "Casa Masala Cozinha Indiana" in texto
        assert texto.endswith("terça-feira, 24/11/2026, 19:30.")
    assert "Maya" in textos[0]
    # Cada analista recebe os dados da sua área entre <dados> e </dados>
    assert all("<dados>" in texto and "</dados>" in texto for texto in textos[1:])


def test_data_e_hora_em_sao_paulo():
    assert descrever_agora(datetime(2026, 11, 23, 12, 0, tzinfo=FUSO)) == "Agora em São Paulo: segunda-feira, 23/11/2026, 12:00."
