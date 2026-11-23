"""Compara limites de suporte e confiança e gera as regras de associação de cada loja."""

from lojas import LOJAS, caminho, lojas_disponiveis
from modelo.regras import (
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


def executar(loja):
    print(f"\n{'#' * 60}\n# Loja: {LOJAS[loja]}\n{'#' * 60}\n")

    pedidos = carregar_pedidos_limpos(caminho(loja, "pedidos_limpos.csv"))
    cestas = montar_cestas(pedidos)
    print(f"Cestas: {cestas.shape[0]} pedidos x {cestas.shape[1]} itens\n")

    # Quantidade de regras, cobertura, confiança média e lift médio para cada combinação
    print("Comparação de limites:")
    resultado = testar_limites(cestas, SUPORTES, CONFIANCAS)
    print(resultado.to_string(index=False))

    # Regras finais com os limites escolhidos
    regras = formatar_regras(calcular_regras(cestas))
    print(f"\nRegras geradas (suporte {SUPORTE_MINIMO:.0%}, confiança {CONFIANCA_MINIMA:.0%}): {len(regras)}")
    print(regras.head(10).to_string(index=False))

    destino = caminho(loja, "regras.csv")
    salvar_regras(regras, destino)
    print(f"\nRegras salvas em {destino}")


if __name__ == "__main__":
    for loja in lojas_disponiveis():
        executar(loja)
