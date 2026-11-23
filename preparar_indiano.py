"""Prepara a base da Casa Masala: converte a exportação do caixa para o formato do projeto."""

import pandas as pd

ORIGEM = "dados/indiano/restaurant-1-orders.csv"
TRADUCAO = "dados/indiano/traducao_itens.csv"
DESTINO = "dados/indiano/pedidos.csv"


def preparar():
    exportacao = pd.read_csv(ORIGEM)
    traducao = pd.read_csv(TRADUCAO)
    print(f"Exportação: {len(exportacao)} linhas, {exportacao['Order Number'].nunique()} pedidos, "
          f"{exportacao['Item Name'].nunique()} itens")

    # Colunas usadas pelo projeto: número do pedido e nome do item
    pedidos = exportacao.rename(columns={"Order Number": "id_pedido", "Item Name": "item_original"})
    pedidos = pedidos[["id_pedido", "item_original"]]

    # Nome em português; grafias diferentes do mesmo item recebem a mesma tradução
    pedidos = pedidos.merge(traducao, on="item_original", how="left")
    print(f"Itens sem tradução: {pedidos['item'].isna().sum()} linhas")
    print(f"Itens em português: {pedidos['item'].nunique()}")

    pedidos[["id_pedido", "item"]].to_csv(DESTINO, index=False)
    print(f"Base salva em {DESTINO}")


if __name__ == "__main__":
    preparar()
