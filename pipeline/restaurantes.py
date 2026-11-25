"""Pipeline do catálogo de restaurantes: carregamento, tratamento e recorte das cidades atendidas."""

import pandas as pd

from cidades import CIDADES

COLUNAS = ["ibge", "name", "category", "rating", "delivery_fee", "delivery_time", "price_range", "minimumOrderValue", "tags"]

# Faixa de preço do catálogo -> número de cifrões
FAIXAS_DE_PRECO = {"CHEAPEST": 1, "CHEAP": 2, "MODERATE": 3, "EXPENSIVE": 4, "MOST_EXPENSIVE": 5}

# Limites de valores plausíveis
TEMPO_MAXIMO_MINUTOS = 120
PEDIDO_MINIMO_MAXIMO = 500

# Trechos de etiqueta que descrevem o restaurante -> palavra usada no texto; as demais são códigos de campanha
ETIQUETAS_UTEIS = {
    "PRATOS_VEGETARIANOS": "vegetariano",
    "SAUDAVE": "saudável",
    "BOMEBARATO": "bom e barato",
    "BOM_BARATO": "bom e barato",
}


def carregar_restaurantes(caminho):
    """Lê só as colunas usadas e só as cidades atendidas."""
    ibges = {cidade["ibge"]: identificador for identificador, cidade in CIDADES.items()}
    df = pd.read_csv(caminho, usecols=COLUNAS, encoding="utf-8")
    df = df[df["ibge"].isin(ibges)].copy()
    df["cidade"] = df["ibge"].map(ibges)
    return df


def mostrar_visao_geral(df):
    print("=== Etapa 1: carregamento ===\n")
    print(f"Restaurantes nas cidades atendidas: {len(df)}")
    print(df["cidade"].value_counts().to_string())
    print(f"\nCulinárias: {df['category'].nunique()}")
    print(df["category"].value_counts().head(10).to_string())


def mostrar_valores_problematicos(df):
    print("\n=== Etapa 2: valores ausentes e inválidos ===\n")
    print("Nulos por coluna:")
    print(df.isna().sum().to_string())
    print(f"\nNota 0 (sem avaliação): {(df['rating'] == 0).sum()} ({(df['rating'] == 0).mean():.1%})")
    print(f"Tempo de entrega <= 0: {(df['delivery_time'] <= 0).sum()}")
    print(f"Tempo de entrega > {TEMPO_MAXIMO_MINUTOS} min: {(df['delivery_time'] > TEMPO_MAXIMO_MINUTOS).sum()}")
    print(f"Pedido mínimo > R$ {PEDIDO_MINIMO_MAXIMO}: {(df['minimumOrderValue'] > PEDIDO_MINIMO_MAXIMO).sum()}")
    print(f"Frete grátis: {(df['delivery_fee'] == 0).sum()}")


def tratar_valores(df):
    """Nota 0 vira ausente, tempo impossível sai da base e pedido mínimo absurdo vira ausente."""
    df = df.copy()

    # Nota 0 significa "sem avaliação" (RN-R03)
    df["rating"] = df["rating"].where(df["rating"] > 0)

    # Sem tempo de entrega confiável, o restaurante não pode ser comparado
    validos = (df["delivery_time"] > 0) & (df["delivery_time"] <= TEMPO_MAXIMO_MINUTOS)
    print(f"\nRestaurantes removidos por tempo de entrega inválido: {(~validos).sum()}")
    df = df[validos]

    # O pedido mínimo não entra na pontuação; o valor absurdo só deixa de ser exibido
    df["minimumOrderValue"] = df["minimumOrderValue"].where(df["minimumOrderValue"] <= PEDIDO_MINIMO_MAXIMO)
    return df


def mostrar_duplicados(df):
    print("\n=== Etapa 3: duplicados ===\n")
    print(f"Linhas idênticas: {df.duplicated(subset=COLUNAS).sum()}")
    print(f"Mesmo nome na mesma cidade (unidades de redes): {df.duplicated(['cidade', 'name']).sum()}")
    print("As unidades com o mesmo nome continuam na base e aparecem uma vez na recomendação (RN-R05).")


def tratar_duplicados(df):
    antes = len(df)
    df = df.drop_duplicates(subset=COLUNAS)
    print(f"Linhas idênticas removidas: {antes - len(df)}")
    return df


def extrair_etiquetas(tags):
    """Palavras úteis encontradas nas etiquetas, sem repetir; os códigos de campanha são descartados."""
    texto = str(tags).upper() if isinstance(tags, str) else ""
    encontradas = []
    for trecho, palavra in ETIQUETAS_UTEIS.items():
        if trecho in texto and palavra not in encontradas:
            encontradas.append(palavra)
    return "; ".join(encontradas)


def montar_catalogo(df):
    """Catálogo tratado, com nomes de colunas em português e sem dados que não serão usados."""
    catalogo = pd.DataFrame({
        "cidade": df["cidade"],
        "nome": df["name"].str.strip(),
        "culinaria": df["category"].str.strip(),
        "nota": df["rating"].round(2),
        "frete": df["delivery_fee"].round(2),
        "tempo": df["delivery_time"].astype(int),
        "faixa_preco": df["price_range"].map(FAIXAS_DE_PRECO),
        "pedido_minimo": df["minimumOrderValue"].round(2),
        "etiquetas": df["tags"].map(extrair_etiquetas),
    })
    return catalogo.sort_values(["cidade", "culinaria", "nome"]).reset_index(drop=True)


def mostrar_exploracao(catalogo):
    print("\n=== Etapa 4: exploração do catálogo tratado ===\n")
    resumo = catalogo.groupby("cidade").agg(
        restaurantes=("nome", "size"),
        sem_avaliacao=("nota", lambda notas: f"{notas.isna().mean():.1%}"),
        nota_mediana=("nota", "median"),
        frete_mediano=("frete", "median"),
        tempo_mediano=("tempo", "median"),
    )
    print(resumo.to_string())
    print("\nEtiquetas úteis:")
    print(catalogo["etiquetas"].str.split("; ").explode().replace("", pd.NA).dropna().value_counts().to_string())
