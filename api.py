"""API do MVP (controller): recebe as requisições do site, chama os serviços e devolve a resposta em JSON."""

import os
from typing import Any

import uvicorn
from fastapi import Body, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from servicos import recomendacao, restaurantes
from servicos.chat import ServicoChat
from servicos.erros import EntradaInvalida, ErroDoServico, Indisponivel, NaoEncontrado, erro

app = FastAPI(title="MVP de recomendação de itens")

# Endereços do site em desenvolvimento; em produção, a Vercel repassa /api para o Render
origens = os.getenv("ORIGENS_PERMITIDAS", "http://localhost:5173,http://127.0.0.1:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens.split(","),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

servico_chat = ServicoChat()

# Status HTTP de cada erro dos serviços
STATUS = {EntradaInvalida: 400, NaoEncontrado: 404, Indisponivel: 503}
ERRO_CORPO = erro("corpo", "invalid_type", "O corpo da requisição precisa ser um objeto JSON.")


def falha(status, erros):
    return JSONResponse(status_code=status, content={"ok": False, "errors": erros})


def ler_corpo(corpo):
    """O corpo precisa ser um objeto JSON para que os campos possam ser extraídos."""
    if not isinstance(corpo, dict):
        raise EntradaInvalida([ERRO_CORPO])
    return corpo


# ---------------------------------------------------------------- conversão de erros em status HTTP


@app.exception_handler(ErroDoServico)
def erro_do_servico(requisicao, excecao):
    return falha(STATUS[type(excecao)], excecao.erros)


@app.exception_handler(RequestValidationError)
def json_invalido(requisicao, excecao):
    return falha(400, [ERRO_CORPO])


@app.exception_handler(HTTPException)
def erro_de_rota(requisicao, excecao):
    """Rota que não existe (404) ou método que a rota não aceita (405)."""
    if excecao.status_code == 405:
        return falha(405, [erro("rota", "method_not_allowed", "Método não aceito nesta rota.")])
    return falha(excecao.status_code, [erro("rota", "not_found", "Rota não encontrada.")])


# ---------------------------------------------------------------- recomendação


@app.get("/api/saude")
def saude():
    return {"status": "ok"}


@app.get("/api/lojas")
def listar_lojas():
    return recomendacao.listar_lojas()


@app.get("/api/lojas/{loja}/cardapio")
def cardapio(loja: str):
    return recomendacao.ver_cardapio(loja)


@app.post("/api/lojas/{loja}/sugestoes")
def sugestoes(loja: str, corpo: Any = Body(None)):
    corpo = ler_corpo(corpo)
    return recomendacao.sugerir(loja, corpo.get("carrinho"))


# ---------------------------------------------------------------- assistente de conversa


@app.post("/api/lojas/{loja}/chat")
def chat(loja: str, corpo: Any = Body(None)):
    corpo = ler_corpo(corpo)
    return servico_chat.responder(loja, corpo.get("conversa_id"), corpo.get("mensagem"))


@app.delete("/api/lojas/{loja}/chat/{conversa_id}")
def encerrar_chat(loja: str, conversa_id: str):
    return servico_chat.encerrar(loja, conversa_id)


# ---------------------------------------------------------------- recomendação de restaurantes


@app.get("/api/restaurantes/cidades")
def cidades():
    return restaurantes.listar_cidades()


@app.get("/api/restaurantes/{cidade}/culinarias")
def culinarias(cidade: str):
    return restaurantes.listar_culinarias(cidade)


@app.post("/api/restaurantes/{cidade}/recomendacoes")
def recomendacoes(cidade: str, corpo: Any = Body(None)):
    corpo = ler_corpo(corpo)
    return restaurantes.recomendar(cidade, corpo.get("culinaria"), corpo.get("preferencia"), corpo.get("pesos"))


if __name__ == "__main__":
    # No Render, a porta vem da variável PORT
    uvicorn.run("api:app", host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
