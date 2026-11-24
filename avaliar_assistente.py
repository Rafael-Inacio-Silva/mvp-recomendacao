"""Avalia o assistente de conversa das lojas com os casos de dados/<loja>/casos_assistente.json.

Chama a OpenAI de verdade, então tem custo: roda só quando executado, fora do pytest.
Uso: python avaliar_assistente.py [--loja mexicano] [--rodadas 2] [--sem-juiz]
"""

import argparse
import json
import os
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from agente import llm
from agente.avaliacao import ESFORCO_JUIZ, conferir, julgar
from agente.llm import ESFORCO_PADRAO, MODELO_PADRAO, criar_cliente
from agente.orquestrador import Conversa
from agente.prompts import FUSO
from dados_loja import carregar_dados_loja
from lojas import LOJAS, caminho

# Preço do gpt-6-luna em US$ por milhão de tokens (tabela de nov/2026; conferir na página de preços da OpenAI)
PRECO_ENTRADA = 0.10
PRECO_SAIDA = 0.50

# Data e hora fixas, para as respostas sobre "hoje" e "agora" serem comparáveis entre rodadas
AGORA = datetime(2026, 11, 25, 19, 0, tzinfo=FUSO)
CONVERSAS_EM_PARALELO = 4
RELATORIO = Path("docs/avaliacao_assistente.md")


def custo(uso):
    return (uso["entrada"] * PRECO_ENTRADA + uso["saida"] * PRECO_SAIDA) / 1_000_000


def conversar(cliente, dados, caso):
    """Manda as mensagens do caso numa conversa nova e mede o tempo de cada resposta."""
    conversa = Conversa(cliente, dados)
    respostas = []
    for mensagem in caso["mensagens"]:
        inicio = time.perf_counter()
        resposta = conversa.responder(mensagem, agora=AGORA)
        respostas.append({
            "texto": resposta.texto,
            "consultas": resposta.consultas,
            "estagio": resposta.estagio,
            "falhou": resposta.falhou,
            "segundos": time.perf_counter() - inicio,
        })
    return respostas


def avaliar_loja(cliente, cliente_juiz, loja, rodadas, com_juiz):
    dados = carregar_dados_loja(loja)
    casos = json.loads(Path(caminho(loja, "casos_assistente.json")).read_text(encoding="utf-8"))
    tarefas = [(caso, rodada) for caso in casos for rodada in range(rodadas)]

    llm.zerar_uso()
    with ThreadPoolExecutor(CONVERSAS_EM_PARALELO) as executor:
        conversas = list(executor.map(lambda tarefa: conversar(cliente, dados, tarefa[0]), tarefas))
    uso_assistente = dict(llm.uso)

    resultados = defaultdict(list)
    for (caso, _), respostas in zip(tarefas, conversas):
        resultados[caso["id"]].append({"respostas": respostas, "falhas": conferir(caso, respostas, dados.atendente)})

    # O juiz avalia a primeira rodada de cada caso, com esforço de raciocínio maior
    juizes, uso_juiz = {}, None
    if com_juiz:
        llm.zerar_uso()
        with ThreadPoolExecutor(CONVERSAS_EM_PARALELO) as executor:
            vereditos = executor.map(
                lambda caso: julgar(cliente_juiz, dados, caso["mensagens"], resultados[caso["id"]][0]["respostas"], AGORA),
                casos,
            )
            juizes = {caso["id"]: veredito for caso, veredito in zip(casos, vereditos)}
        uso_juiz = dict(llm.uso)

    return {"dados": dados, "casos": casos, "resultados": resultados, "juizes": juizes,
            "uso_assistente": uso_assistente, "uso_juiz": uso_juiz, "rodadas": rodadas}


def resumo(avaliacao):
    """Números do relatório de uma loja."""
    casos, resultados, rodadas = avaliacao["casos"], avaliacao["resultados"], avaliacao["rodadas"]
    aprovacoes = {caso["id"]: sum(not r["falhas"] for r in resultados[caso["id"]]) for caso in casos}
    tempos = [resposta["segundos"] for caso in casos for r in resultados[caso["id"]] for resposta in r["respostas"]]
    conversas = len(casos) * rodadas
    uso = avaliacao["uso_assistente"]
    return {
        "sempre": sum(aprovados == rodadas for aprovados in aprovacoes.values()),
        "instaveis": sum(0 < aprovados < rodadas for aprovados in aprovacoes.values()),
        "aprovacoes": sum(aprovacoes.values()),
        "total": conversas,
        "aprovacoes_por_caso": aprovacoes,
        "tempo_medio": sum(tempos) / len(tempos),
        "tempo_maximo": max(tempos),
        "tokens_por_conversa": (uso["entrada"] + uso["saida"]) / conversas,
        "custo_por_conversa": custo(uso) / conversas,
    }


def por_categoria(avaliacao, numeros):
    totais = defaultdict(lambda: [0, 0])
    for caso in avaliacao["casos"]:
        totais[caso["categoria"]][0] += numeros["aprovacoes_por_caso"][caso["id"]]
        totais[caso["categoria"]][1] += avaliacao["rodadas"]
    return totais


