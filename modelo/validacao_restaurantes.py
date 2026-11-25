"""Validação da busca de restaurantes antes da recomendação (RN-R07)."""

import math

from modelo.restaurantes import PESOS_PADRAO

MAXIMO_CARACTERES_PREFERENCIA = 200


def validar_busca(culinaria, preferencia, pesos, culinarias_da_cidade):
    """Valida e normaliza a busca.

    Retorna {"ok": True, "value": {"culinaria", "preferencia", "pesos"}} ou {"ok": False, "errors": [...]}.
    Não lança exceção, não altera a entrada e não repete nos erros o valor recebido.
    """
    erros = []
    valor = {"culinaria": None, "preferencia": "", "pesos": None}

    # Culinária: opcional; comparada sem diferença de maiúsculas e espaços
    if culinaria is not None:
        oficiais = {nome.strip().lower(): nome for nome in culinarias_da_cidade}
        if not isinstance(culinaria, str):
            erros.append({"field": "culinaria", "code": "invalid_type"})
        elif not culinaria.strip():
            erros.append({"field": "culinaria", "code": "empty"})
        elif culinaria.strip().lower() not in oficiais:
            erros.append({"field": "culinaria", "code": "unknown_cuisine"})
        else:
            valor["culinaria"] = oficiais[culinaria.strip().lower()]

    # Texto livre: opcional
    if preferencia is not None:
        if not isinstance(preferencia, str):
            erros.append({"field": "preferencia", "code": "invalid_type"})
        elif len(preferencia) > MAXIMO_CARACTERES_PREFERENCIA:
            erros.append({"field": "preferencia", "code": "too_long"})
        else:
            valor["preferencia"] = preferencia.strip()

    # Pesos: opcionais; critério não enviado vale 0
    if pesos is not None:
        if not isinstance(pesos, dict):
            erros.append({"field": "pesos", "code": "invalid_type"})
        else:
            validos = {}
            for criterio in PESOS_PADRAO:
                if criterio not in pesos:
                    validos[criterio] = 0.0
                    continue
                peso = pesos[criterio]
                campo = f"pesos.{criterio}"
                # bool é subclasse de int em Python e precisa ser recusado à parte
                if peso is None:
                    erros.append({"field": campo, "code": "null"})
                elif isinstance(peso, bool) or not isinstance(peso, (int, float)):
                    erros.append({"field": campo, "code": "invalid_type"})
                elif not math.isfinite(peso):
                    erros.append({"field": campo, "code": "not_finite"})
                elif peso < 0:
                    erros.append({"field": campo, "code": "out_of_range"})
                else:
                    validos[criterio] = float(peso)

            for chave in sorted((chave for chave in pesos if chave not in PESOS_PADRAO), key=str):
                erros.append({"field": f"pesos.{chave}", "code": "unknown_field"})

            if not erros and len(validos) == len(PESOS_PADRAO):
                if sum(validos.values()) == 0:
                    erros.append({"field": "pesos", "code": "out_of_range"})
                else:
                    valor["pesos"] = validos

    if erros:
        return {"ok": False, "errors": erros}
    return {"ok": True, "value": valor}
