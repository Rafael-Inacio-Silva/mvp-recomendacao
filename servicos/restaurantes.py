"""Serviço de recomendação de restaurantes: cidades, culinárias e o top 10 da busca."""

from cidades import CIDADES
from dados_restaurantes import CatalogoIndisponivel, indice_da_cidade
from modelo.restaurantes import pesos_efetivos, recomendar_restaurantes
from modelo.validacao_restaurantes import validar_busca
from servicos.erros import EntradaInvalida, Indisponivel, NaoEncontrado, com_mensagens, erro


def carregar_cidade(cidade):
    """Índice da cidade; erro quando ela não é atendida ou o catálogo ainda não foi gerado."""
    if cidade not in CIDADES:
        raise NaoEncontrado([erro("cidade", "not_found", "Cidade não atendida.")])
    try:
        return indice_da_cidade(cidade)
    except CatalogoIndisponivel:
        raise Indisponivel([erro("restaurantes", "unavailable", "O catálogo de restaurantes ainda não foi gerado.")])


def listar_cidades():
    return [{"cidade": cidade, "nome": dados["nome"], "ibge": dados["ibge"]} for cidade, dados in CIDADES.items()]


def listar_culinarias(cidade):
    """Culinárias da cidade, da mais comum para a menos comum."""
    restaurantes = carregar_cidade(cidade)["restaurantes"]
    contagem = restaurantes["culinaria"].value_counts()
    culinarias = [{"culinaria": nome, "restaurantes": int(total)} for nome, total in contagem.items()]
    return {"cidade": cidade, "nome": CIDADES[cidade]["nome"], "culinarias": culinarias}


def recomendar(cidade, culinaria, preferencia, pesos):
    """Valida a busca (RN-R07) e devolve os restaurantes recomendados com a explicação de cada um."""
    indice = carregar_cidade(cidade)

    verificacao = validar_busca(culinaria, preferencia, pesos, indice["restaurantes"]["culinaria"].unique())
    if not verificacao["ok"]:
        raise EntradaInvalida(com_mensagens(verificacao["errors"]))

    busca = verificacao["value"]
    restaurantes = recomendar_restaurantes(indice, busca["culinaria"], busca["preferencia"], busca["pesos"])
    return {
        "ok": True,
        "cidade": cidade,
        "culinaria": busca["culinaria"],
        "preferencia": busca["preferencia"],
        "pesos": {criterio: round(peso, 4) for criterio, peso in pesos_efetivos(busca["pesos"], busca["preferencia"]).items()},
        "restaurantes": restaurantes,
    }
