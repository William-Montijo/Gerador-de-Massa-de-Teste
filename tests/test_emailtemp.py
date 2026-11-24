"""Testes do e-mail temporário, com uma sessão HTTP de mentira (sem internet)."""

import pytest
import requests

from qahub import emailtemp as e


class Resp:
    def __init__(self, status=200, dados=None, headers=None, text=""):
        self.status_code = status
        self._dados = dados
        self.content = b"" if dados is None else b"x"
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._dados


class Sessao:
    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def request(self, metodo, url, **kw):
        self.chamadas.append((metodo, url, kw))
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def cliente(*respostas, tentativas=3):
    s = Sessao(*respostas)
    c = e.ClienteMailTm(s, pausa=c_pausas.append, tentativas=tentativas)
    return c, s


c_pausas: list = []  # pausas pedidas ao cliente (os testes não esperam de verdade)


# --- nome do usuário -------------------------------------------------------

def test_normalizar_usuario():
    assert e.normalizar_usuario("") is None and e.normalizar_usuario(None) is None
    assert e.normalizar_usuario("  João Teste ") == "joao.teste"
    assert e.normalizar_usuario("QA_loja-01") == "qa_loja-01"
    for ruim in ["ab", "a" * 31, "ola@mundo", "ç$%"]:
        with pytest.raises(ValueError):
            e.normalizar_usuario(ruim)
    assert e.normalizar_usuario(e.gerar_usuario())  # o sorteado sempre serve


# --- domínios e conta ------------------------------------------------------

def test_dominios_filtra_inativos_e_privados():
    c, _ = cliente(Resp(200, {"hydra:member": [
        {"domain": "a.com", "isActive": True, "isPrivate": False},
        {"domain": "b.com", "isActive": False, "isPrivate": False},
        {"domain": "c.com", "isActive": True, "isPrivate": True},
    ]}))
    assert c.dominios() == ["a.com"]


def test_dominios_aceita_lista_simples():
    c, _ = cliente(Resp(200, [{"domain": "x.com", "isActive": True, "isPrivate": False}]))
    assert c.dominios() == ["x.com"]


def test_criar_conta_usa_o_mesmo_endereco_e_senha():
    c, s = cliente(Resp(201, {"id": "abc"}), Resp(200, {"id": "abc", "token": "tok"}))
    conta = c.criar_conta("Meu Teste", "x.com")
    assert conta["address"] == "meu.teste@x.com" and conta["token"] == "tok" and conta["id"] == "abc"
    (m1, u1, k1), (m2, u2, k2) = s.chamadas
    assert (m1, u1.endswith("/accounts"), m2, u2.endswith("/token")) == ("POST", True, "POST", True)
    assert k1["json"] == k2["json"] == {"address": "meu.teste@x.com", "password": conta["password"]}
    assert len(conta["password"]) >= 12


def test_criar_conta_sem_dominio_busca_o_primeiro():
    c, s = cliente(Resp(200, [{"domain": "um.com"}, {"domain": "dois.com"}]), Resp(201, {"id": "1"}), Resp(200, {"token": "t"}))
    assert c.criar_conta().get("address").endswith("@um.com")
    assert s.chamadas[0][1].endswith("/domains")


def test_criar_conta_nome_repetido():
    c, _ = cliente(Resp(422, {}))
    with pytest.raises(e.ErroEmail, match="já em uso|em uso") as exc:
        c.criar_conta("abc", "x.com")
    assert exc.value.status == 422


def test_sem_dominio_disponivel():
    c, _ = cliente(Resp(200, []))
    with pytest.raises(e.ErroEmail, match="domínio"):
        c.criar_conta()


# --- erros -----------------------------------------------------------------

def test_erros_viram_mensagens_em_portugues():
    c, _ = cliente(Resp(404, {}), Resp(500, {}))
    with pytest.raises(e.ErroEmail, match="Não encontrado") as exc:
        c.dominios()
    assert exc.value.status == 404
    with pytest.raises(e.ErroEmail, match="500"):
        c.dominios()


def test_429_tenta_de_novo_e_funciona():
    c_pausas.clear()
    c, s = cliente(Resp(429, {}), Resp(429, {}), Resp(200, [{"domain": "ok.com"}]))
    assert c.dominios() == ["ok.com"]
    assert len(s.chamadas) == 3 and len(c_pausas) == 2 and all(0 < p <= 5 for p in c_pausas)


def test_429_persistente_explica_e_guarda_detalhes():
    c_pausas.clear()
    r = Resp(429, {}, headers={"Retry-After": "60", "Server": "cloudflare", "X-Outro": "n"}, text='{"msg":"slow down"}')
    c, s = cliente(r, r, r)
    with pytest.raises(e.ErroEmail) as exc:
        c.dominios()
    err = exc.value
    assert len(s.chamadas) == 3                       # tentou 3 vezes e desistiu
    assert err.status == 429 and err.espera == 60
    assert "60 segundo" in str(err)                   # mostra o que o serviço pediu
    assert "GET /domains -> HTTP 429" in err.detalhe and "Retry-After" in err.detalhe
    assert "slow down" in err.detalhe and "X-Outro" not in err.detalhe
    assert max(c_pausas) <= 5                         # nunca trava a tela esperando 60 s


def test_429_sem_retry_after_sugere_trocar_de_rede():
    c, _ = cliente(Resp(429, {}), tentativas=1)
    with pytest.raises(e.ErroEmail, match="VPN"):
        c.dominios()


