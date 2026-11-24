"""
QAhub - e-mail temporário
--------------------------
Cria endereços descartáveis e lê as mensagens que chegam neles, para você
testar cadastro, confirmação de e-mail, recuperação de senha e códigos de
verificação sem encher a sua caixa pessoal.

Usa a API gratuita do Mail.tm (https://mail.tm), documentada em
https://docs.mail.tm. Limite do serviço: 8 consultas por segundo por IP.

Este módulo não depende de Streamlit. O cliente aceita uma sessão HTTP
"de mentira" para os testes não precisarem da internet.
"""

from __future__ import annotations

import re
import secrets
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

import requests

BASE_URL = "https://api.mail.tm"
SITE = "https://mail.tm"
TIMEOUT = 15


class ErroEmail(Exception):
    """Erro já em português, pronto para mostrar na tela."""

    def __init__(self, mensagem: str, status: int | None = None, detalhe: str = "",
                 espera: int | None = None):
        super().__init__(mensagem)
        self.status = status
        self.detalhe = detalhe  # texto técnico (o que o serviço respondeu), para diagnóstico
        self.espera = espera    # segundos que o serviço pediu para esperar (Retry-After)


# ---------------------------------------------------------------------------
# Texto: nome do usuário, HTML, links e códigos
# ---------------------------------------------------------------------------


def _sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def normalizar_usuario(texto: str | None) -> str | None:
    """Parte antes do @. Vazio = sorteia. Levanta ValueError se não servir."""
    t = _sem_acentos((texto or "").strip().lower())
    if not t:
        return None
    t = re.sub(r"\s+", ".", t)
    if not re.fullmatch(r"[a-z0-9._-]{3,30}", t):
        raise ValueError("Use de 3 a 30 letras, números, ponto, traço ou underline no nome.")
    return t


def gerar_usuario() -> str:
    return "qa" + secrets.token_hex(4)


class _LeitorHtml(HTMLParser):
    """Tira o texto e os links (href) de um HTML."""

    _BLOCOS = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "table", "ul", "ol", "hr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self.links: list[str] = []
        self._ignorar = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head"):
            self._ignorar += 1
        if tag in self._BLOCOS:
            self.partes.append("\n")
        if tag == "a":
            for nome, valor in attrs:
                if nome == "href" and valor:
                    self.links.append(valor.strip())

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head") and self._ignorar:
            self._ignorar -= 1
        if tag in self._BLOCOS:
            self.partes.append("\n")

    def handle_data(self, data):
        if not self._ignorar:
            self.partes.append(data)


