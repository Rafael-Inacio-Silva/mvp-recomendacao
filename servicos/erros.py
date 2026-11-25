"""Erros dos serviços; a API converte cada tipo no status HTTP correspondente."""

# Texto de cada código de erro
MENSAGENS = {
    "null": "Campo obrigatório não informado.",
    "invalid_type": "Valor em formato diferente do esperado.",
    "empty": "Campo vazio.",
    "unknown_item": "Item fora do cardápio da loja.",
    "unknown_cuisine": "Culinária não encontrada nesta cidade.",
    "too_long": "Texto com mais de 200 caracteres.",
    "unknown_field": "Campo não previsto.",
    "not_finite": "Número não finito.",
    "out_of_range": "Valor fora da faixa permitida.",
}


def erro(campo, codigo, mensagem=None):
    """Um erro no formato da API: campo, código e texto."""
    return {"field": campo, "code": codigo, "message": mensagem or MENSAGENS[codigo]}


def com_mensagens(erros):
    """Acrescenta o texto aos erros devolvidos pelo validador."""
    return [erro(item["field"], item["code"]) for item in erros]


class ErroDoServico(Exception):
    """Erro com a lista de problemas encontrados."""

    def __init__(self, erros):
        super().__init__(erros)
        self.erros = erros


class EntradaInvalida(ErroDoServico):
    """Dados recebidos com problema."""


class NaoEncontrado(ErroDoServico):
    """Loja que não existe."""


class Indisponivel(ErroDoServico):
    """Loja sem os arquivos gerados ou assistente sem a chave da OpenAI."""