def test_so_repete_no_429():
    c, s = cliente(Resp(500, {}), Resp(200, []))
    with pytest.raises(e.ErroEmail):
        c.dominios()
    assert len(s.chamadas) == 1


def test_pausa_entre_criar_conta_e_entrar():
    c_pausas.clear()
    c, _ = cliente(Resp(201, {"id": "1"}), Resp(200, {"token": "t"}))
    c.criar_conta("abc", "x.com")
    assert c_pausas == [0.6]


def test_sem_internet():
    c, _ = cliente(requests.ConnectionError("sem rede"))
    with pytest.raises(e.ErroEmail, match="internet"):
        c.dominios()


# --- mensagens -------------------------------------------------------------

CONTA = {"id": "acc", "address": "a@x.com", "password": "senha", "token": "velho"}

MSG = {
    "id": "m1", "from": {"name": "Loja", "address": "no-reply@loja.com"}, "to": [{"address": "a@x.com"}],
    "subject": "Confirme seu e-mail", "intro": "Seu código é 482913", "seen": False,
    "hasAttachments": False, "createdAt": "2026-11-23T14:05:00.000Z",
}


def test_listar_normaliza():
    c, s = cliente(Resp(200, {"hydra:member": [MSG]}))
    (m,) = c.listar(dict(CONTA))
    assert m["id"] == "m1" and m["de"] == "Loja <no-reply@loja.com>" and m["visto"] is False
    assert m["assunto"] == "Confirme seu e-mail" and m["quando"] == "23/11 11:05"
    assert s.chamadas[0][2]["headers"]["Authorization"] == "Bearer velho"


def test_token_vencido_entra_de_novo_e_repete():
    conta = dict(CONTA)
    c, s = cliente(Resp(401, {}), Resp(200, {"token": "novo"}), Resp(200, {"hydra:member": []}))
    assert c.listar(conta) == []
    assert conta["token"] == "novo"
    assert [x[0] for x in s.chamadas] == ["GET", "POST", "GET"]
    assert s.chamadas[2][2]["headers"]["Authorization"] == "Bearer novo"


def test_dois_401_seguidos_dao_erro():
    c, _ = cliente(Resp(401, {}), Resp(200, {"token": "n"}), Resp(401, {}))
    with pytest.raises(e.ErroEmail):
        c.listar(dict(CONTA))


def test_mensagem_completa_com_html_so():
    bruto = {**MSG, "text": "", "html": ["<html><head><style>x{}</style></head><body><p>Olá!</p>"
             "<p>Seu código de verificação: <b>731904</b></p>"
             "<a href='https://loja.com/confirmar?t=abc'>Confirmar</a></body></html>"],
             "attachments": [{"filename": "nota.pdf", "contentType": "application/pdf", "size": 2048}]}
    c, _ = cliente(Resp(200, bruto))
    m = c.mensagem(dict(CONTA), "m1")
    assert "Olá!" in m["texto"] and "731904" in m["texto"] and "x{}" not in m["texto"]
    assert m["codigos"][0] == "731904"
    assert m["links"] == ["https://loja.com/confirmar?t=abc"]
    assert m["anexos"] == [{"nome": "nota.pdf", "tipo": "application/pdf", "tamanho": 2048}]
    assert m["para"] == "a@x.com"


def test_marcar_lida_apagar_e_excluir_conta():
    c, s = cliente(Resp(200, {"seen": True}), Resp(204), Resp(204))
    c.marcar_lida(dict(CONTA), "m1")
    c.excluir_mensagem(dict(CONTA), "m1")
    c.excluir_conta(dict(CONTA))
    assert [(m, u.rsplit("/", 2)[-2:]) for m, u, _ in s.chamadas] == [
        ("PATCH", ["messages", "m1"]), ("DELETE", ["messages", "m1"]), ("DELETE", ["accounts", "acc"])]
    assert s.chamadas[0][2]["headers"]["Content-Type"] == "application/merge-patch+json"


# --- códigos e links -------------------------------------------------------

def test_codigos():
    assert e.extrair_codigos("Seu código é 482913. Válido por 10 minutos.") == ["482913"]
    assert e.extrair_codigos("Em 2026 lançamos. Código: 1234") == ["1234"]  # ano ignorado, código perto da palavra
    assert e.extrair_codigos("Use 123 456 para entrar") == ["123456"]
    assert e.extrair_codigos("Pedido 99887766 e código 5521") == ["5521", "99887766"]  # os perto da palavra vêm antes
    assert e.extrair_codigos("Acesse https://x.com/c/123456 agora") == []
    assert e.extrair_codigos("sem números") == []
    assert e.extrair_codigos("Código 1111 e de novo código 1111") == ["1111"]


def test_links():
    texto = "Clique: https://loja.com/ok?a=1&b=2. Ou http://x.com/y), obrigado"
    assert e.extrair_links(texto) == ["https://loja.com/ok?a=1&b=2", "http://x.com/y"]
    html = '<a href="https://a.com/1">1</a><a href="mailto:x@y.com">m</a><a href="https://a.com/1">1</a>'
    assert e.extrair_links("", html) == ["https://a.com/1"]


def test_html_para_texto_e_quebrado():
    assert e.html_para_texto("<p>Oi</p><p>Tchau</p>") == "Oi\n\nTchau" or e.html_para_texto("<p>Oi</p><p>Tchau</p>").split() == ["Oi", "Tchau"]
    assert "Oi" in e.html_para_texto("<p>Oi <b>mundo")  # HTML sem fechar
    assert e.html_para_texto("<script>alert(1)</script>texto") == "texto"
