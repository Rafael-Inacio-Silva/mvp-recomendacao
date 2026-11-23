"""API do MVP: liga o site (frontend) ao recomendador e ao assistente de conversa."""

import os
import re
import threading
from collections import OrderedDict
from typing import Any

import uvicorn
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agente.llm import criar_cliente
from agente.orquestrador import Conversa
from dados_loja import LojaIndisponivel, carregar_dados_loja
from lojas import ATENDENTES, LOJAS
from modelo.explicacao import explicar
from modelo.recomendador import recomendar
from modelo.validacao import validar_carrinho

MAXIMO_CARACTERES_MENSAGEM = 1000
# Conversas antigas saem da memória depois desse limite
MAXIMO_CONVERSAS = 200
PADRAO_CONVERSA_ID = re.compile(r"[A-Za-z0-9-]{8,64}")

app = FastAPI(title="MVP de recomendação de itens")

# Endereços do site em desenvolvimento; em produção, a Vercel repassa /api para o Render
origens = os.getenv("ORIGENS_PERMITIDAS", "http://localhost:5173,http://127.0.0.1:5173")
app.add_middleware(CORSMiddleware, allow_origins=origens.split(","), allow_methods=["GET", "POST"], allow_headers=["*"])


def obter_dados(loja):
    """Dados da loja; 404 para loja desconhecida e 503 quando faltam os arquivos gerados."""
    try:
        return carregar_dados_loja(loja)
    except LojaIndisponivel as erro:
        status = 404 if loja not in LOJAS else 503
        raise HTTPException(status_code=status, detail=str(erro))


def falha(erros, status=400):
    """Resposta de erro no mesmo formato do validador."""
    return JSONResponse(status_code=status, content={"ok": False, "errors": erros})


# ---------------------------------------------------------------- recomendação


@app.get("/api/saude")
def saude():
    return {"status": "ok"}


@app.get("/api/lojas")
def listar_lojas():
    return [{"loja": loja, "nome": nome, "atendente": ATENDENTES[loja]} for loja, nome in LOJAS.items()]


@app.get("/api/lojas/{loja}/cardapio")
def cardapio(loja: str):
    dados = obter_dados(loja)

    # Itens do mais pedido para o menos pedido
    ranking = {item: posicao for posicao, item in enumerate(dados.populares)}
    produtos = dados.produtos.assign(posicao=dados.produtos["item"].map(ranking)).sort_values("posicao")
    itens = produtos[["item", "categoria", "descricao"]].to_dict("records")
    return {"loja": loja, "nome": dados.nome, "itens": itens}


@app.post("/api/lojas/{loja}/sugestoes")
def sugestoes(loja: str, corpo: Any = Body(None)):
    dados = obter_dados(loja)

    if not isinstance(corpo, dict):
        return falha([{"field": "corpo", "code": "invalid_type"}])

    # Validação do carrinho antes da recomendação (RN-09)
    verificacao = validar_carrinho(corpo.get("carrinho"), dados.populares)
    if not verificacao["ok"]:
        return falha(verificacao["errors"])

    carrinho = verificacao["value"]
    resposta = []
    for sugestao in recomendar(carrinho, dados.regras, dados.populares):
        resposta.append({
            "item": sugestao["item"],
            "frase": explicar(sugestao, dados.cardapio),
            "origem": sugestao["origem"],
        })
    return {"ok": True, "carrinho": carrinho, "sugestoes": resposta}


# ---------------------------------------------------------------- assistente de conversa


class Conversas:
    """Conversas abertas, guardadas em memória por loja e identificador."""

    def __init__(self):
        self._conversas = OrderedDict()
        self._trava = threading.Lock()
        self._cliente = None

    def obter(self, loja, conversa_id, dados):
        """Devolve a conversa existente ou cria uma nova, com o histórico vazio."""
        with self._trava:
            if self._cliente is None:
                self._cliente = criar_cliente()
            if self._cliente is None:
                return None

            chave = (loja, conversa_id)
            if chave not in self._conversas:
                self._conversas[chave] = Conversa(self._cliente, dados)
                if len(self._conversas) > MAXIMO_CONVERSAS:
                    self._conversas.popitem(last=False)
            self._conversas.move_to_end(chave)
            return self._conversas[chave]

    def reiniciar(self, loja, conversa_id):
        """Apaga o histórico da conversa."""
        with self._trava:
            self._conversas.pop((loja, conversa_id), None)


conversas = Conversas()


def validar_conversa_id(conversa_id):
    """Erros do identificador da conversa, no formato do validador."""
    if conversa_id is None:
        return [{"field": "conversa_id", "code": "null"}]
    if not isinstance(conversa_id, str) or not PADRAO_CONVERSA_ID.fullmatch(conversa_id):
        return [{"field": "conversa_id", "code": "invalid_type"}]
    return []


@app.post("/api/lojas/{loja}/chat")
def chat(loja: str, corpo: Any = Body(None)):
    dados = obter_dados(loja)

    if not isinstance(corpo, dict):
        return falha([{"field": "corpo", "code": "invalid_type"}])

    erros = validar_conversa_id(corpo.get("conversa_id"))
    mensagem = corpo.get("mensagem")
    if mensagem is None:
        erros.append({"field": "mensagem", "code": "null"})
    elif not isinstance(mensagem, str):
        erros.append({"field": "mensagem", "code": "invalid_type"})
    elif not mensagem.strip():
        erros.append({"field": "mensagem", "code": "empty"})
    elif len(mensagem) > MAXIMO_CARACTERES_MENSAGEM:
        erros.append({"field": "mensagem", "code": "too_long"})
    if erros:
        return falha(erros)

    conversa = conversas.obter(loja, corpo["conversa_id"], dados)
    if conversa is None:
        return falha([{"field": "assistente", "code": "unavailable"}], status=503)

    resposta = conversa.responder(mensagem.strip())
    return {"ok": not resposta.falhou, "resposta": resposta.texto, "consultas": resposta.consultas}


@app.post("/api/lojas/{loja}/chat/reiniciar")
def reiniciar_chat(loja: str, corpo: Any = Body(None)):
    obter_dados(loja)

    if not isinstance(corpo, dict):
        return falha([{"field": "corpo", "code": "invalid_type"}])

    erros = validar_conversa_id(corpo.get("conversa_id"))
    if erros:
        return falha(erros)

    conversas.reiniciar(loja, corpo["conversa_id"])
    return {"ok": True}


if __name__ == "__main__":
    # No Render, a porta vem da variável PORT
    uvicorn.run("api:app", host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
