"""Avalia as versões do recomendador com pedidos separados para teste, para cada loja."""

import pandas as pd

from lojas import LOJAS, caminho, lojas_disponiveis
from modelo.avaliacao import DOBRAS, PROPORCAO_TESTE, avaliar_divisoes, dividir_em_dobras, dividir_pedidos
from modelo.regras import carregar_pedidos_limpos


def executar(loja):
    print(f"\n{'#' * 60}\n# Loja: {LOJAS[loja]}\n{'#' * 60}\n")

    pedidos = carregar_pedidos_limpos(caminho(loja, "pedidos_limpos.csv"))
    print(f"Pedidos: {pedidos['id_pedido'].nunique()}")

    # Divisão única: 80% treino e 20% teste
    unica, casos_unica = avaliar_divisoes([dividir_pedidos(pedidos)])

    # Validação cruzada: todos os pedidos passam pelo teste uma vez
    cruzada, casos_cruzada = avaliar_divisoes(dividir_em_dobras(pedidos))

    print(f"Casos de teste: {casos_unica} na divisão {1 - PROPORCAO_TESTE:.0%}/{PROPORCAO_TESTE:.0%}"
          f" e {casos_cruzada} na validação cruzada ({DOBRAS} dobras)\n")

    print("Acerto no top 3 (Hit Rate@3) e cobertura das regras:")
    print(f"  {'Versão':38} {'divisão única':>14} {'valid. cruzada':>15} {'cobertura':>10}")
    for nome in cruzada:
        cobertura = cruzada[nome]["cobertura_%"]
        texto_cobertura = f"{cobertura}%" if cobertura is not None else "-"
        print(f"  {nome:38} {unica[nome]['acerto_%']:>13}% {cruzada[nome]['acerto_%']:>14}% {texto_cobertura:>10}")

    # Resultado salvo em CSV, como registro da avaliação
    resultado = pd.DataFrame([
        {
            "versao": nome,
            "acerto_divisao_unica_%": unica[nome]["acerto_%"],
            "acerto_validacao_cruzada_%": cruzada[nome]["acerto_%"],
            "cobertura_%": cruzada[nome]["cobertura_%"],
            "casos_divisao_unica": casos_unica,
            "casos_validacao_cruzada": casos_cruzada,
        }
        for nome in cruzada
    ])
    destino = caminho(loja, "avaliacao.csv")
    resultado.to_csv(destino, index=False)
    print(f"\nResultado salvo em {destino}")


if __name__ == "__main__":
    for loja in lojas_disponiveis():
        executar(loja)
