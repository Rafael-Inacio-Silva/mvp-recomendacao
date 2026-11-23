"""Testes da preparação das cestas (RN-01) e das divisões usadas na avaliação."""

import pandas as pd

from modelo.avaliacao import dividir_em_dobras, dividir_pedidos, montar_casos
from modelo.regras import montar_cestas
from pipeline.etapa3_duplicados import tratar_duplicados


def pedidos_exemplo():
    return pd.DataFrame({
        "id_pedido": [1, 1, 1, 2, 2, 3, 4, 4, 5, 5],
        "item": ["Bowl", "Bowl", "Nachos", "Burrito", "Água", "Bowl", "Nachos", "Água", "Bowl", "Água"],
    })


def test_item_repetido_conta_uma_vez():
    # RN-01
    limpos = tratar_duplicados(pedidos_exemplo())
    assert (limpos["id_pedido"] == 1).sum() == 2

    cestas = montar_cestas(pedidos_exemplo())
    assert cestas.loc[1, "Bowl"]
    assert cestas.loc[1].sum() == 2


def test_casos_escondem_cada_item_uma_vez():
    casos = montar_casos(tratar_duplicados(pedidos_exemplo()))

    # Pedido 3 tem um item só e não forma carrinho; os outros 4 têm 2 itens cada
    assert len(casos) == 8
    assert (["Nachos"], "Bowl") in casos
    assert (["Bowl"], "Nachos") in casos


def test_divisao_unica_sem_pedido_nos_dois_lados():
    treino, teste = dividir_pedidos(pedidos_exemplo(), proporcao_teste=0.4)
    assert not set(treino["id_pedido"]) & set(teste["id_pedido"])
    assert teste["id_pedido"].nunique() == 2


def test_cada_pedido_no_teste_de_uma_dobra():
    pedidos = pedidos_exemplo()
    dobras = dividir_em_dobras(pedidos, dobras=5)

    vezes_no_teste = pd.concat([teste.drop_duplicates("id_pedido") for _, teste in dobras])["id_pedido"]
    assert sorted(vezes_no_teste) == sorted(pedidos["id_pedido"].unique())

    for treino, teste in dobras:
        assert not set(treino["id_pedido"]) & set(teste["id_pedido"])
