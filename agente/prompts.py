"""Montagem das instruções de cada agente a partir dos arquivos de agente/prompts/<agente>/."""

from datetime import datetime
from functools import cache
from pathlib import Path
from zoneinfo import ZoneInfo

PASTA_PROMPTS = Path(__file__).resolve().parent / "prompts"
FUSO = ZoneInfo("America/Sao_Paulo")
DIAS_DA_SEMANA = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")


@cache
def ler_prompt(agente, arquivo):
    """Lê um arquivo de prompt uma vez por execução."""
    return (PASTA_PROMPTS / agente / f"{arquivo}.md").read_text(encoding="utf-8").strip()


def preencher(texto, dados):
    """Troca os marcadores {loja} e {atendente} pelos dados da loja."""
    return texto.replace("{loja}", dados.nome).replace("{atendente}", dados.atendente)


def descrever_agora(agora=None):
    """Dia da semana, data e hora em São Paulo."""
    agora = (agora or datetime.now(FUSO)).astimezone(FUSO)
    return f"Agora em São Paulo: {DIAS_DA_SEMANA[agora.weekday()]}, {agora:%d/%m/%Y}, {agora:%H:%M}."


def instrucoes_orquestrador(dados, agora=None):
    """Persona e diretrizes do orquestrador, com a data e a hora no final."""
    partes = [
        f"# Persona\n\n{ler_prompt('orquestrador', 'persona')}",
        f"# Diretrizes\n\n{ler_prompt('orquestrador', 'diretrizes')}",
        f"# Data e hora\n\n{descrever_agora(agora)}",
    ]
    return preencher("\n\n".join(partes), dados)


def instrucoes_especialista(agente, dados, agora=None):
    """Prompt do especialista, com a data e a hora no final."""
    partes = [ler_prompt(agente, "prompt"), f"# Data e hora\n\n{descrever_agora(agora)}"]
    return preencher("\n\n".join(partes), dados)