def imprimir(avaliacao, numeros):
    dados = avaliacao["dados"]
    print(f"\n{'#' * 60}\n# {dados.nome} — {dados.atendente}\n{'#' * 60}")
    print(f"Casos aprovados em todas as rodadas: {numeros['sempre']} de {len(avaliacao['casos'])}"
          f" ({numeros['instaveis']} instáveis)")
    print(f"Aprovações: {numeros['aprovacoes']} de {numeros['total']} conversas")
    for categoria, (aprovados, total) in por_categoria(avaliacao, numeros).items():
        print(f"  {categoria:18} {aprovados}/{total}")
    print(f"Tempo por resposta: média {numeros['tempo_medio']:.1f} s, máximo {numeros['tempo_maximo']:.1f} s")
    print(f"Custo por conversa: {numeros['tokens_por_conversa']:,.0f} tokens, US$ {numeros['custo_por_conversa']:.5f}")

    for caso in avaliacao["casos"]:
        for rodada, resultado in enumerate(avaliacao["resultados"][caso["id"]], start=1):
            if resultado["falhas"]:
                print(f"\n  FALHOU {caso['id']} (rodada {rodada}): {'; '.join(resultado['falhas'])}")
                print(f"    resposta: {resultado['respostas'][-1]['texto']}")

    if avaliacao["juizes"]:
        juizes = avaliacao["juizes"].values()
        print(f"\nJuiz ({ESFORCO_JUIZ}): respondeu à pergunta em {sum(j['respondeu_a_pergunta'] for j in juizes)}"
              f" de {len(juizes)}, inventou informação em {sum(j['inventou_informacao'] for j in juizes)},"
              f" tom médio {sum(j['tom'] for j in juizes) / len(juizes):.1f}")


def escrever_relatorio(avaliacoes, rodadas, com_juiz):
    modelo = os.getenv("OPENAI_MODEL", "").strip() or MODELO_PADRAO
    esforco = os.getenv("OPENAI_REASONING_EFFORT", "").strip() or ESFORCO_PADRAO
    linhas = [
        "# Avaliação do assistente de conversa",
        "",
        f"Gerado por `avaliar_assistente.py` em {datetime.now(FUSO):%d/%m/%Y %H:%M}. Modelo `{modelo}`,"
        f" esforço `{esforco}` no assistente{f' e `{ESFORCO_JUIZ}` no juiz' if com_juiz else ''};"
        f" {rodadas} rodada(s) por caso; data simulada {AGORA:%d/%m/%Y %H:%M}.",
        "",
        "| Loja | Casos sempre aprovados | Instáveis | Aprovações | Tempo médio por resposta | Custo por conversa |",
        "|---|---|---|---|---|---|",
    ]
    for avaliacao, numeros in avaliacoes:
        linhas.append(
            f"| {avaliacao['dados'].nome} | {numeros['sempre']} de {len(avaliacao['casos'])} | {numeros['instaveis']}"
            f" | {numeros['aprovacoes']} de {numeros['total']} | {numeros['tempo_medio']:.1f} s"
            f" | {numeros['tokens_por_conversa']:,.0f} tokens · US$ {numeros['custo_por_conversa']:.5f} |"
        )

    for avaliacao, numeros in avaliacoes:
        dados = avaliacao["dados"]
        linhas += ["", f"## {dados.nome}", "",
                   "| Caso | Categoria | Aprovado | Juiz: respondeu | Juiz: inventou | Juiz: tom | Juiz: motivo |",
                   "|---|---|---|---|---|---|---|"]
        for caso in avaliacao["casos"]:
            juiz = avaliacao["juizes"].get(caso["id"])
            colunas_juiz = (
                f"{'sim' if juiz['respondeu_a_pergunta'] else 'não'} | {'sim' if juiz['inventou_informacao'] else 'não'}"
                f" | {juiz['tom']} | {juiz['motivo'].replace('|', '/')}"
            ) if juiz else "- | - | - | -"
            linhas.append(f"| `{caso['id']}` | {caso['categoria']} | {numeros['aprovacoes_por_caso'][caso['id']]}"
                          f"/{rodadas} | {colunas_juiz} |")

        falhas = [(caso, rodada, resultado) for caso in avaliacao["casos"]
                  for rodada, resultado in enumerate(avaliacao["resultados"][caso["id"]], start=1) if resultado["falhas"]]
        if falhas:
            linhas += ["", "**Falhas:**", ""]
            for caso, rodada, resultado in falhas:
                resposta = resultado["respostas"][-1]["texto"].replace("\n", " ")
                linhas.append(f"- `{caso['id']}`, rodada {rodada}: {'; '.join(resultado['falhas'])}. Resposta: “{resposta}”")

    RELATORIO.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"\nRelatório salvo em {RELATORIO}")


def main():
    parser = argparse.ArgumentParser(description="Avaliação do assistente de conversa")
    parser.add_argument("--loja", choices=list(LOJAS), help="avaliar só uma loja")
    parser.add_argument("--rodadas", type=int, default=2, help="vezes que cada caso roda (padrão 2)")
    parser.add_argument("--sem-juiz", action="store_true", help="só as regras determinísticas")
    argumentos = parser.parse_args()

    cliente = criar_cliente()
    if cliente is None:
        raise SystemExit("Falta a OPENAI_API_KEY no .env.")
    # O juiz raciocina mais e precisa de mais tempo por chamada
    cliente_juiz = criar_cliente(tempo_limite=120.0)

    lojas = [argumentos.loja] if argumentos.loja else list(LOJAS)
    avaliacoes = []
    for loja in lojas:
        avaliacao = avaliar_loja(cliente, cliente_juiz, loja, argumentos.rodadas, not argumentos.sem_juiz)
        numeros = resumo(avaliacao)
        imprimir(avaliacao, numeros)
        avaliacoes.append((avaliacao, numeros))

    escrever_relatorio(avaliacoes, argumentos.rodadas, not argumentos.sem_juiz)


if __name__ == "__main__":
    main()
