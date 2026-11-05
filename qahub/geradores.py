"""
QAhub - geradores de coluna
----------------------------
Cada coluna da planilha, o dado único avulso e o validador de valores.

Este módulo não depende de Streamlit: pode ser usado e testado sozinho.
"""

from __future__ import annotations

import random
import re
import unicodedata
from datetime import date, timedelta

from . import brasil
from .brasil import (
    BAIRROS, COMPLEMENTOS, ESCOLARIDADES, ESTADOS_BR, PROFISSOES, SIGLAS_BR,
    UF_DA_CIDADE, TIPOS_PIX, NOME_TIPO_PIX, chave_pix, cnh, cnh_valida,
    codigo_barras, codigo_barras_valido, cnpj_valido, cep_da_regiao,
    celular_da_regiao, conta_bancaria, cpf_valido, data_cadastro, digitos,
    fmt_data, int_min_max, luhn_valido, moeda, pis, pis_valido, placa_mercosul,
    escolher, sortear_sem_repetir, embaralhar, sorteia_regiao,
    telefone_da_regiao, titulo_de_eleitor, titulo_valido, uuid,
)

Faker = None


def _fake():
    """Instancia o faker em português uma única vez (preguiçoso)."""
    global Faker
    if Faker is None:
        from faker import Faker as _Faker
        Faker = _Faker("pt_BR")
    return Faker


# ---------------------------------------------------------------------------
# Listas de opções
# ---------------------------------------------------------------------------

BANDEIRAS = ["Visa", "Mastercard", "American Express", "Discover", "Diners Club", "JCB", "Maestro"]

TIPOS_DADO_UNICO = [
    "CPF", "CNPJ", "Cartão de crédito", "RG", "Telefone", "Celular", "CEP", "E-mail",
    "Senha", "PIX", "CNH", "PIS/NIT", "Título de eleitor", "Placa", "Código de barras",
    "UUID", "Valor", "Conta bancária", "Data de cadastro",
]

COLUNAS_DISPONIVEIS = [
    "Nome completo", "Nome social", "Nome do pai", "Nome da mãe", "CPF", "CNPJ",
    "Nome da empresa", "Data de nascimento", "Idade", "Sexo", "Estado civil", "E-mail",
    "Telefone", "Celular", "RG", "PIX", "CNH", "PIS/NIT", "Título de eleitor", "Placa",
    "Banco", "Agência", "Conta", "Endereço", "Complemento", "Bairro", "Cidade",
    "Estado (UF)", "CEP", "Senha", "Cartão de crédito", "Bandeira do cartão",
    "Validade do cartão", "CVV do cartão", "Código de barras", "Valor", "Renda mensal",
    "Escolaridade", "Profissão", "Data de cadastro", "UUID",
]

# Código da UF usado no título de eleitor (tabela do TSE).
CODIGO_TITULO = {
    "SP": 1, "MG": 2, "RJ": 3, "RS": 4, "PR": 5, "DF": 6, "BA": 7, "AL": 8, "PA": 9,
    "PE": 10, "GO": 11, "CE": 12, "ES": 13, "MA": 14, "AM": 15, "PB": 16, "PI": 17,
    "AC": 18, "RN": 19, "MT": 21, "SE": 23, "MS": 24, "SC": 25, "AP": 26, "RO": 27,
    "RR": 28, "TO": 29,
}

DOMINIOS_EMAIL = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com.br", "uol.com.br", "bol.com.br"]

# ---------------------------------------------------------------------------
# Configurações com valor padrão
# ---------------------------------------------------------------------------

NASCIMENTO_PADRAO = {"modo": "idade", "idade_min": 18, "idade_max": 80}
SENHA_PADRAO = {"tamanho": 10, "maiusculas": True, "minusculas": True, "numeros": True, "especiais": True}
VALOR_PADRAO = {"min": 10, "max": 250000}
RENDA_PADRAO = {"min": 1412, "max": 30000}

# ---------------------------------------------------------------------------
# Geradores básicos
# ---------------------------------------------------------------------------


