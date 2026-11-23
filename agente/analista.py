"""Subagentes analistas: cada um recebe os dados da sua área e analisa a pergunta com o LLM."""

from dataclasses import dataclass
from typing import Callable

from agente.llm import criar_resposta
from agente.prompts import instrucoes_analista

RESPOSTA_VAZIA = "Não encontrei essa informação nos dados."


@dataclass(frozen=True)
class Analista:
    """Subagente com prompt próprio (agente/prompts/<nome>/prompt.md) e uma fonte de dados."""

    nome: str
    descricao: str
    fonte: Callable

    def responder(self, cliente, dados, pergunta, agora=None):
        """Responde à pergunta do coordenador lendo os dados da sua área; não guarda histórico."""
        instrucoes = instrucoes_analista(self.nome, dados, self.fonte(dados.loja), agora)
        resposta = criar_resposta(cliente, instrucoes, [{"role": "user", "content": pergunta}])
        return resposta.output_text.strip() or RESPOSTA_VAZIA
