"""Serviço do chat: valida as mensagens e guarda as conversas abertas em memória."""

import re
import threading
from collections import OrderedDict

from agente.llm import criar_cliente
from agente.orquestrador import Conversa
from servicos.erros import EntradaInvalida, Indisponivel, erro
from servicos.recomendacao import carregar_loja

MAXIMO_CARACTERES_MENSAGEM = 1000
# Conversas antigas saem da memória depois desse limite
MAXIMO_CONVERSAS = 200
PADRAO_CONVERSA_ID = re.compile(r"[A-Za-z0-9-]{8,64}")


def validar_conversa_id(conversa_id):
    if conversa_id is None:
        return [erro("conversa_id", "null")]
    if not isinstance(conversa_id, str) or not PADRAO_CONVERSA_ID.fullmatch(conversa_id):
        return [erro("conversa_id", "invalid_type", "Identificador com 8 a 64 letras, números ou hífens.")]
    return []


def validar_mensagem(mensagem):
    if mensagem is None:
        return [erro("mensagem", "null")]
    if not isinstance(mensagem, str):
        return [erro("mensagem", "invalid_type")]
    if not mensagem.strip():
        return [erro("mensagem", "empty")]
    if len(mensagem) > MAXIMO_CARACTERES_MENSAGEM:
        return [erro("mensagem", "too_long", f"Mensagem com mais de {MAXIMO_CARACTERES_MENSAGEM} caracteres.")]
    return []


class ServicoChat:
    """Conversas abertas, guardadas em memória por loja e identificador."""

    def __init__(self):
        self._conversas = OrderedDict()
        self._trava = threading.Lock()
        self._cliente = None

    def responder(self, loja, conversa_id, mensagem):
        """Valida a entrada antes de chamar o assistente e devolve a resposta."""
        dados = carregar_loja(loja)

        erros = validar_conversa_id(conversa_id) + validar_mensagem(mensagem)
        if erros:
            raise EntradaInvalida(erros)

        conversa = self._obter_conversa(dados, conversa_id)
        resposta = conversa.responder(mensagem.strip())
        return {"ok": not resposta.falhou, "resposta": resposta.texto, "consultas": resposta.consultas, "estagio": resposta.estagio}

    def encerrar(self, loja, conversa_id):
        """Apaga o histórico; a próxima mensagem começa uma conversa nova, na etapa 1."""
        carregar_loja(loja)

        erros = validar_conversa_id(conversa_id)
        if erros:
            raise EntradaInvalida(erros)

        with self._trava:
            self._conversas.pop((loja, conversa_id), None)
        return {"ok": True}

    def _obter_conversa(self, dados, conversa_id):
        """Conversa existente ou uma nova, com o histórico vazio."""
        with self._trava:
            if self._cliente is None:
                self._cliente = criar_cliente()
            if self._cliente is None:
                raise Indisponivel([erro("assistente", "unavailable", "O assistente está indisponível no momento.")])

            chave = (dados.loja, conversa_id)
            if chave not in self._conversas:
                self._conversas[chave] = Conversa(self._cliente, dados)
                if len(self._conversas) > MAXIMO_CONVERSAS:
                    self._conversas.popitem(last=False)
            self._conversas.move_to_end(chave)
            return self._conversas[chave]
