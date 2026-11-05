"""
QAhub - histórico das gerações
-------------------------------
Guarda as últimas planilhas geradas na sessão para você baixar de novo
sem precisar configurá-las outra vez.
"""

from __future__ import annotations

import json

LINHAS_MAX = 5000
VERSAO_ARQUIVO = 1

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


def exportar(modelos: list, historico: list, banco: dict, cfg: dict, extras: list) -> bytes:
    """Junta tudo o que a pessoa fez num arquivo para ela guardar no computador."""
    itens = []
    for h in historico[:LIMITE]:
        itens.append({**h, "linhas": list(banco.get(h["token"]) or [])[:LINHAS_MAX]})
    dados = {
        "app": "gerador-massa-teste",
        "versao": VERSAO_ARQUIVO,
        "modelos": list(modelos),
        "historico": itens,
        "config": {k: v for k, v in cfg.items() if k != "extras"},
        "extras": list(extras),
    }
    return json.dumps(dados, ensure_ascii=False, default=str).encode("utf-8")


def importar(conteudo: bytes) -> dict:
    """Lê o arquivo baixado antes. Levanta ValueError se não for um arquivo do app."""
    try:
        dados = json.loads(conteudo.decode("utf-8"))
    except Exception as e:
        raise ValueError("Esse arquivo não é um histórico do gerador.") from e
    if not isinstance(dados, dict) or dados.get("app") != "gerador-massa-teste":
        raise ValueError("Esse arquivo não é um histórico do gerador.")
    modelos = [m for m in dados.get("modelos") or [] if isinstance(m, dict) and m.get("nome") and isinstance(m.get("colunas"), list)]
    hist, banco = [], {}
    for i, h in enumerate((dados.get("historico") or [])[:LIMITE], start=1):
        if not isinstance(h, dict) or not isinstance(h.get("colunas"), list):
            continue
        linhas = h.pop("linhas", []) or []
        h["token"] = i
        hist.append(h)
        banco[i] = linhas
    cfg = dados.get("config") if isinstance(dados.get("config"), dict) else {}
    extras = [e for e in dados.get("extras") or [] if isinstance(e, dict) and e.get("nome")]
    return {"modelos": modelos, "historico": hist, "banco": banco, "config": cfg, "extras": extras}


__all__ = ["LIMITE", "LINHAS_MAX", "registrar", "resumo", "exportar", "importar"]
