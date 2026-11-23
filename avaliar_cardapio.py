"""Compara os artigos gerados pelo LLM na etapa 6 com o gabarito feito à mão."""

import pandas as pd

ARTIGOS = ["uma porção de", "umas", "uns", "uma", "um"]
CAMINHO_CARDAPIO = "dados/mexicano/cardapio.csv"
CAMINHO_GABARITO = "dados/mexicano/gabarito_cardapio.csv"


def extrair_artigo(na_frase):
    """Retorna o artigo do início da frase, ou vazio quando não há artigo."""
    texto = str(na_frase).lower()
    for artigo in ARTIGOS:
        if texto.startswith(artigo + " "):
            return artigo
    return ""


def comparar(cardapio, gabarito):
    """Junta o artigo do LLM e o do gabarito, item a item."""
    tabela = gabarito.merge(cardapio, on="item", how="left")
    tabela["artigo_llm"] = tabela["na_frase"].apply(extrair_artigo)
    tabela["artigo_correto"] = tabela["artigo_correto"].fillna("").str.strip().str.lower()
    tabela["acertou"] = tabela["artigo_llm"] == tabela["artigo_correto"]
    return tabela[["item", "artigo_correto", "artigo_llm", "na_frase", "acertou"]]


def executar():
    cardapio = pd.read_csv(CAMINHO_CARDAPIO)
    gabarito = pd.read_csv(CAMINHO_GABARITO)

    # Gabarito precisa estar completo
    vazios = gabarito["artigo_correto"].isna() | (gabarito["artigo_correto"].astype(str).str.strip() == "")
    if vazios.any():
        print(f"Gabarito incompleto: {vazios.sum()} de {len(gabarito)} itens sem artigo em {CAMINHO_GABARITO}")
        return

    tabela = comparar(cardapio, gabarito)
    acertos = tabela["acertou"].sum()
    print(f"Artigos corretos do LLM: {acertos} de {len(tabela)} ({acertos / len(tabela):.0%})")

    erros = tabela[~tabela["acertou"]]
    if len(erros):
        print("\nDivergências:")
        print(erros[["item", "artigo_correto", "artigo_llm", "na_frase"]].to_string(index=False))


if __name__ == "__main__":
    executar()
