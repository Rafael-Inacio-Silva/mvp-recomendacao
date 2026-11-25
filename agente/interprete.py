"""Intérprete da busca de restaurantes: o LLM transforma o texto livre em culinária e termos de busca."""

import json

from agente.llm import criar_resposta
from agente.prompts import ler_arquivo, preencher

MAXIMO_TERMOS = 5


def formato_intencao(culinarias):
    """Saída em JSON; a culinária só pode ser uma das culinárias da cidade, ou null."""
    return {
        "type": "json_schema",
        "name": "intencao",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "culinaria": {"type": ["string", "null"], "enum": [*culinarias, None]},
                "termos": {"type": "array", "items": {"type": "string"}, "maxItems": MAXIMO_TERMOS},
            },
            "required": ["culinaria", "termos"],
            "additionalProperties": False,
        },
    }


def interpretar(cliente, texto, culinarias):
    """Intenção da frase, como devolvida pelo LLM; a conferência com o catálogo é feita depois, no modelo."""
    instrucoes = preencher(ler_arquivo("interprete/prompt.md"), {"culinarias": "\n".join(f"- {c}" for c in culinarias)})
    resposta = criar_resposta(cliente, instrucoes, [{"role": "user", "content": texto}], formato=formato_intencao(culinarias))
    return json.loads(resposta.output_text)
