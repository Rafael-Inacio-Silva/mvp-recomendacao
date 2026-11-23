"""Etapa 6 do pipeline: forma de cada item do cardápio numa frase, gerada por LLM."""

import json
import os

import openai
import pandas as pd
from dotenv import load_dotenv

MODELO_PADRAO = "gpt-6-luna"
ESFORCO_PADRAO = "low"
TAMANHO_LOTE = 50
ARTIGOS = ("um ", "uma ", "uns ", "umas ")

INSTRUCOES = """Você recebe nomes de itens do cardápio de um restaurante de delivery.
Para cada item, escreva como ele aparece no meio desta frase, em português do Brasil:
"Que tal incluir ___ no pedido?"

Regras:
- comece com o artigo indefinido certo: um, uma, uns ou umas;
- para itens que são servidos em porção e cujo nome está no plural (como Nachos), use "uma porção de";
- o nome do item deve aparecer completo, com as mesmas palavras e na mesma ordem;
- só pode mudar maiúsculas para minúsculas, e mantenha maiúsculas em marcas e nomes próprios;
- devolva todos os itens recebidos, com o nome exatamente como veio no campo "item".

Exemplos:
- Bowl de Frango -> um bowl de frango
- Água Mineral -> uma água mineral
- Nachos -> uma porção de nachos"""

FORMATO_RESPOSTA = {
    "type": "json_schema",
    "name": "cardapio",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "itens": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "item": {"type": "string"},
                        "na_frase": {"type": "string"},
                    },
                    "required": ["item", "na_frase"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["itens"],
        "additionalProperties": False,
    },
}


def criar_cliente():
    """Retorna o cliente da OpenAI, ou None quando não há chave no .env."""
    load_dotenv()
    chave = os.getenv("OPENAI_API_KEY", "").strip()
    if not chave:
        return None
    return openai.OpenAI(api_key=chave)


def pedir_ao_llm(cliente, itens):
    """Envia uma lista de itens ao modelo e retorna um dicionário item -> forma na frase."""
    resposta = cliente.responses.create(
        model=os.getenv("OPENAI_MODEL", "").strip() or MODELO_PADRAO,
        instructions=INSTRUCOES,
        input="\n".join(itens),
        reasoning={"effort": os.getenv("OPENAI_REASONING_EFFORT", "").strip() or ESFORCO_PADRAO},
        text={"format": FORMATO_RESPOSTA},
        store=False,
    )
    dados = json.loads(resposta.output_text)
    return {linha["item"]: linha["na_frase"].strip() for linha in dados["itens"]}


def validar(item, na_frase):
    """Confere se a forma começa com artigo e contém o nome do item."""
    texto = na_frase.lower()
    return texto.startswith(ARTIGOS) and item.lower() in texto


def gerar_cardapio(itens, cliente):
    """Gera a forma na frase de cada item; sem resposta válida, usa o nome sem artigo."""
    linhas = []

    for inicio in range(0, len(itens), TAMANHO_LOTE):
        lote = itens[inicio:inicio + TAMANHO_LOTE]

        respostas = {}
        if cliente is not None:
            try:
                respostas = pedir_ao_llm(cliente, lote)
            except (openai.OpenAIError, json.JSONDecodeError, KeyError) as erro:
                print(f"Aviso: falha na chamada ao LLM ({type(erro).__name__}); lote sem artigos")

        for item in lote:
            na_frase = respostas.get(item, "")
            if validar(item, na_frase):
                linhas.append({"item": item, "na_frase": na_frase, "origem": "llm"})
            else:
                linhas.append({"item": item, "na_frase": item, "origem": "sem artigo"})

    return pd.DataFrame(linhas)


def atualizar_cardapio(pedidos, caminho_cardapio, cliente=None):
    """Mantém o cardápio salvo e chama o LLM só para os itens que ainda não estão nele."""
    print("\n=== Etapa 6: cardápio para as frases ===\n")

    if os.path.exists(caminho_cardapio):
        cardapio = pd.read_csv(caminho_cardapio)
    else:
        cardapio = pd.DataFrame(columns=["item", "na_frase", "origem"])

    itens = sorted(pedidos["item"].unique())
    novos = [item for item in itens if item not in set(cardapio["item"])]

    # Sem itens novos, não há chamada ao LLM
    if not novos:
        print(f"Cardápio já salvo em {caminho_cardapio}, com {len(cardapio)} itens")
        return cardapio

    if cliente is None:
        cliente = criar_cliente()
    if cliente is None:
        print("Aviso: OPENAI_API_KEY não encontrada no .env; os itens novos ficam sem artigo")

    print(f"Itens novos para o LLM: {len(novos)}")
    cardapio = pd.concat([cardapio, gerar_cardapio(novos, cliente)], ignore_index=True)
    cardapio = cardapio.sort_values("item").reset_index(drop=True)
    cardapio.to_csv(caminho_cardapio, index=False)
    print(f"Cardápio salvo em {caminho_cardapio}")

    return cardapio


def mostrar_cardapio(cardapio):
    """Exibe quantos itens vieram do LLM e uma amostra do cardápio."""
    print(f"Itens com artigo (LLM): {(cardapio['origem'] == 'llm').sum()}")
    print(f"Itens sem artigo: {(cardapio['origem'] == 'sem artigo').sum()}\n")
    print(cardapio.head(10).to_string(index=False))
