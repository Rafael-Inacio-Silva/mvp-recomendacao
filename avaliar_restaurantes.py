"""Avaliação offline da recomendação de restaurantes nas três cidades.

Sem dados de cliques, não há "acerto" para medir: o top 10 do sistema é comparado com a ordem
alfabética (a lista atual do cliente) e com ordenações por um único critério.
"""

import pandas as pd

from cidades import CIDADES
from dados_restaurantes import indice_da_cidade
from modelo.restaurantes import PESOS_PADRAO, recomendar_restaurantes

CULINARIAS_POR_CIDADE = 5
TEXTOS = ["sushi", "temaki", "vegetariano", "açaí", "pastel", "esfiha", "tapioca", "poke"]

UM_CRITERIO = {
    "Só a nota": {"conteudo": 0, "avaliacao": 1, "frete": 0, "entrega": 0},
    "Só o frete": {"conteudo": 0, "avaliacao": 0, "frete": 1, "entrega": 0},
    "Só o tempo": {"conteudo": 0, "avaliacao": 0, "frete": 0, "entrega": 1},
}


def ordem_alfabetica(indice, culinaria):
    restaurantes = indice["restaurantes"]
    lista = restaurantes[restaurantes["culinaria"] == culinaria].sort_values("nome")
    lista = lista.loc[~lista["nome"].str.strip().str.lower().duplicated()].head(10)
    return [{"nota": None if pd.isna(nota) else nota, "frete": frete, "tempo": tempo}
            for nota, frete, tempo in zip(lista["nota"], lista["frete"], lista["tempo"])]


def medir(top10):
    notas = [restaurante["nota"] for restaurante in top10 if restaurante["nota"] is not None]
    return {
        "nota média": sum(notas) / len(notas) if notas else float("nan"),
        "sem avaliação": 1 - len(notas) / len(top10),
        "frete médio": sum(restaurante["frete"] for restaurante in top10) / len(top10),
        "tempo médio": sum(restaurante["tempo"] for restaurante in top10) / len(top10),
    }


def buscas_por_culinaria():
    """As culinárias mais comuns de cada cidade, sem texto livre."""
    for cidade in CIDADES:
        indice = indice_da_cidade(cidade)
        for culinaria in indice["restaurantes"]["culinaria"].value_counts().head(CULINARIAS_POR_CIDADE).index:
            yield cidade, indice, culinaria


def comparar_ordenacoes():
    linhas = []
    for cidade, indice, culinaria in buscas_por_culinaria():
        formas = {"Ordem alfabética (lista atual)": ordem_alfabetica(indice, culinaria)}
        formas.update({nome: recomendar_restaurantes(indice, culinaria, "", pesos) for nome, pesos in UM_CRITERIO.items()})
        formas["Sistema híbrido (pesos padrão)"] = recomendar_restaurantes(indice, culinaria)
        for forma, top10 in formas.items():
            linhas.append({"forma": forma, **medir(top10)})
    return pd.DataFrame(linhas).groupby("forma", sort=False).mean()


def medir_aderencia():
    linhas = []
    for cidade in CIDADES:
        indice = indice_da_cidade(cidade)
        for texto in TEXTOS:
            hibrido = recomendar_restaurantes(indice, None, texto)
            # Com peso zero no conteúdo, o texto não muda a ordem, mas ainda indica quem combina com ele
            so_nota = recomendar_restaurantes(indice, None, texto, UM_CRITERIO["Só a nota"])
            linhas.append({
                "texto": texto,
                "híbrido com o texto": sum(r["combina_com_busca"] for r in hibrido) / len(hibrido),
                "só a nota": sum(r["combina_com_busca"] for r in so_nota) / len(so_nota),
                **{f"híbrido: {chave}": valor for chave, valor in medir(hibrido).items()},
            })
    return pd.DataFrame(linhas).groupby("texto", sort=False).mean()


def medir_efeito_dos_pesos():
    linhas = []
    for cidade, indice, culinaria in buscas_por_culinaria():
        padrao = {r["nome"] for r in recomendar_restaurantes(indice, culinaria)}
        for criterio in ["avaliacao", "frete", "entrega"]:
            pesos = dict(PESOS_PADRAO, **{criterio: PESOS_PADRAO[criterio] * 2})
            dobrado = {r["nome"] for r in recomendar_restaurantes(indice, culinaria, "", pesos)}
            linhas.append({"peso dobrado": criterio, "continuam no top 10": len(padrao & dobrado)})
    return pd.DataFrame(linhas).groupby("peso dobrado", sort=False).mean()


if __name__ == "__main__":
    pd.set_option("display.width", 160)
    print(f"Buscas sem texto: {CULINARIAS_POR_CIDADE} culinárias mais comuns de cada uma das {len(CIDADES)} cidades\n")
    print("=== Top 10 de cada forma de ordenar (médias) ===\n")
    print(comparar_ordenacoes().round(2).to_string())
    print("\n=== Aderência ao texto livre (parte do top 10 que combina com o texto) ===\n")
    print(medir_aderencia().round(2).to_string())
    print("\n=== Efeito dos pesos: restaurantes que continuam no top 10 ao dobrar um peso ===\n")
    print(medir_efeito_dos_pesos().round(1).to_string())
