"""
QAhub - histórico das gerações
-------------------------------
Guarda as últimas planilhas geradas na sessão para você baixar de novo
sem precisar configurá-las outra vez.
"""

from __future__ import annotations

LIMITE = 8


def registrar(historico: list[dict], entrada: dict, limite: int = LIMITE) -> list[dict]:
    """Coloca a geração mais recente no começo e corta o que passar do limite."""
    nova = [entrada] + [h for h in historico if h is not entrada]
    return nova[: max(0, limite)]


def resumo(entrada: dict) -> str:
    """Frase curta descrevendo a geração guardada."""
    colunas = entrada.get("colunas") or []
    mostradas = ", ".join(colunas[:3])
    if len(colunas) > 3:
        mostradas += f" +{len(colunas) - 3}"
    return f"{entrada.get('quantidade', 0)} linhas · {mostradas or 'sem colunas'}"


__all__ = ["LIMITE", "registrar", "resumo"]
