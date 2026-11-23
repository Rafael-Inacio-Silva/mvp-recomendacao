"""Arquivos de cada loja carregados uma vez e mantidos em memória pela API e pelo agente."""

import os
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from lojas import ATENDENTES, LOJAS, caminho
from modelo.explicacao import carregar_cardapio
from modelo.recomendador import carregar_populares, carregar_regras

# Arquivos gerados pelos scripts e arquivos recebidos do restaurante
ARQUIVOS_NECESSARIOS = ["pedidos_limpos.csv", "regras.csv", "cardapio.csv", "produtos.csv", "loja.md"]


class LojaIndisponivel(Exception):
    """A loja não existe ou ainda não tem os arquivos gerados."""


@dataclass(frozen=True)
class DadosLoja:
    """Tudo o que a API e o agente usam de uma loja."""

    loja: str
    nome: str
    atendente: str
    regras: list
    populares: list
    cardapio: dict
    produtos: pd.DataFrame
    informacoes: str


@lru_cache(maxsize=None)
def carregar_dados_loja(loja):
    """Lê os arquivos da loja uma vez; nas chamadas seguintes, devolve o que já está em memória."""
    if loja not in LOJAS:
        raise LojaIndisponivel(f"loja desconhecida: {loja}")

    faltando = [arquivo for arquivo in ARQUIVOS_NECESSARIOS if not os.path.exists(caminho(loja, arquivo))]
    if faltando:
        raise LojaIndisponivel(f"arquivos não encontrados para {loja}: {', '.join(faltando)}")

    with open(caminho(loja, "loja.md"), encoding="utf-8") as arquivo:
        informacoes = arquivo.read()

    return DadosLoja(
        loja=loja,
        nome=LOJAS[loja],
        atendente=ATENDENTES[loja],
        regras=carregar_regras(caminho(loja, "regras.csv")),
        populares=carregar_populares(caminho(loja, "pedidos_limpos.csv")),
        cardapio=carregar_cardapio(caminho(loja, "cardapio.csv")),
        produtos=pd.read_csv(caminho(loja, "produtos.csv")),
        informacoes=informacoes,
    )
