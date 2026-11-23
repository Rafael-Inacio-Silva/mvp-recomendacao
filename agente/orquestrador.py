"""Orquestrador (coordenador): conversa com o cliente, guarda o histórico e decide quais analistas consultar."""

import json
import logging
from dataclasses import dataclass, field

import openai

from agente.analista import Analista
from agente.fontes import texto_cardapio, texto_combinacoes, texto_loja
from agente.llm import criar_resposta
from agente.prompts import instrucoes_orquestrador

logger = logging.getLogger(__name__)

MAXIMO_CONSULTAS = 4

RESPOSTA_ERRO_CONEXAO = "Desculpe, estou com dificuldade para me conectar agora. Pode tentar de novo em alguns instantes?"
RESPOSTA_OCUPADA = "Desculpe, estou recebendo muitas mensagens agora. Pode tentar de novo daqui a pouco?"
RESPOSTA_ERRO = "Desculpe, tive um problema técnico e não consegui responder. Pode tentar de novo?"
RESPOSTA_VAZIA = "Desculpe, não consegui montar a resposta. Pode repetir a pergunta de outro jeito?"

# Ferramenta do orquestrador -> subagente analista consultado
ANALISTAS = {
    "consultar_cardapio": Analista(
        nome="cardapio",
        descricao=(
            "Analista do cardápio: quais itens existem, ingredientes, como cada prato é feito, "
            "picância, categorias e opções vegetarianas."
        ),
        fonte=texto_cardapio,
    ),
    "consultar_combinacoes": Analista(
        nome="combinacoes",
        descricao=(
            "Analista de combinações: o que os clientes costumam pedir junto com um ou mais itens, "
            "para sugerir complementos ao pedido."
        ),
        fonte=texto_combinacoes,
    ),
    "consultar_loja": Analista(
        nome="loja",
        descricao=(
            "Analista da loja: endereço, horário, se está aberta agora, delivery, taxa, pedido mínimo, "
            "pagamento, alergias, problemas com o pedido e contato."
        ),
        fonte=texto_loja,
    ),
}


def esquema_consulta(nome, analista):
    """Ferramenta do orquestrador que encaminha uma pergunta ao analista."""
    return {
        "type": "function",
        "name": nome,
        "description": analista.descricao,
        "parameters": {
            "type": "object",
            "properties": {
                "pergunta": {
                    "type": "string",
                    "description": "Pergunta completa, que se entende sem ler a conversa, com os nomes dos itens.",
                },
            },
            "required": ["pergunta"],
            "additionalProperties": False,
        },
        "strict": True,
    }


ESQUEMAS = [esquema_consulta(nome, analista) for nome, analista in ANALISTAS.items()]


@dataclass
class RespostaAgente:
    """Resposta a uma mensagem do cliente e os analistas consultados."""

    texto: str
    consultas: list = field(default_factory=list)
    falhou: bool = False


class Conversa:
    """Uma conversa com um cliente; o histórico fica em memória até o chat ser reiniciado."""

    def __init__(self, cliente, dados):
        self._cliente = cliente
        self._dados = dados
        # Lista explícita de mensagens, enviada inteira a cada chamada
        self.historico = []

    def responder(self, mensagem, agora=None):
        """Responde à mensagem do cliente, consultando os analistas que o orquestrador escolher."""
        inicio = len(self.historico)
        self.historico.append({"role": "user", "content": mensagem})
        instrucoes = instrucoes_orquestrador(self._dados, agora)
        consultas = []

        try:
            while True:
                # Depois do limite, o orquestrador responde com o que já tem
                resposta = criar_resposta(
                    self._cliente, instrucoes, self.historico, ESQUEMAS, len(consultas) < MAXIMO_CONSULTAS
                )
                self.historico.extend(resposta.output)

                pedidos = [parte for parte in resposta.output if parte.type == "function_call"]
                if not pedidos:
                    return RespostaAgente(texto=resposta.output_text.strip() or RESPOSTA_VAZIA, consultas=consultas)

                for pedido in pedidos:
                    texto = self._consultar(pedido, agora)
                    consultas.append(ANALISTAS[pedido.name].nome if pedido.name in ANALISTAS else pedido.name)
                    self.historico.append({"type": "function_call_output", "call_id": pedido.call_id, "output": texto})

        except openai.APIError as erro:
            # A mensagem com falha sai do histórico, para o cliente poder tentar de novo
            del self.historico[inicio:]
            return RespostaAgente(texto=resposta_de_erro(erro), consultas=consultas, falhou=True)

    def _consultar(self, pedido, agora):
        """Encaminha a pergunta ao analista escolhido pelo orquestrador."""
        analista = ANALISTAS.get(pedido.name)
        if analista is None:
            return "Analista desconhecido."
        try:
            pergunta = json.loads(pedido.arguments or "{}").get("pergunta", "")
        except (json.JSONDecodeError, AttributeError):
            pergunta = ""
        if not pergunta:
            return "A pergunta para o analista veio vazia."
        return analista.responder(self._cliente, self._dados, pergunta, agora)


def resposta_de_erro(erro):
    """Mensagem amigável para o cliente; o detalhe técnico vai só para o log."""
    # Só o tipo e o código: a mensagem do SDK para chave inválida contém parte da chave
    logger.error("Falha na chamada à OpenAI: %s (código %s)", type(erro).__name__, getattr(erro, "code", None))
    if isinstance(erro, openai.APIConnectionError):
        return RESPOSTA_ERRO_CONEXAO
    if isinstance(erro, openai.RateLimitError) and getattr(erro, "code", None) != "insufficient_quota":
        return RESPOSTA_OCUPADA
    return RESPOSTA_ERRO
