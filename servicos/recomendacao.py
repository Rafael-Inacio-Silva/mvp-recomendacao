"""Serviço de recomendação: lojas, cardápio e sugestões para o carrinho."""

from dados_loja import LojaIndisponivel, carregar_dados_loja
from lojas import ATENDENTES, LOJAS
from modelo.explicacao import explicar
from modelo.recomendador import recomendar
from modelo.validacao import validar_carrinho
from servicos.erros import EntradaInvalida, Indisponivel, NaoEncontrado, com_mensagens, erro


def carregar_loja(loja):
    """Dados da loja; erro quando a loja não existe ou ainda não tem os arquivos gerados."""
    if loja not in LOJAS:
        raise NaoEncontrado([erro("loja", "not_found", "Loja não encontrada.")])
    try:
        return carregar_dados_loja(loja)
    except LojaIndisponivel:
        raise Indisponivel([erro("loja", "unavailable", "Os dados da loja ainda não foram gerados.")])


def listar_lojas():
    return [{"loja": loja, "nome": nome, "atendente": ATENDENTES[loja]} for loja, nome in LOJAS.items()]


def ver_cardapio(loja):
    """Itens da loja, do mais pedido para o menos pedido."""
    dados = carregar_loja(loja)

    ranking = {item: posicao for posicao, item in enumerate(dados.populares)}
    produtos = dados.produtos.assign(posicao=dados.produtos["item"].map(ranking)).sort_values("posicao")
    itens = produtos[["item", "categoria", "descricao"]].to_dict("records")
    return {"loja": loja, "nome": dados.nome, "itens": itens}


def sugerir(loja, carrinho):
    """Valida o carrinho (RN-09) e devolve as 3 sugestões com a frase de cada uma."""
    dados = carregar_loja(loja)

    verificacao = validar_carrinho(carrinho, dados.populares)
    if not verificacao["ok"]:
        raise EntradaInvalida(com_mensagens(verificacao["errors"]))

    carrinho = verificacao["value"]
    sugestoes = []
    for sugestao in recomendar(carrinho, dados.regras, dados.populares):
        sugestoes.append({
            "item": sugestao["item"],
            "frase": explicar(sugestao, dados.cardapio),
            "origem": sugestao["origem"],
        })
    return {"ok": True, "carrinho": carrinho, "sugestoes": sugestoes}
