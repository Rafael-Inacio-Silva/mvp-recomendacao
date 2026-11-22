"""Cálculo das regras de associação a partir dos pedidos limpos."""

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

CAMINHO_PEDIDOS_LIMPOS = "dados/pedidos_limpos.csv"
CAMINHO_REGRAS = "dados/regras.csv"
COLUNAS_REGRAS = ["antecedents", "consequents", "support", "confidence", "lift"]

# Limites escolhidos na comparação de combinações
SUPORTE_MINIMO = 0.01
CONFIANCA_MINIMA = 0.2


def carregar_pedidos_limpos(caminho=CAMINHO_PEDIDOS_LIMPOS):
    """Lê a base limpa gerada pelo pipeline de dados."""
    return pd.read_csv(caminho)


def montar_cestas(df):
    """Retorna a tabela pedido x item, com True quando o item está no pedido."""
    return pd.crosstab(df["id_pedido"], df["item"]).astype(bool)


def calcular_regras(cestas, suporte_minimo=SUPORTE_MINIMO, confianca_minima=CONFIANCA_MINIMA):
    """Calcula as regras com suporte e confiança acima dos limites e lift maior que 1."""
    frequentes = apriori(cestas, min_support=suporte_minimo, use_colnames=True)

    # Sem conjuntos de dois itens ou mais, não há regras
    if frequentes["itemsets"].apply(len).max() < 2:
        return pd.DataFrame(columns=COLUNAS_REGRAS)

    regras = association_rules(
        frequentes,
        num_itemsets=len(cestas),
        metric="confidence",
        min_threshold=confianca_minima,
    )

    # Apenas associações positivas
    regras = regras[regras["lift"] > 1]

    return regras[COLUNAS_REGRAS].reset_index(drop=True)


def calcular_cobertura(cestas, regras):
    """Retorna o percentual de pedidos em que pelo menos uma regra se aplica."""
    cobertos = pd.Series(False, index=cestas.index)

    # Um pedido é coberto quando contém todos os itens do antecedente da regra
    for antecedente in regras["antecedents"]:
        cobertos = cobertos | cestas[list(antecedente)].all(axis=1)

    return cobertos.mean() * 100


def testar_limites(cestas, suportes, confiancas):
    """Calcula as regras para cada combinação de limites e resume os resultados."""
    resultados = []

    for suporte in suportes:
        for confianca in confiancas:
            regras = calcular_regras(cestas, suporte, confianca)
            resultados.append({
                "suporte_minimo": suporte,
                "confianca_minima": confianca,
                "regras": len(regras),
                "cobertura_%": round(calcular_cobertura(cestas, regras), 1),
                "lift_medio": round(regras["lift"].mean(), 2) if len(regras) else 0,
            })

    return pd.DataFrame(resultados)


def formatar_regras(regras):
    """Converte as regras para colunas em português, com os itens em texto."""
    return pd.DataFrame({
        "antecedente": regras["antecedents"].apply(lambda itens: " + ".join(sorted(itens))),
        "consequente": regras["consequents"].apply(lambda itens: " + ".join(sorted(itens))),
        "suporte": regras["support"].round(4),
        "confianca": regras["confidence"].round(4),
        "lift": regras["lift"].round(4),
    }).sort_values(["lift", "confianca"], ascending=False).reset_index(drop=True)


def salvar_regras(regras, caminho=CAMINHO_REGRAS):
    """Salva as regras formatadas em CSV."""
    regras.to_csv(caminho, index=False)
