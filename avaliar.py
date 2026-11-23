"""Avalia o recomendador com pedidos separados para teste."""

from modelo.avaliacao import PROPORCAO_TESTE, avaliar, dividir_pedidos, montar_casos, treinar
from modelo.regras import carregar_pedidos_limpos


def executar():
    pedidos = carregar_pedidos_limpos()

    # Divisão em treino e teste
    treino, teste = dividir_pedidos(pedidos)
    print(f"Pedidos de treino: {treino['id_pedido'].nunique()}")
    print(f"Pedidos de teste: {teste['id_pedido'].nunique()} ({PROPORCAO_TESTE:.0%})\n")

    # Regras e mais pedidos calculados só com o treino
    regras, populares = treinar(treino)
    print(f"Regras geradas no treino: {len(regras)}")

    # Um caso por item escondido nos pedidos de teste
    casos = montar_casos(teste)
    print(f"Casos de teste: {len(casos)}\n")

    # Versão 1: mais pedidos só quando nenhuma regra se aplica
    versao1 = avaliar(casos, regras, populares, completar=False)

    # Versão 2: mais pedidos completando as vagas restantes
    versao2 = avaliar(casos, regras, populares, completar=True)

    print("Acerto no top 3 (Hit Rate@3):")
    print(f"  Versão 1 (só regras):              {versao1['hit_rate_modelo_%']}%")
    print(f"  Versão 2 (regras + mais pedidos):  {versao2['hit_rate_modelo_%']}%")
    print(f"  Referência (só mais pedidos):      {versao2['hit_rate_referencia_%']}%\n")

    print(f"Casos com regra aplicável (cobertura): {versao2['cobertura_%']}%")
    print("Acerto no top 3 só nesses casos:")
    print(f"  Versão 1:   {versao1['hit_rate_modelo_com_regra_%']}%")
    print(f"  Versão 2:   {versao2['hit_rate_modelo_com_regra_%']}%")
    print(f"  Referência: {versao2['hit_rate_referencia_com_regra_%']}%\n")

    print(f"Lift médio das sugestões por regra: {versao2['lift_medio']}")


if __name__ == "__main__":
    executar()
