"""Executa as etapas do pipeline de dados em sequência."""

from pipeline.etapa1_carregamento import carregar_pedidos, mostrar_visao_geral


def executar_pipeline():
    # Etapa 1: carregamento dos dados
    pedidos = carregar_pedidos()
    mostrar_visao_geral(pedidos)

    return pedidos


if __name__ == "__main__":
    executar_pipeline()
