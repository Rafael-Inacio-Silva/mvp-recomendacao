"""Conexão com o LLM da OpenAI, configurada pelo .env."""

import os

import openai
from dotenv import load_dotenv

MODELO_PADRAO = "gpt-6-luna"
ESFORCO_PADRAO = "low"
TEMPO_LIMITE_SEGUNDOS = 30.0


def criar_cliente():
    """Retorna o cliente da OpenAI, ou None quando não há chave no .env."""
    load_dotenv()
    chave = os.getenv("OPENAI_API_KEY", "").strip()
    if not chave:
        return None
    return openai.OpenAI(api_key=chave, timeout=TEMPO_LIMITE_SEGUNDOS)


def criar_resposta(cliente, instrucoes, entrada, ferramentas=None, permitir_ferramentas=True):
    """Faz uma chamada à Responses API; as ferramentas são opcionais."""
    parametros = {
        "model": os.getenv("OPENAI_MODEL", "").strip() or MODELO_PADRAO,
        "instructions": instrucoes,
        "input": entrada,
        "reasoning": {"effort": os.getenv("OPENAI_REASONING_EFFORT", "").strip() or ESFORCO_PADRAO},
        # store=False: a OpenAI não guarda as conversas; o raciocínio volta criptografado na entrada
        "store": False,
        "include": ["reasoning.encrypted_content"],
    }
    if ferramentas:
        parametros["tools"] = ferramentas
        parametros["tool_choice"] = "auto" if permitir_ferramentas else "none"
    return cliente.responses.create(**parametros)
