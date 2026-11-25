"""Testes das regras da avaliação do assistente, com respostas escritas à mão (sem o LLM)."""

import json
from pathlib import Path

import pytest

from agente.avaliacao import conferir, normalizar


def resposta(texto, consultas=(), estagio=2, falhou=False):
    return {"texto": texto, "consultas": list(consultas), "estagio": estagio, "falhou": falhou}


CASO = {
    "id": "picancia",
    "mensagens": ["O burrito de carne é picante?"],
    "analistas": ["cardapio"],
    "contem": [["levemente picante", "pouco picante"]],
    "nao_contem": ["r$"],
}


def test_normalizar_tira_acentos_e_maiusculas():
    assert normalizar("  Não É   PICANTE ") == "nao e picante"


def test_resposta_correta_e_aprovada():
    certa = resposta("O Burrito de Carne é levemente picante, por causa da pimenta chipotle.", ["cardapio"])
    assert conferir(CASO, [certa], "Lupe") == []


def test_cada_regra_gera_a_sua_falha():
    errada = resposta("Oi! Eu sou a Lupe. Ele custa R$ 30 e é bem apimentado.", ["loja"])
    assert conferir(CASO, [errada], "Lupe") == [
        "se apresentou de novo",
        "não consultou o analista cardapio",
        "faltou: levemente picante / pouco picante",
        "não podia conter: r$",
    ]


def test_apresentacao_permitida_no_caso_de_identidade():
    caso = {"mensagens": ["Você é uma pessoa?"], "contem": [["virtual"]], "apresentacao_permitida": True}
    assert conferir(caso, [resposta("Sou a Lupe, assistente virtual da casa.")], "Lupe") == []


def test_etapa_minima_e_falha_na_chamada():
    caso = {"mensagens": ["Quais bowls?", "Vou querer o bowl de frango."], "estagio_minimo": 3}
    assert conferir(caso, [resposta("..."), resposta("Ótima escolha!", estagio=2)], "Lupe") == [
        "ficou na etapa 2, esperada 3"
    ]
    assert conferir(caso, [resposta("..."), resposta("", falhou=True)], "Lupe") == ["a chamada ao LLM falhou"]


def test_etapa_maxima():
    caso = {"mensagens": ["Do que é feito o papado?", "Esse simples"], "estagio_maximo": 2}
    assert conferir(caso, [resposta("..."), resposta("...", estagio=3)], "Maya") == ["avançou para a etapa 3, máximo 2"]


@pytest.mark.parametrize("loja", ["mexicano", "indiano"])
def test_arquivos_de_casos_bem_formados(loja):
    casos = json.loads(Path(f"dados/{loja}/casos_assistente.json").read_text(encoding="utf-8"))
    campos = {"id", "categoria", "mensagens", "analistas", "contem", "nao_contem", "estagio_minimo", "estagio_maximo", "apresentacao_permitida"}
    assert len({caso["id"] for caso in casos}) == len(casos)
    for caso in casos:
        assert set(caso) <= campos and caso["mensagens"]
        assert set(caso.get("analistas", [])) <= {"cardapio", "combinacoes", "loja"}
        # As alternativas são comparadas já normalizadas
        for alternativas in caso.get("contem", []):
            assert all(normalizar(a) == a for a in alternativas)
