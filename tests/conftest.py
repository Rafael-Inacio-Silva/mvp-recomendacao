"""Configurações comuns dos testes."""

import os

import pytest

from dados_loja import ARQUIVOS_NECESSARIOS
from lojas import LOJAS, caminho


def arquivos_gerados():
    """True quando as duas lojas têm todos os arquivos usados pela API e pelo agente."""
    return all(os.path.exists(caminho(loja, arquivo)) for loja in LOJAS for arquivo in ARQUIVOS_NECESSARIOS)


# Testes que usam os dados reais das lojas
precisa_dos_dados = pytest.mark.skipif(
    not arquivos_gerados(),
    reason="execute analise_dados.py e gerar_regras.py antes",
)
