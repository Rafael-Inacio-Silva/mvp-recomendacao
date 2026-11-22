"""Compara limites de suporte e confiança e gera as regras de associação."""

from modelo.regras import (
    CAMINHO_REGRAS,
    CONFIANCA_MINIMA,
    SUPORTE_MINIMO,
    calcular_regras,
    carregar_pedidos_limpos,
    formatar_regras,
    montar_cestas,
    salvar_regras,
    testar_limites,
)

SUPORTES = [0.005, 0.01, 0.02, 0.03]
CONFIANCAS = [0.1, 0.2, 0.3]


def executar():
    pedidos = carregar_pedidos_limpos()
    cestas = montar_cestas(pedidos)
    print(f"Cestas: {cestas.shape[0]} pedidos x {cestas.shape[1]} itens\n")

    # Quantidade de regras, cobertura e lift médio para cada combinação
    print("Comparação de limites:")
    resultado = testar_limites(cestas, SUPORTES, CONFIANCAS)
    print(resultado.to_string(index=False))

    # Regras finais com os limites escolhidos
    regras = formatar_regras(calcular_regras(cestas))
    print(f"\nRegras geradas (suporte {SUPORTE_MINIMO:.0%}, confiança {CONFIANCA_MINIMA:.0%}): {len(regras)}")
    print(regras.head(10).to_string(index=False))

    salvar_regras(regras)
    print(f"\nRegras salvas em {CAMINHO_REGRAS}")


if __name__ == "__main__":
    executar()
