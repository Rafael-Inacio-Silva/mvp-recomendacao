"""Testes da montagem do assistente (fontes, prompts e etapas), sem chamar o LLM."""

from datetime import datetime
from types import SimpleNamespace

import pytest

from agente.fontes import texto_cardapio, texto_combinacoes, texto_loja
from agente.orquestrador import ANALISTAS, ESQUEMAS, Conversa
from agente.prompts import (
    ESTAGIOS,
    FUSO,
    descrever_agora,
    instrucoes_analista,
    instrucoes_orquestrador,
    ler_estagio,
    referencias_data,
)
from dados_loja import carregar_dados_loja
from tests.conftest import precisa_dos_dados

pytestmark = precisa_dos_dados

AGORA = datetime(2026, 11, 24, 19, 30, tzinfo=FUSO)


@pytest.fixture
def indiano():
    return carregar_dados_loja("indiano")


def test_ferramentas_do_orquestrador():
    assert [esquema["name"] for esquema in ESQUEMAS] == list(ANALISTAS) + ["avancar_estagio"]
    assert [analista.nome for analista in ANALISTAS.values()] == ["cardapio", "combinacoes", "loja"]


def test_cardapio_com_todos_os_itens_do_mais_pedido_para_o_menos_pedido():
    linhas = texto_cardapio("mexicano").splitlines()
    assert len(linhas) == 1 + 45
    assert linhas[1].startswith("Bowl de Frango | Bowls | ")


def test_combinacoes_com_a_cada_100_pedidos(indiano):
    texto = texto_combinacoes("mexicano")
    assert "- pedidos com Nachos + Água Mineral → Bowl de Frango: 79 de cada 100 pedidos" in texto
    assert "Itens mais pedidos da casa, em ordem: Bowl de Frango, Burrito de Frango" in texto

    linhas = [linha for linha in texto_combinacoes("indiano").splitlines() if linha.startswith("- pedidos com")]
    assert len(linhas) == len(indiano.regras)


def test_loja_com_o_documento_da_empresa():
    assert texto_loja("indiano").startswith("# Casa Masala Cozinha Indiana")


def test_estagios_com_nome_objetivo_e_instrucao():
    nomes = [ler_estagio(numero)["nome"] for numero in ESTAGIOS]
    assert nomes == ["Conexão", "Atendimento", "Fechamento"]
    assert all(ler_estagio(numero)["objetivo"] for numero in ESTAGIOS)
    # Só a última etapa não tem critério de avanço
    assert all("Critério de avanço" in ler_estagio(numero)["instrucao"] for numero in ESTAGIOS[:-1])


@pytest.mark.parametrize("estagio", ESTAGIOS)
def test_orquestrador_recebe_so_a_etapa_atual(indiano, estagio):
    texto = instrucoes_orquestrador(indiano, estagio, AGORA)
    etapa = ler_estagio(estagio)

    assert f"Etapa atual: {estagio} — {etapa['nome']}" in texto
    # A instrução das outras etapas não entra no prompt
    outras = [ler_estagio(numero)["objetivo"] for numero in ESTAGIOS if numero != estagio]
    assert all(objetivo not in texto for objetivo in outras)
    assert "{{" not in texto and "Maya" in texto and "Casa Masala Cozinha Indiana" in texto


def test_analistas_recebem_os_dados_da_sua_area(indiano):
    for analista in ANALISTAS.values():
        conteudo = analista.fonte("indiano")
        texto = instrucoes_analista(analista.nome, indiano, conteudo, AGORA)
        assert "{{" not in texto
        assert conteudo in texto
        assert "Casa Masala Cozinha Indiana" in texto


def test_datas_de_referencia():
    assert descrever_agora(AGORA) == "terça-feira, 24/11/2026, 19:30 (horário de São Paulo)"
    linhas = referencias_data(AGORA).splitlines()
    assert linhas[0] == "- hoje: terça-feira, 24/11/2026"
    assert linhas[1] == "- amanhã: quarta-feira, 25/11/2026"
    assert linhas[6] == "- daqui a 6 dias: segunda-feira, 30/11/2026"


def test_etapa_so_avanca(indiano):
    conversa = Conversa(cliente=None, dados=indiano)

    def pedido(estagio):
        return SimpleNamespace(arguments=f'{{"estagio": {estagio}}}')

    assert conversa.estagio == 1
    assert conversa._avancar_estagio(pedido(2)).startswith("Etapa atual: 2 — Atendimento")
    assert conversa._avancar_estagio(pedido(1)).startswith("A etapa continua 2")
    assert conversa._avancar_estagio(pedido(3)).startswith("Etapa atual: 3 — Fechamento")
    assert conversa.estagio == 3
