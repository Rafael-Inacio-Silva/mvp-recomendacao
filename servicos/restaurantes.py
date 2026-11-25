"""Serviço de recomendação de restaurantes: cidades, culinárias, interpretação do texto livre e o top 10."""

import json
import threading
from collections import OrderedDict

import openai

from agente.interprete import interpretar
from agente.llm import criar_cliente
from cidades import CIDADES
from dados_restaurantes import CatalogoIndisponivel, indice_da_cidade
from modelo.restaurantes import pesos_efetivos, recomendar_restaurantes, validar_intencao
from modelo.validacao_restaurantes import validar_busca
from servicos.erros import EntradaInvalida, Indisponivel, NaoEncontrado, com_mensagens, erro

# Interpretações já feitas, por cidade e texto: mover os pesos reaproveita a mesma, sem chamar o LLM de novo
MAXIMO_INTERPRETACOES = 500
_interpretacoes = OrderedDict()
_trava = threading.Lock()
_cliente = {"llm": None}


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


def interpretar_texto(cidade, indice, texto):
    """Intenção do texto livre conferida no catálogo, ou None quando o LLM não está disponível (RN-R09)."""
    chave = (cidade, " ".join(texto.lower().split()))
    with _trava:
        if chave in _interpretacoes:
            _interpretacoes.move_to_end(chave)
            return _interpretacoes[chave]
        if _cliente["llm"] is None:
            _cliente["llm"] = criar_cliente()
        cliente = _cliente["llm"]
    if cliente is None:
        return None

    culinarias = sorted(indice["restaurantes"]["culinaria"].unique())
    try:
        intencao = validar_intencao(indice, interpretar(cliente, texto, culinarias), culinarias)
    except (openai.OpenAIError, json.JSONDecodeError, ValueError):
        # Falha não entra no cache: a próxima busca tenta de novo
        return None

    with _trava:
        _interpretacoes[chave] = intencao
        if len(_interpretacoes) > MAXIMO_INTERPRETACOES:
            _interpretacoes.popitem(last=False)
    return intencao


def recomendar(cidade, culinaria, preferencia, pesos):
    """Valida a busca (RN-R07), interpreta o texto livre (RN-R09) e devolve o top 10 com a explicação de cada um."""
    indice = carregar_cidade(cidade)

    verificacao = validar_busca(culinaria, preferencia, pesos, indice["restaurantes"]["culinaria"].unique())
    if not verificacao["ok"]:
        raise EntradaInvalida(com_mensagens(verificacao["errors"]))
    busca = verificacao["value"]

    culinaria_usada = busca["culinaria"]
    culinaria_do_texto = False
    termos = []
    interpretacao = None
    avisos = []

    # Texto vazio dispensa o LLM
    if busca["preferencia"]:
        intencao = interpretar_texto(cidade, indice, busca["preferencia"])
        if intencao is None:
            interpretacao = {"disponivel": False}
            avisos.append("Não consegui interpretar o texto agora. A busca segue pela cidade, pela culinária e pelos pesos.")
        else:
            termos = intencao["termos"]
            pedida = intencao["culinaria"]
            conflito = bool(pedida and busca["culinaria"] and pedida != busca["culinaria"])
            if conflito:
                avisos.append(f"O texto pede culinária {pedida}, mas o seletor está em {busca['culinaria']}. Mantive {busca['culinaria']}.")
            elif pedida and not busca["culinaria"]:
                # Culinária pedida no texto restringe os candidatos antes da pontuação
                culinaria_usada, culinaria_do_texto = pedida, True
            if intencao["ignorados"]:
                avisos.append("Não encontrei nesta cidade: " + ", ".join(f"“{termo}”" for termo in intencao["ignorados"]) + ".")
            if not pedida and not termos:
                avisos.append("Não identifiquei no texto uma culinária ou característica do catálogo. A ordem segue avaliação, frete e entrega.")
            interpretacao = {"disponivel": True, "culinaria": pedida, "termos": termos,
                             "ignorados": intencao["ignorados"], "conflito": conflito}

    restaurantes = recomendar_restaurantes(indice, culinaria_usada, termos, busca["pesos"], culinaria_do_texto)
    return {
        "ok": True,
        "cidade": cidade,
        "culinaria": culinaria_usada,
        "preferencia": busca["preferencia"],
        "interpretacao": interpretacao,
        "avisos": avisos,
        "pesos": {criterio: round(peso, 4) for criterio, peso in pesos_efetivos(busca["pesos"], " ".join(termos)).items()},
        "restaurantes": restaurantes,
    }