def somente_numeros(valor: str, ativo: bool) -> str:
    return re.sub(r"\D", "", valor) if ativo else valor


def sem_pontuacao(valor: str, ativo: bool) -> str:
    """Tira pontos, traços, parênteses e espaços, mas guarda letras como o X do RG."""
    return re.sub(r"[.\-/\s()]", "", valor) if ativo else valor


REGIAO_FISCAL_CPF = {
    "RS": 0, "DF": 1, "GO": 1, "MT": 1, "MS": 1, "TO": 1,
    "AC": 2, "AM": 2, "AP": 2, "PA": 2, "RO": 2, "RR": 2,
    "CE": 3, "MA": 3, "PI": 3, "AL": 4, "PB": 4, "PE": 4, "RN": 4,
    "BA": 5, "SE": 5, "MG": 6, "ES": 7, "RJ": 7, "SP": 8, "PR": 9, "SC": 9,
}


def cpf(uf: str | None = None) -> str:
    """CPF com os dois dígitos verificadores corretos.

    Com `uf`, o 9º dígito sai na região fiscal da Receita daquele estado.
    """
    d = digitos(9)
    if uf in REGIAO_FISCAL_CPF:
        d[8] = REGIAO_FISCAL_CPF[uf]
    for _ in range(2):
        soma = sum(d[i] * (len(d) + 1 - i) for i in range(len(d)))
        r = (soma * 10) % 11
        d.append(0 if r == 10 else r)
    s = "".join(map(str, d))
    return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"


