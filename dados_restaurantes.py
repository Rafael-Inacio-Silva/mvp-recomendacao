"""Catálogo tratado de restaurantes, carregado uma vez e mantido em memória com o índice de cada cidade."""

import os
from functools import lru_cache

import pandas as pd

from cidades import ARQUIVO_TRATADO, CIDADES, LOJAS_PARCEIRAS
from lojas import LOJAS
from modelo.restaurantes import montar_indice


class CatalogoIndisponivel(Exception):
    """O catálogo tratado ainda não foi gerado."""


@lru_cache(maxsize=1)
def carregar_catalogo():
    if not os.path.exists(ARQUIVO_TRATADO):
        raise CatalogoIndisponivel(f"{ARQUIVO_TRATADO} não encontrado")
    return pd.read_csv(ARQUIVO_TRATADO, encoding="utf-8")


def vincular_lojas(restaurantes, cidade):
    """Troca o nome dos restaurantes parceiros pelo da loja e guarda o identificador dela, usado no link."""
    restaurantes = restaurantes.copy()
    parceiros = LOJAS_PARCEIRAS.get(cidade, {})
    restaurantes["loja"] = restaurantes["nome"].map(parceiros)
    vinculados = restaurantes["loja"].notna()
    restaurantes.loc[vinculados, "nome"] = restaurantes.loc[vinculados, "loja"].map(LOJAS)
    return restaurantes


@lru_cache(maxsize=len(CIDADES))
def indice_da_cidade(cidade):
    """Índice TF-IDF da cidade, montado na primeira busca e reaproveitado nas seguintes."""
    catalogo = carregar_catalogo()
    return montar_indice(vincular_lojas(catalogo[catalogo["cidade"] == cidade], cidade))
