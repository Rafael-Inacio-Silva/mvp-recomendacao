"""Conexão com o LLM da OpenAI, configurada pelo .env."""

import os
import threading

import openai
from dotenv import load_dotenv

MODELO_PADRAO = "gpt-6-luna"
ESFORCO_PADRAO = "low"
TEMPO_LIMITE_SEGUNDOS = 30.0

# Tokens gastos desde o último zerar_uso(); a avaliação do assistente usa para calcular o custo
uso = {"chamadas": 0, "entrada": 0, "saida": 0}
_trava_uso = threading.Lock()


def zerar_uso():
    with _trava_uso:
        for chave in uso:
            uso[chave] = 0


def registrar_uso(resposta):
    """Soma os tokens de entrada e de saída (inclui o raciocínio) de uma chamada."""
    tokens = getattr(resposta, "usage", None)
    if tokens is None:
        return
    with _trava_uso:
        uso["chamadas"] += 1
        uso["entrada"] += tokens.input_tokens
        uso["saida"] += tokens.output_tokens


def criar_cliente(tempo_limite=TEMPO_LIMITE_SEGUNDOS):
    """Retorna o cliente da OpenAI, ou None quando não há chave no .env."""
    load_dotenv()
    chave = os.getenv("OPENAI_API_KEY", "").strip()
    if not chave:
        return None
    return openai.OpenAI(api_key=chave, timeout=tempo_limite)


def criar_resposta(cliente, instrucoes, entrada, ferramentas=None, permitir_ferramentas=True, esforco=None, formato=None):
    """Faz uma chamada à Responses API; ferramentas, esforço e formato da saída são opcionais."""
    parametros = {
        "model": os.getenv("OPENAI_MODEL", "").strip() or MODELO_PADRAO,
        "instructions": instrucoes,
        "input": entrada,
        "reasoning": {"effort": esforco or os.getenv("OPENAI_REASONING_EFFORT", "").strip() or ESFORCO_PADRAO},
        # store=False: a OpenAI não guarda as conversas; o raciocínio volta criptografado na entrada
        "store": False,
        "include": ["reasoning.encrypted_content"],
    }
    if ferramentas:
        parametros["tools"] = ferramentas
        parametros["tool_choice"] = "auto" if permitir_ferramentas else "none"
    if formato:
        parametros["text"] = {"format": formato}
    resposta = cliente.responses.create(**parametros)
    registrar_uso(resposta)
    return resposta
