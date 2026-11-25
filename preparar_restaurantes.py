"""Gera o catálogo tratado de restaurantes das cidades atendidas, a partir do catálogo recebido."""

import os

from cidades import ARQUIVO_ORIGINAL, ARQUIVO_TRATADO
from pipeline.restaurantes import (
    carregar_restaurantes,
    montar_catalogo,
    mostrar_duplicados,
    mostrar_exploracao,
    mostrar_valores_problematicos,
    mostrar_visao_geral,
    tratar_duplicados,
    tratar_valores,
)


def executar():
    if not os.path.exists(ARQUIVO_ORIGINAL):
        raise SystemExit(f"{ARQUIVO_ORIGINAL} não encontrado (ver README); o catálogo tratado já vem no repositório.")

    # Etapa 1: carregamento das cidades atendidas
    df = carregar_restaurantes(ARQUIVO_ORIGINAL)
    mostrar_visao_geral(df)

    # Etapa 2: valores ausentes e inválidos
    mostrar_valores_problematicos(df)
    df = tratar_valores(df)

    # Etapa 3: duplicados
    mostrar_duplicados(df)
    df = tratar_duplicados(df)

    # Etapa 4: catálogo tratado
    catalogo = montar_catalogo(df)
    mostrar_exploracao(catalogo)

    catalogo.to_csv(ARQUIVO_TRATADO, index=False)
    print(f"\nCatálogo tratado salvo em {ARQUIVO_TRATADO} ({os.path.getsize(ARQUIVO_TRATADO) / 1e6:.1f} MB)")


if __name__ == "__main__":
    executar()