def _ler_html(html: str) -> tuple[str, list[str]]:
    leitor = _LeitorHtml()
    try:
        leitor.feed(html or "")
        leitor.close()
    except Exception:  # HTML quebrado: usa o que deu para ler
        pass
    texto = re.sub(r"[ \t\r\f\v]+", " ", "".join(leitor.partes))
    texto = re.sub(r" ?\n ?", "\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto).strip()
    return texto, leitor.links


def html_para_texto(html: str) -> str:
    return _ler_html(html)[0]


_URL = re.compile(r"https?://[^\s<>\"'\\)\]]+", re.I)


def extrair_links(texto: str, html: str = "") -> list[str]:
    """Links http(s) do texto e do HTML, sem repetir, na ordem em que aparecem."""
    achados = [m.group(0).rstrip(".,;:!?") for m in _URL.finditer(texto or "")]
    achados += _ler_html(html)[1] if html else []
    vistos, saida = set(), []
    for link in achados:
        if link.lower().startswith(("http://", "https://")) and link not in vistos:
            vistos.add(link)
            saida.append(link)
    return saida


_PALAVRAS_CODIGO = re.compile(
    r"(c[óo]digo|code|verifica|confirma|senha|token|pin|otp|acesso)", re.I)


def extrair_codigos(texto: str) -> list[str]:
    """Possíveis códigos de verificação (4 a 8 dígitos). Os que vêm perto de
    'código', 'verificação' etc. aparecem primeiro."""
    limpo = _URL.sub(" ", texto or "")
    perto, resto = [], []
    for m in re.finditer(r"(?<![\w.,-])(\d{3}[ -]\d{3}|\d{4,8})(?![\w])", limpo):
        codigo = re.sub(r"\D", "", m.group(1))
        antes = limpo[max(0, m.start() - 40): m.start()]
        proximo = bool(_PALAVRAS_CODIGO.search(antes))
        if len(codigo) == 4 and 1990 <= int(codigo) <= 2100 and not proximo:
            continue  # parece ano
        (perto if proximo else resto).append(codigo)
    vistos, saida = set(), []
    for c in perto + resto:
        if c not in vistos:
            vistos.add(c)
            saida.append(c)
    return saida


# ---------------------------------------------------------------------------
# Normalização das respostas da API
# ---------------------------------------------------------------------------


def _quando(iso: str | None) -> str:
    """'2026-11-23T14:05:00.000Z' -> '23/11 11:05' (horário de Brasília)."""
    if not iso:
        return ""
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso
    try:
        from zoneinfo import ZoneInfo
        d = d.astimezone(ZoneInfo("America/Sao_Paulo"))
    except Exception:
        d = d.astimezone(timezone(timedelta(hours=-3)))
    return d.strftime("%d/%m %H:%M")


def _pessoa(p) -> str:
    p = p or {}
    nome, end = (p.get("name") or "").strip(), (p.get("address") or "").strip()
    return f"{nome} <{end}>" if nome and end else (end or nome)


def _membros(dados) -> list:
    """A API devolve uma lista simples ou um objeto com 'hydra:member'."""
    if isinstance(dados, list):
        return dados
    if isinstance(dados, dict):
        return dados.get("hydra:member") or dados.get("member") or []
    return []


def normalizar_resumo(m: dict) -> dict:
    return {
        "id": m.get("id", ""),
        "de": _pessoa(m.get("from")),
        "assunto": (m.get("subject") or "").strip() or "(sem assunto)",
        "resumo": (m.get("intro") or "").strip(),
        "visto": bool(m.get("seen")),
        "quando": _quando(m.get("createdAt")),
        "anexos": bool(m.get("hasAttachments")),
    }


def normalizar_mensagem(m: dict) -> dict:
    html_bruto = m.get("html") or ""
    html = "\n".join(html_bruto) if isinstance(html_bruto, list) else str(html_bruto)
    texto = (m.get("text") or "").strip() or html_para_texto(html)
    return {
        "id": m.get("id", ""),
        "de": _pessoa(m.get("from")),
        "para": ", ".join(_pessoa(p) for p in (m.get("to") or [])),
        "assunto": (m.get("subject") or "").strip() or "(sem assunto)",
        "quando": _quando(m.get("createdAt")),
        "texto": texto,
        "html": html,
        "anexos": [{"nome": a.get("filename") or "anexo", "tipo": a.get("contentType") or "",
                    "tamanho": int(a.get("size") or 0)} for a in (m.get("attachments") or [])],
        "codigos": extrair_codigos(texto),
        "links": extrair_links(texto, html),
    }


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------

_ERROS = {
    401: "O acesso a esse e-mail expirou.",
    404: "Não encontrado. Talvez já tenha sido apagado.",
    422: "O serviço não aceitou os dados enviados.",
    429: "O serviço recusou por excesso de consultas (erro 429). Isso costuma acontecer quando outros programas "
         "ou pessoas usam o Mail.tm na mesma rede ou VPN, ou depois de várias tentativas seguidas.",
}

CABECALHOS_UTEIS = ("retry-after", "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset",
                    "server", "cf-ray", "content-type", "via")


def _cabecalhos(r) -> dict:
    cab = getattr(r, "headers", None) or {}
    return {k: v for k, v in dict(cab).items() if k.lower() in CABECALHOS_UTEIS}


def _espera_pedida(r) -> int | None:
    """Segundos do cabeçalho Retry-After, se vier e for um número."""
    for k, v in (getattr(r, "headers", None) or {}).items():
        if k.lower() == "retry-after":
            try:
                return max(0, int(float(v)))
            except (TypeError, ValueError):
                return None
    return None


def _detalhe(metodo: str, caminho: str, r) -> str:
    corpo = str(getattr(r, "text", "") or "")[:200].replace("\n", " ")
    return f"{metodo} {caminho} -> HTTP {r.status_code} | cabeçalhos: {_cabecalhos(r)} | corpo: {corpo!r}"


class ClienteMailTm:
    def __init__(self, sessao=None, base_url: str = BASE_URL, pausa=time.sleep, tentativas: int = 3):
        self.sessao = sessao or requests.Session()
        self.base_url = base_url.rstrip("/")
        self.pausa = pausa            # nos testes vira uma função que não espera
        self.tentativas = max(1, tentativas)

    def _chamar(self, metodo: str, caminho: str, token: str | None = None, json: dict | None = None,
                tipo: str | None = None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        if tipo:
            headers["Content-Type"] = tipo
        for tentativa in range(self.tentativas):
            try:
                r = self.sessao.request(metodo, self.base_url + caminho, headers=headers, json=json, timeout=TIMEOUT)
            except requests.RequestException as e:
                raise ErroEmail("Não consegui falar com o serviço de e-mail temporário. "
                                "Confira a internet e tente de novo.", detalhe=f"{type(e).__name__}: {e}") from e
            if r.status_code != 429 or tentativa == self.tentativas - 1:
                break
            # 429 = o pedido nem foi processado, então repetir é seguro. Espera um pouco e tenta de novo.
            self.pausa(min(_espera_pedida(r) or 1.5 * (tentativa + 1), 5))
        if r.status_code in (200, 201, 204):
            if r.status_code == 204 or not getattr(r, "content", b""):
                return {}
            try:
                return r.json()
            except ValueError as e:
                raise ErroEmail("O serviço respondeu algo que não entendi.", r.status_code,
                                _detalhe(metodo, caminho, r)) from e
        espera = _espera_pedida(r) if r.status_code == 429 else None
        msg = _ERROS.get(r.status_code, f"O serviço respondeu com erro {r.status_code}.")
        if espera:
            msg += f" O serviço pediu para esperar cerca de {espera} segundo(s)."
        elif r.status_code == 429:
            msg += " Espere um minuto e tente de novo; se continuar, troque de rede ou desligue a VPN."
        raise ErroEmail(msg, r.status_code, _detalhe(metodo, caminho, r), espera)

    # -- endereços ---------------------------------------------------------

    def dominios(self) -> list[str]:
        """Domínios ativos e públicos que dá para usar."""
        itens = _membros(self._chamar("GET", "/domains"))
        return [d["domain"] for d in itens if d.get("domain") and d.get("isActive", True) and not d.get("isPrivate")]

    def criar_conta(self, usuario: str | None = None, dominio: str | None = None) -> dict:
        """Cria o endereço e já entra nele. Devolve o que o app precisa guardar."""
        dominio = dominio or next(iter(self.dominios()), None)
        if not dominio:
            raise ErroEmail("O serviço não tem nenhum domínio disponível agora. Tente mais tarde.")
        endereco = f"{normalizar_usuario(usuario) or gerar_usuario()}@{dominio}"
        senha = secrets.token_urlsafe(12)
        try:
            conta = self._chamar("POST", "/accounts", json={"address": endereco, "password": senha})
        except ErroEmail as e:
            if e.status == 422:
                raise ErroEmail("Não deu para criar esse endereço. O nome pode já estar em uso: tente outro.", 422) from e
            raise
        self.pausa(0.6)  # espaça as duas chamadas, o serviço é sensível a rajadas
        tok = self._chamar("POST", "/token", json={"address": endereco, "password": senha})
        return {
            "id": conta.get("id") or tok.get("id"),
            "address": endereco,
            "password": senha,
            "token": tok.get("token", ""),
            "criado": datetime.now().strftime("%d/%m %H:%M"),
        }

    def renovar_token(self, conta: dict) -> None:
        tok = self._chamar("POST", "/token", json={"address": conta["address"], "password": conta["password"]})
        conta["token"] = tok.get("token", "")

    def _autenticado(self, conta: dict, metodo: str, caminho: str, tipo: str | None = None):
        """Chamada com o token da conta; se o token venceu, entra de novo e repete uma vez."""
        try:
            return self._chamar(metodo, caminho, conta.get("token"), tipo=tipo)
        except ErroEmail as e:
            if e.status != 401:
                raise
            self.renovar_token(conta)
            return self._chamar(metodo, caminho, conta.get("token"), tipo=tipo)

    def excluir_conta(self, conta: dict) -> None:
        if conta.get("id"):
            self._autenticado(conta, "DELETE", f"/accounts/{conta['id']}")

    # -- mensagens ---------------------------------------------------------

    def listar(self, conta: dict, pagina: int = 1) -> list[dict]:
        dados = self._autenticado(conta, "GET", f"/messages?page={int(pagina)}")
        return [normalizar_resumo(m) for m in _membros(dados)]

    def mensagem(self, conta: dict, id_mensagem: str) -> dict:
        return normalizar_mensagem(self._autenticado(conta, "GET", f"/messages/{id_mensagem}"))

    def marcar_lida(self, conta: dict, id_mensagem: str) -> None:
        self._autenticado(conta, "PATCH", f"/messages/{id_mensagem}", tipo="application/merge-patch+json")

    def excluir_mensagem(self, conta: dict, id_mensagem: str) -> None:
        self._autenticado(conta, "DELETE", f"/messages/{id_mensagem}")


__all__ = [
    "BASE_URL", "SITE", "ErroEmail", "ClienteMailTm", "normalizar_usuario", "gerar_usuario",
    "html_para_texto", "extrair_links", "extrair_codigos", "normalizar_resumo", "normalizar_mensagem",
]
