"""Recomendação de restaurantes: conteúdo (TF-IDF e cosseno) somado a avaliação, frete e entrega, com pesos."""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

# RN-R04
PESOS_PADRAO = {"conteudo": 0.40, "avaliacao": 0.30, "frete": 0.15, "entrega": 0.15}
QUANTIDADE = 10  # RN-R06

# Escalas fixas das notas de 0 a 1
FRETE_MAXIMO = 15.0
TEMPO_IDEAL = 20
TEMPO_LIMITE = 70

FAIXAS_TEXTO = {1: "muito barato", 2: "barato", 3: "preço moderado", 4: "caro", 5: "muito caro"}
PALAVRAS_VAZIAS = ["a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "com", "em", "na", "no", "para", "the"]


def texto_restaurante(linha):
    """Texto comparado com a busca: nome, culinária, faixa de preço e etiquetas úteis."""
    partes = [linha["nome"], linha["culinaria"], FAIXAS_TEXTO.get(linha["faixa_preco"], "")]
    if isinstance(linha["etiquetas"], str):
        partes.append(linha["etiquetas"].replace(";", " "))
    return " ".join(parte for parte in partes if parte)


def montar_indice(restaurantes):
    """Vetores TF-IDF dos restaurantes de uma cidade e a nota usada para quem não tem avaliação."""
    restaurantes = restaurantes.reset_index(drop=True)
    vetorizador = TfidfVectorizer(strip_accents="unicode", lowercase=True, stop_words=PALAVRAS_VAZIAS)
    matriz = vetorizador.fit_transform(restaurantes.apply(texto_restaurante, axis=1))
    return {
        "restaurantes": restaurantes,
        "vetorizador": vetorizador,
        "matriz": matriz,
        # RN-R03: primeiro quartil das notas da cidade
        "nota_sem_avaliacao": float(restaurantes["nota"].quantile(0.25)),
    }


def nota_frete(frete):
    """R$ 0 vale 1 e R$ 15 ou mais vale 0."""
    return 1 - frete.clip(0, FRETE_MAXIMO) / FRETE_MAXIMO


def nota_entrega(tempo):
    """20 minutos ou menos vale 1 e 70 minutos ou mais vale 0."""
    return 1 - ((tempo - TEMPO_IDEAL) / (TEMPO_LIMITE - TEMPO_IDEAL)).clip(0, 1)


def pesos_efetivos(pesos, preferencia):
    """Pesos que somam 1; sem texto livre, o peso do conteúdo é dividido entre os outros critérios (RN-R04)."""
    pesos = dict(pesos or PESOS_PADRAO)
    if not (preferencia or "").strip():
        pesos["conteudo"] = 0.0
    total = sum(pesos.values())
    if total == 0:
        # Só o conteúdo tinha peso e não há texto: vale a ordem pela avaliação
        return {"conteudo": 0.0, "avaliacao": 1.0, "frete": 0.0, "entrega": 0.0}
    return {criterio: peso / total for criterio, peso in pesos.items()}


def semelhanca(indice, texto, linhas):
    """Cosseno entre o texto e cada restaurante das linhas; zero quando não há texto."""
    if not texto.strip():
        return pd.Series(0.0, index=linhas)
    vetor = indice["vetorizador"].transform([texto])
    # Os vetores do TF-IDF já têm norma 1, então o produto escalar é o cosseno
    return pd.Series(linear_kernel(vetor, indice["matriz"][linhas]).ravel(), index=linhas)


def formatar_valor(valor):
    return f"{valor:.2f}".replace(".", ",")


def explicar(restaurante, preferencia):
    """Frase da recomendação, montada com os dados do restaurante (RN-R08)."""
    partes = [f"Nota {restaurante['nota']:.1f}".replace(".", ",") if restaurante["avaliado"] else "Sem avaliação"]
    partes.append("frete grátis" if restaurante["frete"] == 0 else f"frete R$ {formatar_valor(restaurante['frete'])}")
    partes.append(f"entrega em cerca de {restaurante['tempo']} min")
    if preferencia and restaurante["combina_com_busca"]:
        partes.append(f"combina com “{preferencia}”")
    return " · ".join(partes)


def recomendar_restaurantes(indice, culinaria=None, preferencia="", pesos=None, quantidade=QUANTIDADE):
    """Os restaurantes mais indicados da cidade do índice, já validados e com pesos que somam 1."""
    preferencia = (preferencia or "").strip()
    pesos = pesos_efetivos(pesos, preferencia)
    restaurantes = indice["restaurantes"]

    # RN-R02: só a culinária escolhida
    filtro = restaurantes["culinaria"] == culinaria if culinaria else pd.Series(True, index=restaurantes.index)
    linhas = restaurantes.index[filtro]
    candidatos = restaurantes.loc[linhas].copy()

    # Quatro notas de 0 a 1; a culinária já filtrou, então o conteúdo compara só o texto livre
    candidatos["parte_conteudo"] = semelhanca(indice, preferencia, linhas)
    candidatos["parte_avaliacao"] = candidatos["nota"].fillna(indice["nota_sem_avaliacao"]) / 5
    candidatos["parte_frete"] = nota_frete(candidatos["frete"])
    candidatos["parte_entrega"] = nota_entrega(candidatos["tempo"])
    candidatos["combina_com_busca"] = candidatos["parte_conteudo"] > 0

    candidatos["pontuacao"] = sum(pesos[criterio] * candidatos[f"parte_{criterio}"] for criterio in PESOS_PADRAO)

    # RN-R06: maior pontuação primeiro; empate decidido pela nota e depois pelo nome
    candidatos = candidatos.sort_values(["pontuacao", "nota", "nome"], ascending=[False, False, True], na_position="last")

    # RN-R05: uma unidade por nome na cidade, a de maior pontuação
    candidatos = candidatos.loc[~candidatos["nome"].str.strip().str.lower().duplicated()]

    resultado = []
    for _, linha in candidatos.head(quantidade).iterrows():
        restaurante = {
            "nome": linha["nome"],
            "culinaria": linha["culinaria"],
            "nota": None if pd.isna(linha["nota"]) else float(linha["nota"]),
            "avaliado": not pd.isna(linha["nota"]),
            "frete": float(linha["frete"]),
            "tempo": int(linha["tempo"]),
            "faixa_preco": int(linha["faixa_preco"]),
            "pedido_minimo": None if pd.isna(linha["pedido_minimo"]) else float(linha["pedido_minimo"]),
            "pontuacao": round(float(linha["pontuacao"]), 4),
            "partes": {criterio: round(float(linha[f"parte_{criterio}"]), 4) for criterio in PESOS_PADRAO},
            "combina_com_busca": bool(linha["combina_com_busca"]),
            # Identificador da loja com site próprio no MVP, ou None
            "loja": linha["loja"] if isinstance(linha.get("loja"), str) else None,
        }
        restaurante["explicacao"] = explicar(restaurante, preferencia)
        resultado.append(restaurante)
    return resultado
