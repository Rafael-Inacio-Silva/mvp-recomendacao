"""Compara limites de suporte e confiança para as regras de associação."""

from modelo.regras import carregar_pedidos_limpos, montar_cestas, testar_limites

SUPORTES = [0.005, 0.01, 0.02, 0.03]
CONFIANCAS = [0.1, 0.2, 0.3]


def executar():
    pedidos = carregar_pedidos_limpos()
    cestas = montar_cestas(pedidos)
    print(f"Cestas: {cestas.shape[0]} pedidos x {cestas.shape[1]} itens\n")

    # Quantidade de regras, cobertura e lift médio para cada combinação
    resultado = testar_limites(cestas, SUPORTES, CONFIANCAS)
    print(resultado.to_string(index=False))


if __name__ == "__main__":
    executar()
