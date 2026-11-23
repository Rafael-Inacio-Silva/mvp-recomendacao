"""Executa as etapas do pipeline de dados em sequência, para cada loja."""

from lojas import LOJAS, caminho, lojas_disponiveis
from pipeline.etapa1_carregamento import carregar_pedidos, mostrar_visao_geral
from pipeline.etapa2_nulos_vazios import mostrar_nulos_vazios, tratar_nulos_vazios
from pipeline.etapa3_duplicados import mostrar_duplicados, tratar_duplicados
from pipeline.etapa4_outliers import mostrar_outliers, tratar_outliers
from pipeline.etapa5_exploracao import mostrar_exploracao
from pipeline.etapa6_cardapio import atualizar_cardapio, mostrar_cardapio


def executar_pipeline(loja):
    print(f"\n{'#' * 60}\n# Loja: {LOJAS[loja]}\n{'#' * 60}\n")

    # Etapa 1: carregamento dos dados
    pedidos = carregar_pedidos(caminho(loja, "pedidos.csv"))
    mostrar_visao_geral(pedidos)

    # Etapa 2: nulos e vazios
    mostrar_nulos_vazios(pedidos)
    pedidos = tratar_nulos_vazios(pedidos)

    # Etapa 3: duplicados
    mostrar_duplicados(pedidos)
    pedidos = tratar_duplicados(pedidos)

    # Etapa 4: outliers
    mostrar_outliers(pedidos)
    pedidos = tratar_outliers(pedidos)

    # Etapa 5: exploração
    mostrar_exploracao(pedidos)

    # Base limpa usada pelo modelo
    destino = caminho(loja, "pedidos_limpos.csv")
    pedidos.to_csv(destino, index=False)
    print(f"\nBase limpa salva em {destino}")

    # Etapa 6: cardápio com a forma de cada item na frase (LLM só para itens novos)
    cardapio = atualizar_cardapio(pedidos, caminho(loja, "cardapio.csv"))
    mostrar_cardapio(cardapio)

    return pedidos


if __name__ == "__main__":
    for loja in lojas_disponiveis():
        executar_pipeline(loja)
