"""Etapa 5 do pipeline: exploração da base limpa."""

QUANTIDADE_EXIBIDA = 10


def calcular_frequencia_itens(df):
    """Retorna o percentual de pedidos em que cada item aparece."""
    total_pedidos = df["id_pedido"].nunique()
    pedidos_por_item = df.groupby("item")["id_pedido"].nunique()
    return (pedidos_por_item / total_pedidos * 100).sort_values(ascending=False)


def calcular_pares(df):
    """Retorna os pares de itens pedidos juntos e em quantos pedidos aparecem."""
    # Combinação dos itens de um mesmo pedido, dois a dois
    pares = df.merge(df, on="id_pedido", suffixes=("_a", "_b"))

    # Cada par uma única vez: sem repetir A + A nem inverter para B + A
    pares = pares[pares["item_a"] < pares["item_b"]]

    contagem = pares.groupby(["item_a", "item_b"]).size()
    return contagem.sort_values(ascending=False)


def mostrar_exploracao(df):
    """Exibe o resumo da base, os itens e os pares mais frequentes."""
    print("\n=== Etapa 5: exploração ===\n")

    total_pedidos = df["id_pedido"].nunique()
    tamanhos = df.groupby("id_pedido").size()

    # Resumo da base limpa
    print(f"Pedidos: {total_pedidos} | Itens distintos: {df['item'].nunique()}")
    print(f"Média de itens por pedido: {tamanhos.mean():.2f}")

    # Itens mais frequentes
    print("\nItens mais frequentes (% dos pedidos):")
    frequencia = calcular_frequencia_itens(df)
    for item, percentual in frequencia.head(QUANTIDADE_EXIBIDA).items():
        print(f"{item:<45} {percentual:5.1f}%")

    # Pares mais frequentes
    print("\nPares mais frequentes:")
    pares = calcular_pares(df)
    for (item_a, item_b), quantidade in pares.head(QUANTIDADE_EXIBIDA).items():
        percentual = quantidade / total_pedidos * 100
        print(f"{item_a + ' + ' + item_b:<60} {quantidade:4} pedidos ({percentual:.1f}%)")
