"""Orquestrador (coordenador): conversa com o cliente, guarda o histórico e decide quais analistas consultar."""

import json
import logging
from dataclasses import dataclass, field

import openai

from agente.analista import Analista
from agente.fontes import texto_cardapio, texto_combinacoes, texto_loja
from agente.llm import criar_resposta
from agente.prompts import ESTAGIOS, instrucoes_orquestrador, ler_estagio

logger = logging.getLogger(__name__)

MAXIMO_CONSULTAS = 4
MAXIMO_CHAMADAS = 8

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
            "pagamento, alergias, pedidos especiais (como menos picante), problemas com o pedido e contato."
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


# Ferramenta para o orquestrador registrar que o critério de avanço da etapa foi cumprido
AVANCAR_ESTAGIO = {
    "type": "function",
    "name": "avancar_estagio",
    "description": (
        "Registra que o critério de avanço da etapa atual foi cumprido e muda para a próxima etapa. "
        "Chame antes de responder ao cliente."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "estagio": {"type": "integer", "enum": list(ESTAGIOS[1:]), "description": "Número da próxima etapa."},
        },
        "required": ["estagio"],
        "additionalProperties": False,
    },
    "strict": True,
}

ESQUEMAS = [esquema_consulta(nome, analista) for nome, analista in ANALISTAS.items()] + [AVANCAR_ESTAGIO]


@dataclass
class RespostaAgente:
    """Resposta a uma mensagem do cliente e os analistas consultados."""

    texto: str
    consultas: list = field(default_factory=list)
    estagio: int = 1
    falhou: bool = False


class Conversa:
    """Uma conversa com um cliente; o histórico fica em memória até o chat ser reiniciado."""

    def __init__(self, cliente, dados):
        self._cliente = cliente
        self._dados = dados
        # Lista explícita de mensagens, enviada inteira a cada chamada
        self.historico = []
        # Etapa do atendimento: 1 Conexão, 2 Atendimento, 3 Fechamento
        self.estagio = ESTAGIOS[0]

    def responder(self, mensagem, agora=None):
        """Responde à mensagem do cliente, consultando os analistas que o orquestrador escolher."""
        inicio = len(self.historico)
        estagio_inicial = self.estagio
        self.historico.append({"role": "user", "content": mensagem})
        consultas = []
        chamadas = 0

        try:
            while True:
                # Só a etapa atual entra nas instruções
                instrucoes = instrucoes_orquestrador(self._dados, self.estagio, agora)

                # Depois dos limites, o orquestrador responde com o que já tem
                permitir = len(consultas) < MAXIMO_CONSULTAS and chamadas < MAXIMO_CHAMADAS
                resposta = criar_resposta(self._cliente, instrucoes, self.historico, ESQUEMAS, permitir)
                self.historico.extend(resposta.output)

                pedidos = [parte for parte in resposta.output if parte.type == "function_call"]
                if not pedidos:
                    texto = resposta.output_text.strip() or RESPOSTA_VAZIA
                    return RespostaAgente(texto=texto, consultas=consultas, estagio=self.estagio)

                for pedido in pedidos:
                    chamadas += 1
                    if pedido.name == AVANCAR_ESTAGIO["name"]:
                        texto = self._avancar_estagio(pedido)
                    else:
                        texto = self._consultar(pedido, agora)
                        consultas.append(ANALISTAS[pedido.name].nome if pedido.name in ANALISTAS else pedido.name)
                    self.historico.append({"type": "function_call_output", "call_id": pedido.call_id, "output": texto})

        except openai.APIError as erro:
            # A mensagem com falha sai do histórico, para o cliente poder tentar de novo
            del self.historico[inicio:]
            self.estagio = estagio_inicial
            return RespostaAgente(texto=resposta_de_erro(erro), consultas=consultas, estagio=self.estagio, falhou=True)

    def _avancar_estagio(self, pedido):
        """Muda para a etapa pedida pelo orquestrador; nunca volta de etapa."""
        try:
            novo = int(json.loads(pedido.arguments or "{}").get("estagio"))
        except (json.JSONDecodeError, AttributeError, TypeError, ValueError):
            return "Etapa inválida. A etapa não mudou."
        if novo not in ESTAGIOS or novo <= self.estagio:
            return f"A etapa continua {self.estagio}: não é possível voltar nem repetir etapa."
        self.estagio = novo
        return f"Etapa atual: {novo} — {ler_estagio(novo)['nome']}. Siga a instrução dessa etapa."

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
