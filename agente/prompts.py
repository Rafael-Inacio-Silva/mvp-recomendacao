"""Montagem das instruções de cada agente a partir dos arquivos de agente/prompts/."""

import re
from datetime import datetime, timedelta
from functools import cache
from pathlib import Path
from zoneinfo import ZoneInfo

PASTA_PROMPTS = Path(__file__).resolve().parent / "prompts"
FUSO = ZoneInfo("America/Sao_Paulo")
DIAS_DA_SEMANA = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")
ESTAGIOS = (1, 2, 3)
DIAS_DE_REFERENCIA = 7


@cache
def ler_arquivo(caminho):
    """Lê um arquivo de agente/prompts/ uma vez por execução."""
    return (PASTA_PROMPTS / caminho).read_text(encoding="utf-8").strip()


@cache
def ler_estagio(numero):
    """Nome, objetivo e instrução do estágio, lidos de orquestrador/estagios/estagio_<n>_*.md."""
    arquivo = next((PASTA_PROMPTS / "orquestrador" / "estagios").glob(f"estagio_{numero}_*.md"))

    # O arquivo tem as linhas "Nome", "Objetivo" e "Instrução", cada uma seguida do seu texto
    partes = re.split(r"^(Nome|Objetivo|Instrução)[ \t]*$", arquivo.read_text(encoding="utf-8"), flags=re.MULTILINE)
    campos = {partes[posicao]: partes[posicao + 1].strip() for posicao in range(1, len(partes), 2)}

    return {"numero": numero, "nome": campos["Nome"], "objetivo": campos["Objetivo"], "instrucao": campos["Instrução"]}


def formatar_data(dia):
    return f"{DIAS_DA_SEMANA[dia.weekday()]}, {dia:%d/%m/%Y}"


def descrever_agora(agora=None):
    """Dia da semana, data e hora em São Paulo."""
    agora = (agora or datetime.now(FUSO)).astimezone(FUSO)
    return f"{formatar_data(agora)}, {agora:%H:%M} (horário de São Paulo)"


def referencias_data(agora=None):
    """Hoje e os próximos dias, com o dia da semana de cada data."""
    agora = (agora or datetime.now(FUSO)).astimezone(FUSO)
    rotulos = {0: "hoje", 1: "amanhã", 2: "depois de amanhã"}

    linhas = []
    for dias in range(DIAS_DE_REFERENCIA + 1):
        rotulo = rotulos.get(dias, f"daqui a {dias} dias")
        linhas.append(f"- {rotulo}: {formatar_data(agora + timedelta(days=dias))}")
    return "\n".join(linhas)


def preencher(texto, valores):
    """Troca cada marcador {{nome}} pelo seu valor."""
    for nome, valor in valores.items():
        texto = texto.replace("{{" + nome + "}}", valor)
    return texto


def valores_da_loja(dados, agora=None):
    return {
        "loja": dados.nome,
        "atendente": dados.atendente,
        "agora": descrever_agora(agora),
        "referencias_data": referencias_data(agora),
    }


def instrucoes_orquestrador(dados, estagio, agora=None):
    """Template base com a etapa atual, a loja e as datas."""
    etapa = ler_estagio(estagio)
    texto = preencher(ler_arquivo("orquestrador/template_base.md"), {
        "etapa_atual": f"{etapa['numero']} — {etapa['nome']}",
        "etapa_objetivo": etapa["objetivo"],
        "etapa_instrucao": etapa["instrucao"],
    })
    # A instrução da etapa também usa {{loja}} e {{atendente}}
    return preencher(texto, valores_da_loja(dados, agora))


def instrucoes_analista(agente, dados, conteudo, agora=None):
    """Prompt do analista com a loja, as datas e os dados da sua área."""
    texto = preencher(ler_arquivo(f"{agente}/prompt.md"), valores_da_loja(dados, agora))
    # Dados por último, para o conteúdo da loja não passar pela troca de marcadores
    return texto.replace("{{dados}}", conteudo)
