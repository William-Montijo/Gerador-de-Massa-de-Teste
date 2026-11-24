"""Testes do script de diagnóstico do Mail.tm (sem internet)."""

import requests

from qahub import diagnostico_email as d


class Resp:
    def __init__(self, status, dados=None, headers=None, text=""):
        self.status_code, self._d, self.headers, self.text = status, dados, headers or {}, text

    def json(self):
        return self._d


class Sessao:
    def __init__(self, *respostas):
        self.respostas, self.chamadas = list(respostas), []

    def request(self, metodo, url, **kw):
        self.chamadas.append((metodo, url.replace(d.BASE_URL, "")))
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def rodar(*respostas, **kw):
    s = Sessao(*respostas)
    pausas = []
    return d.diagnosticar(s, pausa=pausas.append, **kw), s, pausas


def test_tudo_certo_roda_os_quatro_passos_e_apaga_o_endereco():
    linhas, s, pausas = rodar(
        Resp(200, [{"domain": "x.com", "isActive": True}]), Resp(201, {"id": "9"}),
        Resp(200, {"token": "t"}), Resp(204))
    assert [c for c in s.chamadas] == [("GET", "/domains"), ("POST", "/accounts"), ("POST", "/token"), ("DELETE", "/accounts/9")]
    assert sum("HTTP" in l for l in linhas) == 4 and pausas == [2, 2, 1]


def test_429_logo_na_lista_de_dominios_mostra_os_detalhes_e_para():
    linhas, s, _ = rodar(Resp(429, {}, headers={"Retry-After": "30", "X-Lixo": "1"}, text="slow"))
    texto = "\n".join(linhas)
    assert "HTTP 429" in texto and "Retry-After" in texto and "'slow'" in texto and "X-Lixo" not in texto
    assert "Parei aqui" in texto and len(s.chamadas) == 1


def test_sem_criar_so_consulta_os_dominios():
    linhas, s, _ = rodar(Resp(200, []), criar=False)
    assert s.chamadas == [("GET", "/domains")]


def test_sem_internet():
    linhas, _, _ = rodar(requests.ConnectionError("sem rede"))
    assert any("SEM RESPOSTA" in l for l in linhas)
