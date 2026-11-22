"""Etapa 4 do pipeline: verificação e tratamento de outliers."""

MINIMO_PEDIDOS_ITEM = 10


def calcular_tamanho_pedidos(df):
    """Retorna a quantidade de itens de cada pedido."""
    return df.groupby("id_pedido").size()


def calcular_limite_superior(tamanhos):
    """Calcula o limite superior pelo método do IQR."""
    q1 = tamanhos.quantile(0.25)
    q3 = tamanhos.quantile(0.75)
    iqr = q3 - q1
    return q3 + 1.5 * iqr


def mostrar_outliers(df):
    """Exibe os pedidos com quantidade atípica de itens e os itens raros."""
    print("\n=== Etapa 4: outliers ===\n")

    tamanhos = calcular_tamanho_pedidos(df)
    limite = calcular_limite_superior(tamanhos)

    # Distribuição da quantidade de itens por pedido
    print("Pedidos por quantidade de itens:")
    print(tamanhos.value_counts().sort_index().to_string())

    # Pedidos acima do limite superior
    outliers = tamanhos[tamanhos > limite]
    print(f"\nLimite superior (IQR): {limite} itens")
    print(f"Pedidos acima do limite: {len(outliers)} ({len(outliers) / len(tamanhos):.1%})")

    # Itens presentes em poucos pedidos
    pedidos_por_item = df.groupby("item")["id_pedido"].nunique().sort_values()
    raros = pedidos_por_item[pedidos_por_item < MINIMO_PEDIDOS_ITEM]
    print(f"\nItens em menos de {MINIMO_PEDIDOS_ITEM} pedidos: {len(raros)}")
    print(raros.to_string())


def tratar_outliers(df):
    """Remove os pedidos com quantidade de itens acima do limite superior."""
    tamanhos = calcular_tamanho_pedidos(df)
    limite = calcular_limite_superior(tamanhos)
    pedidos_validos = tamanhos[tamanhos <= limite].index

    linhas_antes = len(df)
    pedidos_antes = df["id_pedido"].nunique()

    # Pedidos grandes reúnem escolhas de várias pessoas e são descartados;
    # os itens raros permanecem e são filtrados depois pelo suporte mínimo
    df = df[df["id_pedido"].isin(pedidos_validos)]

    print(f"\nPedidos removidos: {pedidos_antes - df['id_pedido'].nunique()}")
    print(f"Linhas removidas: {linhas_antes - len(df)}")
    print(f"Pedidos restantes: {df['id_pedido'].nunique()} | Linhas restantes: {len(df)}")

    return df
