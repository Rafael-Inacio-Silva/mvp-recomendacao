"""Fonte de dados de cada analista: o conteúdo da loja em texto, enviado junto com o prompt."""

from functools import lru_cache

from dados_loja import carregar_dados_loja

MAXIMO_MAIS_PEDIDOS = 10


@lru_cache(maxsize=None)
def texto_cardapio(loja):
    """Todos os produtos, do mais pedido para o menos pedido: item, categoria e descrição."""
    dados = carregar_dados_loja(loja)
    ranking = {item: posicao for posicao, item in enumerate(dados.populares)}
    produtos = dados.produtos.assign(posicao=dados.produtos["item"].map(ranking)).sort_values("posicao")

    linhas = ["item | categoria | descrição"]
    for produto in produtos.itertuples():
        linhas.append(f"{produto.item} | {produto.categoria} | {produto.descricao}")
    return "\n".join(linhas)


@lru_cache(maxsize=None)
def texto_combinacoes(loja):
    """Regras de associação da loja, da maior para a menor confiança, e os itens mais pedidos."""
    dados = carregar_dados_loja(loja)

    linhas = ["Combinações calculadas a partir do histórico de pedidos (do maior para o menor número):"]
    for regra in dados.regras:
        antecedente = " + ".join(sorted(regra["antecedente"]))
        a_cada_100 = round(regra["confianca"] * 100)
        linhas.append(f"- pedidos com {antecedente} → {regra['consequente']}: {a_cada_100} de cada 100 pedidos")

    linhas.append("")
    linhas.append(f"Itens mais pedidos da casa, em ordem: {', '.join(dados.populares[:MAXIMO_MAIS_PEDIDOS])}")
    return "\n".join(linhas)


@lru_cache(maxsize=None)
def texto_loja(loja):
    """Documento com os dados da empresa."""
    return carregar_dados_loja(loja).informacoes
