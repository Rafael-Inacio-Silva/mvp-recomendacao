"""Etapa 2 do pipeline: verificação e tratamento de nulos e vazios."""

import pandas as pd


def mostrar_nulos_vazios(df):
    """Exibe a quantidade de nulos, vazios e espaços extras na base."""
    print("\n=== Etapa 2: nulos e vazios ===\n")

    # Nulos por coluna
    print("Nulos por coluna:")
    print(df.isnull().sum().to_string())
    print()

    # Textos vazios e espaços no início ou no fim do nome do item
    itens = df["item"].dropna()
    vazios = (itens.str.strip() == "").sum()
    com_espacos = (itens != itens.str.strip()).sum()
    print(f"Itens vazios ou só com espaços: {vazios}")
    print(f"Itens com espaços no início ou no fim: {com_espacos}")


def tratar_nulos_vazios(df):
    """Remove espaços extras e descarta linhas com nulos ou itens vazios."""
    df = df.copy()
    linhas_antes = len(df)

    # Padronização dos nomes e conversão de vazios em nulos
    df["item"] = df["item"].str.strip()
    df["item"] = df["item"].replace("", pd.NA)

    # Remoção das linhas sem pedido ou sem item
    df = df.dropna(subset=["id_pedido", "item"])

    print(f"\nLinhas removidas: {linhas_antes - len(df)}")
    print(f"Linhas restantes: {len(df)}")

    return df
