"""Ferramentas dos especialistas: funções que consultam os dados da loja, sem LLM."""

import json
import unicodedata
from dataclasses import dataclass
from typing import Callable

from modelo.recomendador import recomendar
from modelo.validacao import validar_carrinho

MAXIMO_PRODUTOS = 10
MAXIMO_PARECIDOS = 5


@dataclass(frozen=True)
class Ferramenta:
    """Função que um especialista pode chamar, com a descrição enviada ao modelo."""

    nome: str
    descricao: str
    parametros: dict
    funcao: Callable

    def esquema(self):
        """Formato de ferramenta da Responses API, em modo estrito."""
        return {
            "type": "function",
            "name": self.nome,
            "description": self.descricao,
            "parameters": self.parametros,
            "strict": True,
        }


def normalizar(texto):
    """Texto em minúsculas e sem acentos."""
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return sem_acento.lower()


def palavras_da_busca(termo):
    """Palavras do termo, sem as muito curtas e sem o 's' do plural."""
    palavras = []
    for palavra in normalizar(termo).replace(",", " ").split():
        if len(palavra) <= 2:
            continue
        if len(palavra) > 3 and palavra.endswith("s"):
            palavra = palavra[:-1]
        palavras.append(palavra)
    return palavras


def buscar_produtos(dados, termo):
    """Itens cujo nome, categoria ou descrição contêm todas as palavras do termo."""
    palavras = palavras_da_busca(termo)
    if not palavras:
        return {"encontrados": 0, "produtos": [], "categorias": sorted(dados.produtos["categoria"].unique())}

    # Posição de cada item na lista dos mais pedidos
    ranking = {item: posicao for posicao, item in enumerate(dados.populares)}

    resultados = []
    for linha in dados.produtos.itertuples():
        nome = normalizar(linha.item)
        texto = f"{nome} {normalizar(linha.categoria)} {normalizar(linha.descricao)}"
        if all(palavra in texto for palavra in palavras):
            # Itens com as palavras no nome aparecem primeiro; depois, os mais pedidos
            fora_do_nome = not all(palavra in nome for palavra in palavras)
            produto = {"item": linha.item, "categoria": linha.categoria, "descricao": linha.descricao}
            resultados.append((fora_do_nome, ranking.get(linha.item, len(ranking)), produto))

    resultados.sort(key=lambda resultado: (resultado[0], resultado[1]))
    return {
        "encontrados": len(resultados),
        "produtos": [produto for _, _, produto in resultados[:MAXIMO_PRODUTOS]],
    }


def itens_que_saem_junto(dados, itens):
    """Valida os itens e devolve o que costuma ser pedido junto com eles."""
    verificacao = validar_carrinho(itens, dados.populares)

    # Itens fora do cardápio: devolve nomes parecidos para o especialista escolher ou perguntar
    if not verificacao["ok"]:
        nao_encontrados = []
        for erro in verificacao["errors"]:
            if erro["code"] == "unknown_item":
                posicao = int(erro["field"][len("carrinho["):-1])
                termo = itens[posicao]
                parecidos = buscar_produtos(dados, termo)["produtos"][:MAXIMO_PARECIDOS]
                nao_encontrados.append({"termo": termo, "parecidos": [produto["item"] for produto in parecidos]})
        return {"ok": False, "errors": verificacao["errors"], "nao_encontrados": nao_encontrados}

    sugestoes = []
    for sugestao in recomendar(verificacao["value"], dados.regras, dados.populares):
        if sugestao["origem"] == "regra":
            sugestoes.append({
                "item": sugestao["item"],
                "pedidos_com": sugestao["antecedente"],
                "a_cada_100_pedidos": round(sugestao["confianca"] * 100),
            })
        else:
            sugestoes.append({"item": sugestao["item"], "observacao": "um dos itens mais pedidos da casa"})

    return {"ok": True, "itens": verificacao["value"], "sugestoes": sugestoes}


def consultar_dados_da_loja(dados):
    """Devolve o documento com os dados da empresa."""
    return {"loja": dados.nome, "dados": dados.informacoes}


BUSCAR_PRODUTOS = Ferramenta(
    nome="buscar_produtos",
    descricao=(
        "Busca itens do cardápio pelo nome, pela categoria ou por palavras da descrição "
        "(ingredientes, picância, 'vegetariana'). Devolve nome, categoria e descrição."
    ),
    parametros={
        "type": "object",
        "properties": {
            "termo": {"type": "string", "description": "Poucas palavras, por exemplo 'burrito', 'korma' ou 'vegetariana'."},
        },
        "required": ["termo"],
        "additionalProperties": False,
    },
    funcao=lambda dados, termo: buscar_produtos(dados, termo),
)

ITENS_QUE_SAEM_JUNTO = Ferramenta(
    nome="itens_que_saem_junto",
    descricao=(
        "Recebe itens do cardápio e devolve o que costuma ser pedido junto com eles, "
        "calculado a partir do histórico de pedidos da loja."
    ),
    parametros={
        "type": "object",
        "properties": {
            "itens": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Nomes dos itens, como aparecem no cardápio.",
            },
        },
        "required": ["itens"],
        "additionalProperties": False,
    },
    funcao=lambda dados, itens: itens_que_saem_junto(dados, itens),
)

CONSULTAR_DADOS_DA_LOJA = Ferramenta(
    nome="consultar_dados_da_loja",
    descricao=(
        "Devolve os dados da empresa: endereço, horário, delivery, taxas, pedido mínimo, "
        "formas de pagamento, alergias, problemas com o pedido e contato."
    ),
    parametros={"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    funcao=lambda dados: consultar_dados_da_loja(dados),
)


def executar(ferramenta, argumentos_json, dados):
    """Executa a ferramenta com os argumentos enviados pelo modelo; erros viram resposta, não exceção."""
    try:
        argumentos = json.loads(argumentos_json or "{}")
        return ferramenta.funcao(dados, **argumentos)
    except (json.JSONDecodeError, TypeError, ValueError) as erro:
        return {"erro": f"não foi possível executar {ferramenta.nome}: {type(erro).__name__}"}
