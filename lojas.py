"""Lojas atendidas pelo MVP e caminhos dos arquivos de cada uma."""

import os

LOJAS = {
    "mexicano": "Sabor na Mesa Cozinha Mexicana",
    "indiano": "Casa Masala Cozinha Indiana",
}


def caminho(loja, arquivo):
    """Retorna o caminho de um arquivo de dados da loja."""
    return f"dados/{loja}/{arquivo}"


def lojas_disponiveis():
    """Retorna as lojas que têm o arquivo de pedidos; avisa quando falta algum."""
    disponiveis = []
    for loja in LOJAS:
        if os.path.exists(caminho(loja, "pedidos.csv")):
            disponiveis.append(loja)
        else:
            print(f"Aviso: {caminho(loja, 'pedidos.csv')} não encontrado; a loja {LOJAS[loja]} foi ignorada (ver README).")
    return disponiveis
