"""
QAhub - diagnóstico do e-mail temporário
-----------------------------------------
Faz, uma de cada vez e com pausa, as chamadas que o app faz no Mail.tm e mostra
o que o serviço respondeu (código HTTP, cabeçalhos úteis e começo do corpo).
Serve para descobrir por que aparece "muitas consultas" (erro 429).

Rode na pasta do projeto:

    python -m qahub.diagnostico_email              # testa tudo, inclusive criar um endereço
    python -m qahub.diagnostico_email --sem-criar  # só consulta os domínios

O endereço criado no teste é apagado no final.
"""

from __future__ import annotations

import secrets
import sys
import time

import requests

from .emailtemp import BASE_URL, CABECALHOS_UTEIS, TIMEOUT


def diagnosticar(sessao=None, pausa=time.sleep, criar: bool = True, base_url: str = BASE_URL) -> list[str]:
    """Roda os passos e devolve as linhas do relatório."""
    s = sessao or requests.Session()
    linhas = [f"requests {getattr(requests, '__version__', '?')} | alvo: {base_url}"]

    def passo(nome: str, metodo: str, caminho: str, token: str | None = None, json: dict | None = None):
        inicio = time.time()
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            r = s.request(metodo, base_url + caminho, headers=headers, json=json, timeout=TIMEOUT)
        except requests.RequestException as e:
            linhas.append(f"{nome}: SEM RESPOSTA ({type(e).__name__}: {e})")
            return None
        cab = {k: v for k, v in dict(getattr(r, "headers", {}) or {}).items() if k.lower() in CABECALHOS_UTEIS}
        corpo = str(getattr(r, "text", "") or "")[:200].replace("\n", " ")
        linhas.append(f"{nome}: HTTP {r.status_code} em {time.time() - inicio:.1f}s | cabeçalhos: {cab} | corpo: {corpo!r}")
        return r

    r = passo("1. listar domínios", "GET", "/domains")
    if not criar:
        return linhas
    if r is None or r.status_code != 200:
        linhas.append("Parei aqui: nem a lista de domínios veio. O problema está antes de criar o endereço.")
        return linhas
    try:
        dados = r.json()
        itens = dados if isinstance(dados, list) else dados.get("hydra:member", [])
        dominio = next(d["domain"] for d in itens if d.get("isActive", True) and not d.get("isPrivate"))
    except (ValueError, StopIteration, KeyError, AttributeError):
        linhas.append("Parei aqui: a lista de domínios veio, mas sem nenhum domínio utilizável.")
        return linhas

    pausa(2)
    endereco, senha = f"qa{secrets.token_hex(4)}@{dominio}", secrets.token_urlsafe(12)
    r = passo("2. criar endereço", "POST", "/accounts", json={"address": endereco, "password": senha})
    if r is None or r.status_code not in (200, 201):
        linhas.append("Parei aqui: o serviço não deixou criar o endereço.")
        return linhas
    id_conta = (r.json() or {}).get("id")
    pausa(2)
    r = passo("3. entrar no endereço", "POST", "/token", json={"address": endereco, "password": senha})
    token = (r.json() or {}).get("token") if r is not None and r.status_code == 200 else None
    if token and id_conta:
        pausa(1)
        passo("4. apagar o endereço de teste", "DELETE", f"/accounts/{id_conta}", token=token)
    return linhas


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    print("Diagnóstico do Mail.tm (leva uns 10 segundos)...\n")
    for linha in diagnosticar(criar="--sem-criar" not in argv):
        print(linha)
    print("\nCopie tudo o que apareceu acima e me mande.")


if __name__ == "__main__":
    main()