def cnpj() -> str:
    """CNPJ com os dois dígitos verificadores corretos."""
    d = digitos(8) + [0, 0, 0, 1]
    pesos = [
        [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
        [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
    ]
    for p in pesos:
        r = sum(d[i] * p[i] for i in range(len(p))) % 11
        d.append(0 if r < 2 else 11 - r)
    s = "".join(map(str, d))
    return f"{s[:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:]}"


def rg() -> str:
    s = "".join(map(str, digitos(8)))
    dv = escolher(list("0123456789X"))
    return f"{s[:2]}.{s[2:5]}.{s[5:]}-{dv}"


def telefone() -> str:
    return telefone_da_regiao(sorteia_regiao(None, None))


def celular() -> str:
    return celular_da_regiao(sorteia_regiao(None, None))


def cep(minimo: int | None, maximo: int | None) -> str:
    if minimo is None or maximo is None:
        s = "".join(map(str, digitos(8)))
        return f"{s[:5]}-{s[5:]}"
    return str(int_min_max(minimo, maximo)).zfill(8)


def senha(cfg: dict | None = None) -> str:
    """Senha sorteada com o tamanho e os tipos pedidos."""
    cfg = cfg or SENHA_PADRAO
    grupos: list[str] = []
    if cfg.get("maiusculas", True):
        grupos.append("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if not cfg.get("minusculas", True) and (
        len(grupos)
        + (1 if cfg.get("numeros", True) else 0)
        + (1 if cfg.get("especiais", True) else 0)
    ) == 0:
        grupos.append("abcdefghijklmnopqrstuvwxyz")
    if cfg.get("minusculas", True):
        grupos.append("abcdefghijklmnopqrstuvwxyz")
    if cfg.get("numeros", True):
        grupos.append("0123456789")
    if cfg.get("especiais", True):
        grupos.append("!@#$%^&*()_+-=")
    if not grupos:
        grupos.append("abcdefghijklmnopqrstuvwxyz")
    tam = max(1, int(cfg.get("tamanho", 10)))
    todos = "".join(grupos)
    chars = [escolher(grupo) for grupo in grupos[:tam]]
    while len(chars) < tam:
        chars.append(escolher(todos))
    return "".join(embaralhar(chars))


PREFIXOS = {
    "Visa": {"prefixos": ["4"], "tamanho": 16},
    "Mastercard": {"prefixos": ["51", "52", "53", "54", "55"], "tamanho": 16},
    "American Express": {"prefixos": ["34", "37"], "tamanho": 15},
    "Discover": {"prefixos": ["6011", "65"], "tamanho": 16},
    "Diners Club": {"prefixos": ["300", "301", "302", "303", "304", "305", "36", "38"], "tamanho": 14},
    "JCB": {"prefixos": ["3528", "3589"], "tamanho": 16},
    "Maestro": {"prefixos": ["5018", "5020", "5038", "6304"], "tamanho": 12},
}


def cartao(bandeira: str) -> str:
    """Número de cartão que passa na regra de Luhn."""
    cfg = PREFIXOS.get(bandeira) or PREFIXOS["Visa"]
    base = (escolher(cfg["prefixos"]) + "".join(map(str, digitos(cfg["tamanho"]))))[: cfg["tamanho"] - 1]
    for dv in range(10):
        if luhn_valido(base + str(dv)):
            return base + str(dv)
    return base + "0"


def cvv(bandeira: str) -> str:
    return "".join(map(str, digitos(4 if bandeira == "American Express" else 3)))


def validade() -> str:
    hoje = date.today()
    return f"{int_min_max(1, 12):02d}/{(hoje.year + int_min_max(1, 8)) % 100:02d}"


def calcular_idade(nasc: date, hoje: date | None = None) -> int:
    hoje = hoje or date.today()
    idade = hoje.year - nasc.year
    if (hoje.month, hoje.day) < (nasc.month, nasc.day):
        idade -= 1
    return idade


def _data_com_idade_exata(idade: int, hoje: date) -> date:
    """Data de nascimento que faz a pessoa ter exatamente `idade` anos hoje."""
    try:
        limite = hoje.replace(year=hoje.year - idade)
    except ValueError:  # 29 de fevereiro em ano não bissexto
        limite = date(hoje.year - idade, 3, 1)
    inicio = limite - timedelta(days=364)
    return inicio + timedelta(days=random.randint(0, (limite - inicio).days))


def data_nascimento(cfg: dict) -> date:
    """Data de nascimento respeitando a configuração de idade ou de ano."""
    hoje = date.today()
    if cfg.get("modo") == "ano":
        ini = date(int(cfg["ano_min"]), 1, 1)
        fim = min(date(int(cfg["ano_max"]), 12, 31), hoje)
        if fim < ini:
            fim = ini
        return ini + timedelta(days=random.randint(0, (fim - ini).days))
    idade = int_min_max(int(cfg["idade_min"]), int(cfg["idade_max"]))
    return _data_com_idade_exata(idade, hoje)


def _sem_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def email(dominio: str | None = None, nome: str | None = None) -> str:
    """E-mail derivado do nome, com ponto, underline ou número."""
    base = nome or _fake().name()
    partes = re.sub(r"[^a-z ]", "", _sem_acentos(base).lower()).strip().split()
    partes = [p for p in partes if p] or ["usuario"]
    usuario = f"{partes[0]}{escolher(['.', '_', ''])}{partes[-1]}{escolher(['', str(int_min_max(1, 99))])}"
    return f"{usuario}@{dominio or escolher(DOMINIOS_EMAIL)}"


_TITULOS = {
    "sr.", "sr", "sra.", "sra", "dr.", "dr", "dra.", "dra", "me.", "ms.", "prof.",
    "profª.", "eng.", "cel.", "cap.", "ten.", "padre", "frei", "madame", "mademoiselle",
}


def _limpar_nome(nome: str) -> str:
    """Tira o tratamento que o faker às vezes põe na frente do nome."""
    partes = nome.split(" ")
    while partes and partes[0].lower() in _TITULOS:
        partes.pop(0)
    return " ".join(partes) or nome


def _nome_completo(sexo: str) -> str:
    fake = _fake()
    nome = fake.name_female() if sexo == "Feminino" else fake.name_male()
    return _limpar_nome(nome)


def _primeiro_nome(sexo: str) -> str:
    fake = _fake()
    return fake.first_name_female() if sexo == "Feminino" else fake.first_name_male()


def _nome_empresa() -> str:
    fake = _fake()
    try:
        return fake.company()
    except Exception:
        return f"{_primeiro_nome('Masculino')} & {escolher(['Filhos', 'Irmãos', 'Grupo', 'Holding'])}"


def _endereco() -> str:
    fake = _fake()
    try:
        rua = fake.street_name()
    except Exception:
        rua = f"Rua {escolher(BAIRROS)}"
    try:
        numero = fake.building_number()
    except Exception:
        numero = str(int_min_max(1, 2000))
    return f"{rua}, {numero}"


# ---------------------------------------------------------------------------
# Opções do registro e geração da linha
# ---------------------------------------------------------------------------


def opcoes_padrao() -> dict:
    """Opções de geração sem nenhuma restrição."""
    return {
        "nascimento": dict(NASCIMENTO_PADRAO),
        "senha": dict(SENHA_PADRAO),
        "extras": {},
        "cpf_sem_pontos": False,
        "cnpj_sem_pontos": False,
        "rg_sem_pontos": False,
        "telefone_sem_pontos": False,
        "celular_sem_pontos": False,
        "estados": None,
        "cidades": None,
        "cep_min": None,
        "cep_max": None,
        "sexo_fixo": None,
        "email_dominio": None,
        "escolaridade": None,
        "renda_min": None,
        "renda_max": None,
        "valor_fixo": None,
        "valor_min": None,
        "valor_max": None,
        "pix_tipo": None,
    }


def valor_monetario(o: dict) -> str:
    """Valor monetário: um valor fixo em todas as linhas, ou sorteado na faixa."""
    if o.get("valor_fixo") is not None:
        return moeda(o["valor_fixo"], o["valor_fixo"])
    return moeda(
        o.get("valor_min") if o.get("valor_min") is not None else VALOR_PADRAO["min"],
        o.get("valor_max") if o.get("valor_max") is not None else VALOR_PADRAO["max"],
    )


def gerar_registro(colunas: list[str], o: dict, indice: int) -> dict:
    """Uma linha da planilha, com CEP, cidade, estado e DDD da mesma região."""
    reg = sorteia_regiao(o.get("estados") or None, o.get("cidades") or None)
    nasc = data_nascimento(o.get("nascimento") or NASCIMENTO_PADRAO)
    sexo = o.get("sexo_fixo") or escolher(["Feminino", "Masculino"])
    nome = _nome_completo(sexo)
    partes = nome.split(" ")
    sobrenome = partes[-1] if len(partes) > 1 else "Silva"
    band = escolher(BANDEIRAS)
    cpf_str = cpf(reg.uf)
    cnpj_str = cnpj()
    email_str = email(o.get("email_dominio"), nome)
    cel_str = celular_da_regiao(reg)
    conta = conta_bancaria()
    escolaridade = o.get("escolaridade")
    renda_min = o.get("renda_min") if o.get("renda_min") is not None else RENDA_PADRAO["min"]
    renda_max = o.get("renda_max") if o.get("renda_max") is not None else RENDA_PADRAO["max"]

    geradores = {
        "Nome completo": lambda: nome,
        "Nome social": lambda: nome,
        "Nome do pai": lambda: f"{_primeiro_nome('Masculino')} {sobrenome}",
        "Nome da mãe": lambda: f"{_primeiro_nome('Feminino')} {sobrenome}",
        "CPF": lambda: somente_numeros(cpf_str, o.get("cpf_sem_pontos", False)),
        "CNPJ": lambda: somente_numeros(cnpj_str, o.get("cnpj_sem_pontos", False)),
        "Nome da empresa": _nome_empresa,
        "Data de nascimento": lambda: fmt_data(nasc),
        "Idade": lambda: calcular_idade(nasc),
        "Sexo": lambda: sexo,
        "Estado civil": lambda: escolher(["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"]),
        "E-mail": lambda: email_str,
        "Telefone": lambda: sem_pontuacao(telefone_da_regiao(reg), o.get("telefone_sem_pontos", False)),
        "Celular": lambda: sem_pontuacao(cel_str, o.get("celular_sem_pontos", False)),
        "RG": lambda: sem_pontuacao(rg(), o.get("rg_sem_pontos", False)),
        "PIX": lambda: chave_pix(
            {"cpf": cpf_str, "cnpj": cnpj_str, "email": email_str, "celular": cel_str},
            o.get("pix_tipo"),
        ),
        "CNH": cnh,
        "PIS/NIT": pis,
        "Título de eleitor": lambda: titulo_de_eleitor(CODIGO_TITULO.get(reg.uf)),
        "Placa": placa_mercosul,
        "Banco": lambda: conta["banco"],
        "Agência": lambda: conta["agencia"],
        "Conta": lambda: conta["conta"],
        "Endereço": _endereco,
        "Complemento": lambda: escolher(COMPLEMENTOS),
        "Bairro": lambda: escolher(BAIRROS),
        "Cidade": lambda: reg.cidade,
        "Estado (UF)": lambda: reg.uf,
        "CEP": lambda: cep_da_regiao(reg, o.get("cep_min"), o.get("cep_max")),
        "Senha": lambda: senha(o.get("senha") or SENHA_PADRAO),
        "Cartão de crédito": lambda: cartao(band),
        "Bandeira do cartão": lambda: band,
        "Validade do cartão": validade,
        "CVV do cartão": lambda: cvv(band),
        "Código de barras": codigo_barras,
        "Valor": lambda: valor_monetario(o),
        "Renda mensal": lambda: moeda(renda_min, renda_max),
        "Escolaridade": lambda: escolaridade or escolher(ESCOLARIDADES),
        "Profissão": lambda: escolher(PROFISSOES),
        "Data de cadastro": data_cadastro,
        "UUID": uuid,
    }

    extras = o.get("extras") or {}
    linha = {}
    for c in colunas:
        if c in geradores:
            linha[c] = geradores[c]()
        elif c in extras:
            ex = extras[c]
            valores = ex["valores"]
            linha[c] = valores[indice % len(valores)] if ex.get("sequencial") else escolher(valores)
    return linha


def aplicar_duplicatas(regs: list[dict], qtd: int) -> None:
    """Transforma `qtd` linhas em cópias exatas de linhas anteriores."""
    qtd = min(max(0, qtd), max(0, len(regs) - 1))
    if not qtd:
        return
    for alvo in sortear_sem_repetir(range(1, len(regs)), qtd):
        regs[alvo] = dict(regs[int_min_max(0, alvo - 1)])


def aplicar_sujeira(regs: list[dict], colunas: list[str], s: dict) -> None:
    """Inclui os problemas que costumam quebrar sistema: duplicidade, caixa,
    espaços, campos vazios e linha em branco."""
    if not regs or not colunas:
        return

    def alvos(qtd: int) -> list[int]:
        n = min(max(0, qtd), len(regs) - 1)
        return sortear_sem_repetir(range(1, len(regs)), n) if n else []

    def texto(i: int) -> list[str]:
        return [c for c in colunas if isinstance(regs[i].get(c), str) and str(regs[i][c])]

    if s.get("duplicadas", 0) > 0:
        aplicar_duplicatas(regs, s["duplicadas"])

    if s.get("cpfRepetido", s.get("cpf_repetido", 0)) > 0 and "CPF" in colunas:
        for a in alvos(s.get("cpfRepetido", s.get("cpf_repetido", 0))):
            origem = int_min_max(0, a - 1)
            valor = regs[origem].get("CPF")
            if valor is not None:
                regs[a] = {**regs[a], "CPF": valor}

    if s.get("emailVariacao", s.get("email_variacao", 0)) > 0 and "E-mail" in colunas:
        for a in alvos(s.get("emailVariacao", s.get("email_variacao", 0))):
            e = str(regs[a].get("E-mail") or "")
            if not e:
                continue
            regs[a] = {
                **regs[a],
                "E-mail": escolher([
                    e.upper(),
                    e[0].upper() + e[1:],
                    f"  {e}  ",
                    e.replace("@", " @ "),
                ]),
            }

    if s.get("espacos", 0) > 0:
        for a in alvos(s["espacos"]):
            opcoes = texto(a)
            if not opcoes:
                continue
            c = escolher(opcoes)
            regs[a] = {**regs[a], c: f"  {regs[a][c]} "}

    if s.get("vazios", 0) > 0:
        for a in alvos(s["vazios"]):
            regs[a] = {**regs[a], escolher(colunas): ""}

    for _ in range(max(0, s.get("linhaBranca", s.get("linha_branca", 0)))):
        regs.insert(int_min_max(0, len(regs)), {c: "" for c in colunas})


def validar_coluna_extra(nome: str, texto: str, usados: list[str]) -> dict:
    """Confere o cadastro de uma coluna personalizada."""
    nome = nome.strip()
    if not nome:
        return {"erro": "Dê um nome para a coluna."}
    if len(nome) > 60:
        return {"erro": "O nome pode ter no máximo 60 caracteres."}
    if any(u.lower() == nome.lower() for u in usados):
        return {"erro": "Já existe uma coluna com esse nome."}
    valores = [l.strip() for l in texto.splitlines() if l.strip()]
    if not valores:
        return {"erro": "Informe pelo menos um valor possível (um por linha)."}
    return {"valores": valores}


# ---------------------------------------------------------------------------
# Dado único avulso
# ---------------------------------------------------------------------------


def gerar_dado_unico(tipo: str, o: dict) -> list[list[str]]:
    """Gera um valor avulso; devolve pares [nome do campo, valor]."""
    reg = sorteia_regiao(o.get("estados"), None)
    if tipo == "Cartão de crédito":
        band = o.get("bandeira") or "Visa"
        return [["Número", cartao(band)], ["Validade", validade()], ["CVV", cvv(band)]]
    if tipo == "Senha":
        return [["Senha", senha(o.get("senha") or SENHA_PADRAO)]]
    if tipo == "CPF":
        return [["CPF", somente_numeros(cpf(reg.uf), o.get("sem_pontuacao", False))]]
    if tipo == "CNPJ":
        return [["CNPJ", somente_numeros(cnpj(), o.get("sem_pontuacao", False))]]
    if tipo == "CEP":
        return [["CEP", cep_da_regiao(reg, o.get("cep_min"), o.get("cep_max"))]]
    if tipo == "E-mail":
        return [["E-mail", email(o.get("email_dominio"))]]
    if tipo == "RG":
        return [["RG", sem_pontuacao(rg(), o.get("sem_pontuacao", False))]]
    if tipo == "Telefone":
        return [["Telefone", sem_pontuacao(telefone_da_regiao(reg), o.get("sem_pontuacao", False))]]
    if tipo == "Celular":
        return [["Celular", sem_pontuacao(celular_da_regiao(reg), o.get("sem_pontuacao", False))]]
    if tipo == "PIX":
        c = cpf(reg.uf)
        return [["Chave PIX", chave_pix(
            {"cpf": c, "cnpj": cnpj(), "email": email(o.get("email_dominio")), "celular": celular_da_regiao(reg)},
            o.get("pix_tipo"),
        )]]
    if tipo == "CNH":
        return [["CNH", cnh()]]
    if tipo == "PIS/NIT":
        return [["PIS/NIT", pis()]]
    if tipo == "Título de eleitor":
        return [["Título de eleitor", titulo_de_eleitor()]]
    if tipo == "Placa":
        return [["Placa", placa_mercosul()]]
    if tipo == "Código de barras":
        return [["Código de barras", codigo_barras()]]
    if tipo == "UUID":
        return [["UUID", uuid()]]
    if tipo == "Valor":
        return [["Valor", valor_monetario(o)]]
    if tipo == "Conta bancária":
        c = conta_bancaria()
        return [["Banco", c["banco"]], ["Agência", c["agencia"]], ["Conta", c["conta"]]]
    if tipo == "Data de cadastro":
        return [["Data de cadastro", data_cadastro()]]
    return [["Celular", celular_da_regiao(reg)]]


# ---------------------------------------------------------------------------
# Validador
# ---------------------------------------------------------------------------


def validar_valor(bruto: str) -> dict:
    """Tenta reconhecer o valor e conferir o dígito verificador."""
    v = bruto.strip()
    dig = re.sub(r"\D", "", v)
    if not v:
        return {"valor": bruto, "tipo": "vazio", "valido": False, "motivo": "Nada informado."}
    if re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
        return {"valor": v, "tipo": "E-mail", "valido": True, "motivo": "Formato válido."}
    if re.match(r"^[A-Za-z]{3}\d[A-Za-z]\d{2}$", v):
        return {"valor": v, "tipo": "Placa Mercosul", "valido": True, "motivo": "Formato correto."}
    if re.match(r"^\d{5}-?\d{3}$", v):
        return {"valor": v, "tipo": "CEP", "valido": True, "motivo": "8 dígitos no formato correto."}
    if len(dig) == 44:
        ok = codigo_barras_valido(v)
        return {"valor": v, "tipo": "Código de barras", "valido": ok,
                "motivo": "Dígito verificador confere." if ok else "Dígito verificador não confere."}
    if len(dig) == 14:
        ok = cnpj_valido(v)
        return {"valor": v, "tipo": "CNPJ", "valido": ok,
                "motivo": "Dígitos verificadores conferem." if ok else "Dígitos verificadores não conferem."}
    if len(dig) == 12:
        ok = titulo_valido(v)
        return {"valor": v, "tipo": "Título de eleitor", "valido": ok,
                "motivo": "Dígitos verificadores conferem." if ok else "Dígitos verificadores não conferem."}
    if len(dig) == 11:
        if cpf_valido(v):
            return {"valor": v, "tipo": "CPF", "valido": True, "motivo": "Dígitos verificadores conferem."}
        if cnh_valida(v):
            return {"valor": v, "tipo": "CNH", "valido": True, "motivo": "Dígitos verificadores conferem."}
        if pis_valido(v):
            return {"valor": v, "tipo": "PIS/NIT", "valido": True, "motivo": "Dígito verificador confere."}
        return {"valor": v, "tipo": "CPF", "valido": False,
                "motivo": "Dígitos verificadores não conferem (também não bate com CNH nem PIS)."}
    if 12 <= len(dig) <= 19:
        ok = luhn_valido(v)
        return {"valor": v, "tipo": "Cartão de crédito", "valido": ok,
                "motivo": "Passa na regra de Luhn." if ok else "Não passa na regra de Luhn."}
    return {"valor": v, "tipo": "não reconhecido", "valido": False,
            "motivo": "Não é CPF, CNPJ, cartão, CEP, e-mail, placa, título nem código de barras."}


def parse_cep(v: str) -> int | None:
    d = re.sub(r"\D", "", v or "")
    return int(d) if len(d) == 8 else None


__all__ = [
    "BANDEIRAS", "TIPOS_DADO_UNICO", "COLUNAS_DISPONIVEIS", "CODIGO_TITULO",
    "NASCIMENTO_PADRAO", "SENHA_PADRAO", "VALOR_PADRAO", "RENDA_PADRAO",
    "somente_numeros", "sem_pontuacao", "cpf", "cnpj", "rg", "telefone", "celular", "cep", "senha",
    "cartao", "cvv", "validade", "calcular_idade", "data_nascimento", "email",
    "opcoes_padrao", "valor_monetario", "gerar_registro", "aplicar_duplicatas",
    "aplicar_sujeira", "validar_coluna_extra", "gerar_dado_unico", "validar_valor",
    "parse_cep", "ESCOLARIDADES", "ESTADOS_BR", "SIGLAS_BR", "UF_DA_CIDADE",
    "TIPOS_PIX", "NOME_TIPO_PIX",
]
