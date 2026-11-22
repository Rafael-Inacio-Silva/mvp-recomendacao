"""Etapa 1 do pipeline: carregamento dos dados de pedidos."""

import pandas as pd

CAMINHO_PEDIDOS = "dados/pedidos.csv"


def carregar_pedidos(caminho=CAMINHO_PEDIDOS):
    """Lê o CSV de pedidos e retorna um DataFrame."""
    return pd.read_csv(caminho, encoding="utf-8")


def mostrar_visao_geral(df):
    """Exibe dimensões, estrutura, primeiras linhas e contagens da base."""
    print("=== Etapa 1: carregamento dos dados ===\n")

    # Dimensões da base
    linhas, colunas = df.shape
    print(f"Linhas: {linhas} | Colunas: {colunas}\n")

    # Tipos e quantidade de valores preenchidos por coluna
    print("Estrutura do DataFrame:")
    df.info()
    print()

    # Amostra inicial
    print("Primeiras linhas:")
    print(df.head(10).to_string(index=False))
    print()

    # Contagens de pedidos e itens
    total_pedidos = df["id_pedido"].nunique()
    print(f"Pedidos distintos: {total_pedidos}")
    print(f"Itens distintos: {df['item'].nunique()}")
    print(f"Média de linhas por pedido: {linhas / total_pedidos:.2f}")
