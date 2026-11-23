"""Agentes especialistas: cada um responde a um tipo de pergunta usando a sua ferramenta."""

import json
from dataclasses import dataclass

from agente.ferramentas import Ferramenta, executar
from agente.llm import criar_resposta
from agente.prompts import instrucoes_especialista

MAXIMO_CHAMADAS = 3
RESPOSTA_VAZIA = "Não encontrei essa informação."


@dataclass(frozen=True)
class Especialista:
    """Agente com um prompt próprio (agente/prompts/<nome>/prompt.md) e uma ferramenta."""

    nome: str
    descricao: str
    ferramenta: Ferramenta

    def responder(self, cliente, dados, pergunta, agora=None):
        """Responde a uma pergunta do orquestrador; não guarda histórico entre perguntas."""
        instrucoes = instrucoes_especialista(self.nome, dados, agora)
        entrada = [{"role": "user", "content": pergunta}]
        chamadas = 0

        while True:
            # Depois do limite, o especialista responde com o que já tem
            resposta = criar_resposta(
                cliente, instrucoes, entrada, [self.ferramenta.esquema()], chamadas < MAXIMO_CHAMADAS
            )
            entrada.extend(resposta.output)

            pedidos = [parte for parte in resposta.output if parte.type == "function_call"]
            if not pedidos:
                return resposta.output_text.strip() or RESPOSTA_VAZIA

            for pedido in pedidos:
                chamadas += 1
                resultado = executar(self.ferramenta, pedido.arguments, dados)
                entrada.append({
                    "type": "function_call_output",
                    "call_id": pedido.call_id,
                    "output": json.dumps(resultado, ensure_ascii=False),
                })
