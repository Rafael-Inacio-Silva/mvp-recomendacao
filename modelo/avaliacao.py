"""Avaliação offline do recomendador com pedidos separados para teste."""

import pandas as pd

from modelo.recomendador import calcular_populares, preparar_regras, recomendar, sugerir_populares
from modelo.regras import calcular_regras, formatar_regras, montar_cestas

PROPORCAO_TESTE = 0.2
DOBRAS = 5
SEMENTE = 42
REFERENCIA = "Referência: só mais pedidos"

# Versões comparadas: limites das regras e forma de montar as sugestões
VERSOES = {
    "Versão 1: lift, só regras": {
        "confianca_minima": 0.2, "filtrar_lift": True, "criterio": "lift", "completar": False,
    },
    "Versão 2: lift + mais pedidos": {
        "confianca_minima": 0.2, "filtrar_lift": True, "criterio": "lift", "completar": True,
    },
    "Versão 3: confiança + mais pedidos": {
        "confianca_minima": 0.1, "filtrar_lift": False, "criterio": "confianca", "completar": True,
    },
}


def dividir_pedidos(pedidos, proporcao_teste=PROPORCAO_TESTE, semente=SEMENTE):
    """Separa os pedidos em treino e teste, sem dividir um mesmo pedido entre os dois."""
    ids = pd.Series(pedidos["id_pedido"].unique())
    ids_teste = ids.sample(frac=proporcao_teste, random_state=semente)
    em_teste = pedidos["id_pedido"].isin(ids_teste)
    return pedidos[~em_teste], pedidos[em_teste]


def dividir_em_dobras(pedidos, dobras=DOBRAS, semente=SEMENTE):
    """Separa os pedidos em dobras; cada pedido fica no teste de exatamente uma dobra."""
    ids = pd.Series(pedidos["id_pedido"].unique()).sample(frac=1, random_state=semente).tolist()
    divisoes = []
    for k in range(dobras):
        em_teste = pedidos["id_pedido"].isin(ids[k::dobras])
        divisoes.append((pedidos[~em_teste], pedidos[em_teste]))
    return divisoes


def treinar(treino, confianca_minima, filtrar_lift):
    """Calcula as regras e os itens mais pedidos apenas com os pedidos de treino."""
    cestas = montar_cestas(treino)
    regras = calcular_regras(cestas, confianca_minima=confianca_minima, filtrar_lift=filtrar_lift)
    regras = preparar_regras(formatar_regras(regras))
    return regras, calcular_populares(treino)


def montar_casos(teste):
    """Gera um caso por item de cada pedido de teste: o item escondido e o restante como carrinho."""
    casos = []

    for _, itens in teste.groupby("id_pedido")["item"]:
        itens = list(itens)

        # Pedido com um item só não forma carrinho
        if len(itens) < 2:
            continue

        for escondido in itens:
            carrinho = [item for item in itens if item != escondido]
            casos.append((carrinho, escondido))

    return casos


def calcular_percentual(parte, total):
    """Retorna o percentual com uma casa decimal, ou 0 quando não há total."""
    return round(parte / total * 100, 1) if total else 0


def contar_acertos(casos, regras, populares, criterio, completar):
    """Conta os casos com o item escondido entre as sugestões e os casos com regra aplicável."""
    acertos = 0
    com_regra = 0

    for carrinho, escondido in casos:
        sugestoes = recomendar(carrinho, regras, populares, criterio=criterio, completar=completar)
        acertos += escondido in [sugestao["item"] for sugestao in sugestoes]
        com_regra += any(sugestao["origem"] == "regra" for sugestao in sugestoes)

    return acertos, com_regra


def contar_acertos_referencia(casos, populares):
    """Conta os acertos da referência: sempre os 3 mais pedidos fora do carrinho."""
    acertos = 0
    for carrinho, escondido in casos:
        sugestoes = sugerir_populares(set(carrinho), populares)
        acertos += escondido in [sugestao["item"] for sugestao in sugestoes]
    return acertos


def avaliar_divisoes(divisoes):
    """Calcula o acerto no top 3 e a cobertura de cada versão, somando os casos de todas as divisões."""
    acertos = {nome: 0 for nome in list(VERSOES) + [REFERENCIA]}
    cobertos = {nome: 0 for nome in VERSOES}
    total_casos = 0

    for treino, teste in divisoes:
        casos = montar_casos(teste)
        total_casos += len(casos)

        # Versões com os mesmos limites usam as mesmas regras
        treinados = {}
        for nome, versao in VERSOES.items():
            limites = (versao["confianca_minima"], versao["filtrar_lift"])
            if limites not in treinados:
                treinados[limites] = treinar(treino, *limites)
            regras, populares = treinados[limites]

            certos, com_regra = contar_acertos(casos, regras, populares, versao["criterio"], versao["completar"])
            acertos[nome] += certos
            cobertos[nome] += com_regra

        acertos[REFERENCIA] += contar_acertos_referencia(casos, populares)

    resultado = {}
    for nome in acertos:
        resultado[nome] = {
            "acerto_%": calcular_percentual(acertos[nome], total_casos),
            "cobertura_%": calcular_percentual(cobertos[nome], total_casos) if nome in cobertos else None,
        }
    return resultado, total_casos
