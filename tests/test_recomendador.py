"""Testes das regras de negócio do recomendador (RN-02, RN-03, RN-05 e RN-06)."""

import pandas as pd
import pytest

from modelo.recomendador import preparar_regras, recomendar

POPULARES = ["Bowl", "Burrito", "Nachos", "Refrigerante", "Água"]


@pytest.fixture
def regras():
    """Regras pequenas, no mesmo formato do regras.csv."""
    return preparar_regras(pd.DataFrame([
        {"antecedente": "Bowl", "consequente": "Nachos", "suporte": 0.10, "confianca": 0.3, "lift": 1.2},
        {"antecedente": "Bowl", "consequente": "Refrigerante", "suporte": 0.10, "confianca": 0.3, "lift": 1.5},
        {"antecedente": "Bowl", "consequente": "Água", "suporte": 0.05, "confianca": 0.5, "lift": 0.9},
        {"antecedente": "Bowl + Água", "consequente": "Nachos", "suporte": 0.02, "confianca": 0.6, "lift": 2.0},
        {"antecedente": "Nachos", "consequente": "Bowl", "suporte": 0.10, "confianca": 0.5, "lift": 1.3},
    ]))


def itens(sugestoes):
    return [sugestao["item"] for sugestao in sugestoes]


def test_item_do_carrinho_nao_e_sugerido(regras):
    # RN-02
    sugestoes = recomendar(["Bowl", "Nachos"], regras, POPULARES)
    assert not set(itens(sugestoes)) & {"Bowl", "Nachos"}


def test_no_maximo_tres_sugestoes(regras):
    # RN-03
    assert len(recomendar(["Bowl"], regras, POPULARES)) == 3
    assert len(recomendar(["Bowl"], regras, POPULARES, maximo=2)) == 2


def test_ordem_por_confianca_com_desempate_pelo_lift(regras):
    # RN-05: Água tem a maior confiança; Refrigerante e Nachos empatam e o lift decide
    assert itens(recomendar(["Bowl"], regras, POPULARES)) == ["Água", "Refrigerante", "Nachos"]


def test_item_sugerido_uma_vez_pela_melhor_regra(regras):
    # Nachos vem de duas regras; vale a de maior confiança
    sugestoes = recomendar(["Bowl", "Água"], regras, POPULARES)
    assert itens(sugestoes).count("Nachos") == 1
    assert sugestoes[0]["item"] == "Nachos"
    assert sugestoes[0]["antecedente"] == sorted(["Bowl", "Água"])


def test_vagas_restantes_com_mais_pedidos(regras):
    # RN-06: uma regra e duas vagas completadas com os mais pedidos
    sugestoes = recomendar(["Nachos"], regras, POPULARES)
    assert itens(sugestoes) == ["Bowl", "Burrito", "Refrigerante"]
    assert [sugestao["origem"] for sugestao in sugestoes] == ["regra", "popular", "popular"]


def test_carrinho_sem_regra_recebe_mais_pedidos(regras):
    # RN-06
    assert itens(recomendar(["Burrito"], regras, POPULARES)) == ["Bowl", "Nachos", "Refrigerante"]


def test_primeira_versao_nao_completa_as_vagas(regras):
    # Versão usada só na avaliação
    assert itens(recomendar(["Nachos"], regras, POPULARES, completar=False)) == ["Bowl"]


def test_criterio_lift_reordena(regras):
    # Versão usada só na avaliação: Refrigerante tem o maior lift
    assert itens(recomendar(["Bowl"], regras, POPULARES, criterio="lift")) == ["Refrigerante", "Nachos", "Água"]
