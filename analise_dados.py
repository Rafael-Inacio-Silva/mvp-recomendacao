"""Executa as etapas do pipeline de dados em sequência."""

from pipeline.etapa1_carregamento import carregar_pedidos, mostrar_visao_geral
from pipeline.etapa2_nulos_vazios import mostrar_nulos_vazios, tratar_nulos_vazios
from pipeline.etapa3_duplicados import mostrar_duplicados, tratar_duplicados


def executar_pipeline():
    # Etapa 1: carregamento dos dados
    pedidos = carregar_pedidos()
    mostrar_visao_geral(pedidos)

    # Etapa 2: nulos e vazios
    mostrar_nulos_vazios(pedidos)
    pedidos = tratar_nulos_vazios(pedidos)

    # Etapa 3: duplicados
    mostrar_duplicados(pedidos)
    pedidos = tratar_duplicados(pedidos)

    return pedidos


if __name__ == "__main__":
    executar_pipeline()
