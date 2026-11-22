"""Etapa 3 do pipeline: verificação e tratamento de itens repetidos no mesmo pedido."""

COLUNAS_CHAVE = ["id_pedido", "item"]


def mostrar_duplicados(df):
    """Exibe a quantidade de itens repetidos dentro dos pedidos."""
    print("\n=== Etapa 3: duplicados ===\n")

    # Repetições além da primeira ocorrência de cada item no pedido
    duplicadas = df.duplicated(subset=COLUNAS_CHAVE).sum()
    print(f"Linhas repetidas (mesmo pedido e item): {duplicadas}")

    # Pedidos que têm pelo menos um item repetido
    linhas_repetidas = df[df.duplicated(subset=COLUNAS_CHAVE, keep=False)]
    print(f"Pedidos com item repetido: {linhas_repetidas['id_pedido'].nunique()}")

    # Itens que mais se repetem dentro de um mesmo pedido
    print("\nItens mais repetidos no mesmo pedido:")
    repetidos = df[df.duplicated(subset=COLUNAS_CHAVE)]["item"].value_counts()
    print(repetidos.head(5).to_string())


def tratar_duplicados(df):
    """Mantém uma única linha por item em cada pedido."""
    linhas_antes = len(df)

    df = df.drop_duplicates(subset=COLUNAS_CHAVE)

    print(f"\nLinhas removidas: {linhas_antes - len(df)}")
    print(f"Linhas restantes: {len(df)}")

    return df
