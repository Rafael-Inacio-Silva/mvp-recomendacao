"""Avaliação do assistente: regras determinísticas sobre as respostas e juiz LLM opcional."""

import json
import unicodedata

from agente.fontes import texto_cardapio, texto_combinacoes, texto_loja
from agente.llm import criar_resposta
from agente.prompts import instrucoes_analista

ESFORCO_JUIZ = "high"

# Saída do juiz em JSON com campos fixos
FORMATO_JUIZ = {
    "type": "json_schema",
    "name": "avaliacao",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "respondeu_a_pergunta": {"type": "boolean"},
            "inventou_informacao": {"type": "boolean"},
            "tom": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
            "motivo": {"type": "string"},
        },
        "required": ["respondeu_a_pergunta", "inventou_informacao", "tom", "motivo"],
        "additionalProperties": False,
    },
}


def normalizar(texto):
    """Minúsculas, sem acentos e com espaços simples, para comparar textos."""
    sem_acento = unicodedata.normalize("NFD", texto or "")
    sem_acento = "".join(letra for letra in sem_acento if unicodedata.category(letra) != "Mn")
    return " ".join(sem_acento.lower().split())


def conferir(caso, respostas, atendente):
    """Lista de falhas da conversa; vazia quando o caso foi aprovado.

    `respostas` tem um dicionário por mensagem do caso, com texto, consultas, estagio e falhou.
    As regras de analistas, textos e etapa valem para a última resposta.
    """
    falhas = []

    if any(resposta["falhou"] for resposta in respostas):
        return ["a chamada ao LLM falhou"]

    # A saudação já aparece no site; a assistente não deve se apresentar em nenhuma resposta
    if not caso.get("apresentacao_permitida"):
        apresentacao = normalizar(f"sou a {atendente}")
        if any(apresentacao in normalizar(resposta["texto"]) for resposta in respostas):
            falhas.append("se apresentou de novo")

    ultima = respostas[-1]
    texto = normalizar(ultima["texto"])

    for analista in caso.get("analistas", []):
        if analista not in ultima["consultas"]:
            falhas.append(f"não consultou o analista {analista}")

    for alternativas in caso.get("contem", []):
        if not any(normalizar(alternativa) in texto for alternativa in alternativas):
            falhas.append("faltou: " + " / ".join(alternativas))

    for proibido in caso.get("nao_contem", []):
        if normalizar(proibido) in texto:
            falhas.append(f"não podia conter: {proibido}")

    minimo = caso.get("estagio_minimo")
    if minimo and ultima["estagio"] < minimo:
        falhas.append(f"ficou na etapa {ultima['estagio']}, esperada {minimo}")

    maximo = caso.get("estagio_maximo")
    if maximo and ultima["estagio"] > maximo:
        falhas.append(f"avançou para a etapa {ultima['estagio']}, máximo {maximo}")

    return falhas


def base_do_juiz(loja):
    """Os mesmos dados que os analistas leem, juntos, como gabarito do juiz."""
    return "\n\n".join([texto_loja(loja), texto_cardapio(loja), texto_combinacoes(loja)])


def julgar(cliente, dados, mensagens, respostas, agora=None):
    """Pede ao juiz a avaliação da última resposta; devolve o dicionário do formato FORMATO_JUIZ."""
    instrucoes = instrucoes_analista("juiz", dados, base_do_juiz(dados.loja), agora)
    conversa = []
    for mensagem, resposta in zip(mensagens, respostas):
        conversa.append(f"Cliente: {mensagem}")
        conversa.append(f"{dados.atendente}: {resposta['texto']}")
    entrada = [{"role": "user", "content": "\n".join(conversa)}]
    resposta = criar_resposta(cliente, instrucoes, entrada, esforco=ESFORCO_JUIZ, formato=FORMATO_JUIZ)
    return json.loads(resposta.output_text)
