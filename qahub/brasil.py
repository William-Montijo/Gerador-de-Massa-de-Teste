"""
QAhub - dados do Brasil e dígitos verificadores
-------------------------------------------------
Tudo que amarra CEP, cidade, estado e DDD na mesma região, além das
regras de dígito verificador de CPF, CNPJ, CNH, PIS, título de eleitor,
código de barras e cartão de crédito.

Este módulo não depende de Streamlit: pode ser usado e testado sozinho.
"""

from __future__ import annotations

import random
import uuid as _uuid
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Utilidades de sorteio
# ---------------------------------------------------------------------------


def int_min_max(minimo: int, maximo: int) -> int:
    """Inteiro sorteado entre minimo e maximo, inclusive."""
    return random.randint(minimo, maximo)


def digitos(quantidade: int) -> list[int]:
    """Lista de algarismos sorteados (0 a 9)."""
    return [random.randint(0, 9) for _ in range(quantidade)]


def escolher(opcoes):
    """Sorteia um item da lista."""
    return random.choice(list(opcoes))


def sortear_sem_repetir(populacao, quantidade: int):
    """Sorteia `quantidade` itens diferentes da população."""
    quantidade = max(0, min(quantidade, len(populacao)))
    return random.sample(list(populacao), quantidade)


def embaralhar(itens):
    """Embaralha a lista (não altera a original)."""
    copia = list(itens)
    random.shuffle(copia)
    return copia


# ---------------------------------------------------------------------------
# Estados, faixas de CEP, DDDs e cidades
# ---------------------------------------------------------------------------

ESTADOS_BR: list[tuple[str, str]] = [
    ("AC", "Acre"), ("AL", "Alagoas"), ("AP", "Amapá"), ("AM", "Amazonas"),
    ("BA", "Bahia"), ("CE", "Ceará"), ("DF", "Distrito Federal"),
    ("ES", "Espírito Santo"), ("GO", "Goiás"), ("MA", "Maranhão"),
    ("MT", "Mato Grosso"), ("MS", "Mato Grosso do Sul"), ("MG", "Minas Gerais"),
    ("PA", "Pará"), ("PB", "Paraíba"), ("PR", "Paraná"), ("PE", "Pernambuco"),
    ("PI", "Piauí"), ("RJ", "Rio de Janeiro"), ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"), ("RO", "Rondônia"), ("RR", "Roraima"),
    ("SC", "Santa Catarina"), ("SP", "São Paulo"), ("SE", "Sergipe"),
    ("TO", "Tocantins"),
]
SIGLAS_BR = [sigla for sigla, _ in ESTADOS_BR]

# Faixas de CEP oficiais por estado (AM é dividida para não invadir RR e AC).
CEP_POR_UF: dict[str, list[tuple[int, int]]] = {
    "AC": [(69900000, 69999999)],
    "AL": [(57000000, 57999999)],
    "AP": [(68900000, 68999999)],
    "AM": [(69000000, 69299999), (69400000, 69899999)],
    "BA": [(40000000, 48999999)],
    "CE": [(60000000, 63999999)],
    "DF": [(70000000, 72999999)],
    "ES": [(29000000, 29999999)],
    "GO": [(73000000, 76799999)],
    "MA": [(65000000, 65999999)],
    "MG": [(30000000, 39999999)],
    "MS": [(79000000, 79999999)],
    "MT": [(78000000, 78999999)],
    "PA": [(66000000, 68899999)],
    "PB": [(58000000, 58999999)],
    "PE": [(50000000, 56999999)],
    "PI": [(64000000, 64999999)],
    "PR": [(80000000, 87999999)],
    "RJ": [(20000000, 28999999)],
    "RN": [(59000000, 59999999)],
    "RO": [(76800000, 76999999)],
    "RR": [(69300000, 69399999)],
    "RS": [(90000000, 99999999)],
    "SC": [(88000000, 89999999)],
    "SE": [(49000000, 49999999)],
    "SP": [(1000000, 19999999)],
    "TO": [(77000000, 77999999)],
}

DDDS_POR_UF: dict[str, list[int]] = {
    "AC": [68], "AL": [82], "AP": [96], "AM": [92, 97],
    "BA": [71, 73, 74, 75, 77], "CE": [85, 88], "DF": [61],
    "ES": [27, 28], "GO": [62, 64], "MA": [98, 99], "MT": [65, 66], "MS": [67],
    "MG": [31, 32, 33, 34, 35, 37, 38], "PA": [91, 93, 94], "PB": [83],
    "PR": [41, 42, 43, 44, 45, 46], "PE": [81, 87], "PI": [86, 89],
    "RJ": [21, 22, 24], "RN": [84], "RS": [51, 53, 54, 55], "RO": [69],
    "RR": [95], "SC": [47, 48, 49],
    "SP": [11, 12, 13, 14, 15, 16, 17, 18, 19], "SE": [79], "TO": [63],
}

CIDADES_POR_UF: dict[str, list[str]] = {
    "AC": ["Rio Branco", "Cruzeiro do Sul", "Sena Madureira", "Tarauacá", "Feijó",
           "Brasiléia", "Xapuri", "Epitaciolândia", "Plácido de Castro", "Senador Guiomard"],
    "AL": ["Maceió", "Arapiraca", "Palmares", "Rio Largo", "Penedo", "Piranhas",
           "São Miguel dos Campos", "União dos Palmares", "Santana do Ipanema", "Delmiro Gouveia"],
    "AP": ["Macapá", "Santana", "Laranjal do Jari", "Oiapoque", "Porto Grande",
           "Tartarugalzinho", "Amapá", "Calçoene"],
    "AM": ["Manaus", "Parintins", "Itacoatiara", "Manacapuru", "Coari", "Tefé",
           "Tabatinga", "Iranduba", "Maués", "Manicoré"],
    "BA": ["Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari", "Itabuna",
           "Juazeiro", "Lauro de Freitas", "Ilhéus", "Barreiras", "Porto Seguro",
           "Teixeira de Freitas", "Alagoinhas"],
    "CE": ["Fortaleza", "Caucaia", "Juazeiro do Norte", "Maracanaú", "Sobral", "Crato",
           "Iguatu", "Quixadá", "Aquiraz", "Eusébio"],
    "DF": ["Brasília", "Taguatinga", "Ceilândia", "Sobradinho", "Planaltina", "Gama",
           "Guará", "Núcleo Bandeirante", "Samambaia", "Brazlândia"],
    "ES": ["Vitória", "Vila Velha", "Serra", "Cachoeiro de Itapemirim", "Cariacica",
           "Linhares", "São Mateus", "Colatina", "Aracruz", "Guarapari"],
    "GO": ["Goiânia", "Aparecida de Goiânia", "Anápolis", "Rio Verde", "Luziânia",
           "Águas Lindas de Goiás", "Valparaíso de Goiás", "Trindade", "Formosa",
           "Itumbiara", "Caldas Novas"],
    "MA": ["São Luís", "Imperatriz", "Timon", "Caxias", "Codó", "Paço do Lumiar",
           "Açailândia", "Bacabal", "Santa Inês", "Balsas"],
    "MT": ["Cuiabá", "Várzea Grande", "Rondonópolis", "Sinop", "Tangará da Serra",
           "Sorriso", "Cáceres", "Barra do Garças", "Lucas do Rio Verde", "Primavera do Leste"],
    "MS": ["Campo Grande", "Dourados", "Três Lagoas", "Corumbá", "Ponta Porã", "Naviraí",
           "Aquidauana", "Coxim", "Nova Andradina", "Maracaju"],
    "MG": ["Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim",
           "Montes Claros", "Uberaba", "Araguari", "Ipatinga", "Sete Lagoas",
           "Divinópolis", "Varginha", "Pouso Alegre", "Teófilo Otoni", "Governador Valadares"],
    "PA": ["Belém", "Ananindeua", "Santarém", "Marabá", "Parauapebas", "Castanhal",
           "Abaetetuba", "Marituba", "Barcarena", "Altamira", "Bragança"],
    "PB": ["João Pessoa", "Campina Grande", "Santa Rita", "Patos", "Bayeux", "Sousa",
           "Cabedelo", "Guarabira", "Cajazeiras", "Mamanguape"],
    "PR": ["Curitiba", "Londrina", "Maringá", "Ponta Grossa", "Cascavel", "Foz do Iguaçu",
           "Colombo", "Guarapuava", "Paranaguá", "Arapongas", "Toledo", "Apucarana"],
    "PE": ["Recife", "Jaboatão dos Guararapes", "Olinda", "Caruaru", "Petrolina", "Paulista",
           "Cabo de Santo Agostinho", "Camaragibe", "Garanhuns", "Ipojuca", "Araripina"],
    "PI": ["Teresina", "Parnaíba", "Picos", "Floriano", "Piripiri", "Campo Maior", "Barras",
           "Pedro II", "Oeiras", "São Raimundo Nonato"],
    "RJ": ["Rio de Janeiro", "São Gonçalo", "Duque de Caxias", "Nova Iguaçu", "Niterói",
           "Belford Roxo", "Campos dos Goytacazes", "Petrópolis", "Volta Redonda", "Magé",
           "Itaguaí", "Barra Mansa", "Macaé", "Cabo Frio", "Angra dos Reis"],
    "RN": ["Natal", "Mossoró", "Parnamirim", "São Gonçalo do Amarante", "Ceará-Mirim",
           "Caicó", "Currais Novos", "Açu", "Macaíba", "Santa Cruz"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Santa Maria", "Gravataí",
           "Viamão", "Alvorada", "Passo Fundo", "Novo Hamburgo", "Santa Cruz do Sul",
           "Lajeado", "Uruguaiana", "Bagé", "Erechim"],
    "RO": ["Porto Velho", "Ji-Paraná", "Ariquemes", "Vilhena", "Cacoal", "Rolim de Moura",
           "Guajará-Mirim", "Jaru", "Colorado do Oeste"],
    "RR": ["Boa Vista", "Rorainópolis", "Caracaraí", "Alto Alegre", "Mucajaí", "Cantá",
           "Pacaraima", "Normandia"],
    "SC": ["Florianópolis", "Joinville", "Blumenau", "São José", "Chapecó", "Criciúma",
           "Itajaí", "Jaraguá do Sul", "Lages", "Balneário Camboriú", "Brusque",
           "Concórdia", "Tubarão"],
    "SP": ["São Paulo", "Guarulhos", "Campinas", "São Bernardo do Campo", "Santo André",
           "Osasco", "Ribeirão Preto", "Sorocaba", "Mauá", "São José dos Campos", "Santos",
           "Jundiaí", "Piracicaba", "Carapicuíba", "Bauru", "Itaquaquecetuba",
           "São José do Rio Preto", "Franca", "Limeira", "Praia Grande"],
    "SE": ["Aracaju", "Nossa Senhora do Socorro", "Lagarto", "São Cristóvão", "Itabaiana",
           "Estância", "Tobias Barreto", "Propriá", "Simão Dias", "Carmópolis"],
    "TO": ["Palmas", "Araguaína", "Gurupi", "Porto Nacional", "Paraíso do Tocantins",
           "Colinas do Tocantins", "Guaraí", "Formoso do Araguaia", "Dianópolis",
           "Miracema do Tocantins"],
}

UF_DA_CIDADE: dict[str, str] = {
    cidade: uf for uf, cidades in CIDADES_POR_UF.items() for cidade in cidades
}

BAIRROS = [
    "Centro", "Jardim América", "Vila Nova", "Boa Vista", "Santa Cruz", "São José",
    "Bela Vista", "Liberdade", "Industrial", "Planalto", "Jardim Europa", "Santo Antônio",
    "Cidade Nova", "Morumbi", "Copacabana", "Boa Esperança", "Alto da Colina", "Vila Progresso",
]
COMPLEMENTOS = [
    "Apto 12", "Apto 34 B", "Casa", "Sobrado", "Lote 5", "Quadra 12", "Sala 201", "Fundo",
    "Casa 2", "Bloco C apto 405", "Sem complemento",
]
ESCOLARIDADES = [
    "Fundamental incompleto", "Fundamental completo", "Ensino médio incompleto",
    "Ensino médio completo", "Superior incompleto", "Superior completo",
    "Pós-graduação", "Mestrado", "Doutorado",
]
PROFISSOES = [
    "Analista de sistemas", "Enfermeiro(a)", "Professor(a)", "Vendedor(a)", "Motorista",
    "Contador(a)", "Advogado(a)", "Eletricista", "Cozinheiro(a)", "Atendente",
    "Técnico em segurança do trabalho", "Auxiliar administrativo", "Engenheiro(a)",
    "Designer", "Auxiliar de logística", "Mecânico", "Farmacêutico(a)", "Pedreiro",
]

# ---------------------------------------------------------------------------
# Região: a cidade, o CEP e o DDD sempre batem com o mesmo estado
# ---------------------------------------------------------------------------


class Regiao(dict):
    """Região sorteada: uf, cidade, faixas de CEP e DDDs do mesmo estado."""

    @property
    def uf(self) -> str:
        return self["uf"]

    @property
    def cidade(self) -> str:
        return self["cidade"]

    @property
    def cep_faixas(self) -> list[tuple[int, int]]:
        return self["cep_faixas"]

    @property
    def ddds(self) -> list[int]:
        return self["ddds"]


def sorteia_regiao(estados: list[str] | None, cidades: list[str] | None) -> Regiao:
    """Sorteia uma região coerente, respeitando os estados/cidades filtrados."""
    if cidades:
        cidade = escolher(cidades)
        uf = UF_DA_CIDADE.get(cidade) or escolher(estados or SIGLAS_BR)
    else:
        uf = escolher(estados or SIGLAS_BR)
        cidade = escolher(CIDADES_POR_UF.get(uf, [uf]))
    return Regiao(
        uf=uf,
        cidade=cidade,
        cep_faixas=CEP_POR_UF.get(uf, [(0, 99999999)]),
        ddds=DDDS_POR_UF.get(uf, [11]),
    )


def cep_da_regiao(regiao: Regiao, minimo: int | None, maximo: int | None) -> str:
    """CEP com 8 dígitos, da faixa pedida ou da faixa do estado."""
    if minimo is not None and maximo is not None:
        return str(int_min_max(minimo, maximo)).zfill(8)
    inicio, fim = escolher(regiao.cep_faixas)
    return str(int_min_max(inicio, fim)).zfill(8)


def telefone_da_regiao(regiao: Regiao) -> str:
    return f"({escolher(regiao.ddds)}) {int_min_max(2, 5)}{''.join(map(str, digitos(3)))}-{''.join(map(str, digitos(4)))}"


def celular_da_regiao(regiao: Regiao) -> str:
    return f"({escolher(regiao.ddds)}) 9{''.join(map(str, digitos(4)))}-{''.join(map(str, digitos(4)))}"


# ---------------------------------------------------------------------------
# Dígitos verificadores
# ---------------------------------------------------------------------------


def _mod11(soma: int) -> int:
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def _somente_digitos(valor: str) -> str:
    return "".join(c for c in valor if c.isdigit())


def cpf_valido(valor: str) -> bool:
    """Confere os dois dígitos verificadores do CPF."""
    d = _somente_digitos(valor)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    n = [int(c) for c in d]
    for p in (10, 11):
        soma = sum(n[i] * (p - i) for i in range(p - 1))
        if _mod11(soma) != n[p - 1]:
            return False
    return True


def cnpj_valido(valor: str) -> bool:
    """Confere os dois dígitos verificadores do CNPJ."""
    d = _somente_digitos(valor)
    if len(d) != 14 or len(set(d)) == 1:
        return False
    n = [int(c) for c in d]
    pesos = [
        [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
        [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
    ]
    for k, p in enumerate(pesos):
        soma = sum(n[i] * p[i] for i in range(len(p)))
        resto = soma % 11
        if (0 if resto < 2 else 11 - resto) != n[12 + k]:
            return False
    return True


def luhn_valido(numero: str) -> bool:
    """Regra de Luhn, a mesma dos números de cartão."""
    d = [int(c) for c in reversed(_somente_digitos(numero))]
    if len(d) < 12:
        return False
    soma = 0
    for i, n in enumerate(d):
        if i % 2:
            n = n * 2
            if n > 9:
                n -= 9
        soma += n
    return soma % 10 == 0


def cnh_valida(valor: str) -> bool:
    """Confere os dois dígitos verificadores da CNH."""
    d = _somente_digitos(valor)
    if len(d) != 11:
        return False
    n = [int(c) for c in d]
    s1 = sum(n[i] * (9 - i) for i in range(9))
    r1 = s1 % 11
    dv1 = 0 if r1 >= 10 else r1
    if dv1 != n[9]:
        return False
    s2 = dv1 * 2 + sum(n[i] * (i + 1) for i in range(9))
    r2 = s2 % 11
    return (0 if r2 >= 10 else r2) == n[10]


def pis_valido(valor: str) -> bool:
    """Confere o dígito verificador do PIS/NIT."""
    d = _somente_digitos(valor)
    if len(d) != 11:
        return False
    n = [int(c) for c in d]
    pesos = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(n[i] * pesos[i] for i in range(10))
    return _mod11(soma) == n[10]


def titulo_valido(valor: str) -> bool:
    """Confere os dois dígitos verificadores do título de eleitor."""
    d = _somente_digitos(valor)
    if len(d) != 12:
        return False
    n = [int(c) for c in d]
    uf = n[8] * 10 + n[9]
    if uf < 1 or uf > 29:
        return False
    s1 = sum(n[i] * (2 + i) for i in range(8))
    r1 = s1 % 11
    dv1 = 0 if r1 >= 10 else r1
    if dv1 != n[10]:
        return False
    parte = [n[6], n[7], n[8], n[9], dv1]
    s2 = sum(x * (i + 1) for i, x in enumerate(parte))
    r2 = s2 % 11
    return (0 if r2 >= 10 else r2) == n[11]


def codigo_barras_valido(valor: str) -> bool:
    """Confere o dígito verificador do código de barras de boleto."""
    d = _somente_digitos(valor)
    if len(d) != 44:
        return False
    sem_dv = d[:4] + d[5:]
    soma = 0
    peso = 2
    for i in range(len(sem_dv) - 1, -1, -1):
        soma += int(sem_dv[i]) * peso
        peso = 2 if peso == 9 else peso + 1
    r = 11 - (soma % 11)
    dv = 0 if r > 9 or r == 0 else r
    return dv == int(d[4])


# ---------------------------------------------------------------------------
# Geradores
# ---------------------------------------------------------------------------


def cnh() -> str:
    """CNH com os dois dígitos verificadores corretos."""
    base = digitos(9)
    s1 = sum(base[i] * (9 - i) for i in range(9))
    r1 = s1 % 11
    dv1 = 0 if r1 >= 10 else r1
    s2 = dv1 * 2 + sum(base[i] * (i + 1) for i in range(9))
    r2 = s2 % 11
    dv2 = 0 if r2 >= 10 else r2
    return "".join(map(str, base + [dv1, dv2]))


def pis() -> str:
    """PIS/NIT com dígito verificador correto."""
    base = [int_min_max(1, 9)] + digitos(9)
    pesos = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(base[i] * pesos[i] for i in range(10))
    return "".join(map(str, base)) + str(_mod11(soma))


def titulo_de_eleitor(uf_codigo: int | None = None) -> str:
    """Título de eleitor com os dois dígitos verificadores corretos."""
    seq = digitos(6)
    zona = [int_min_max(0, 9), int_min_max(0, 9)]
    uf = [int(c) for c in str(uf_codigo or int_min_max(1, 29)).zfill(2)]
    oitos = seq + zona
    s1 = sum(x * (2 + i) for i, x in enumerate(oitos))
    r1 = s1 % 11
    dv1 = 0 if r1 >= 10 else r1
    parte = zona + uf + [dv1]
    s2 = sum(x * (i + 1) for i, x in enumerate(parte))
    r2 = s2 % 11
    dv2 = 0 if r2 >= 10 else r2
    return "".join(map(str, oitos + uf + [dv1, dv2]))


LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def placa_mercosul() -> str:
    """Placa no padrão Mercosul: ABC1D23."""
    return (
        escolher(LETRAS) + escolher(LETRAS) + escolher(LETRAS)
        + str(int_min_max(0, 9)) + escolher(LETRAS)
        + "".join(map(str, digitos(2)))
    )


BANCOS: list[tuple[str, str]] = [
    ("001", "Banco do Brasil"), ("033", "Santander"), ("104", "Caixa Econômica Federal"),
    ("237", "Bradesco"), ("260", "Nubank"), ("341", "Itaú Unibanco"),
    ("745", "Sicredi"), ("77", "Banco Inter"), ("290", "PagBank"),
    ("389", "Mercado Pago"),
]


def _dv_mod11_peso(base: list[int]) -> int:
    """Dígito verificador com pesos 2 a 9 contando da direita (boleto e conta)."""
    soma = 0
    peso = 2
    for i in range(len(base) - 1, -1, -1):
        soma += base[i] * peso
        peso = 2 if peso == 9 else peso + 1
    r = 11 - (soma % 11)
    return 0 if r > 9 or r == 0 else r


def conta_bancaria() -> dict:
    """Banco, agência e conta com dígito verificador."""
    codigo, nome = escolher(BANCOS)
    agencia = str(int_min_max(1, 9999)).zfill(4)
    base = digitos(7)
    return {
        "banco": f"{codigo} – {nome}",
        "agencia": agencia,
        "conta": "".join(map(str, base)) + f"-{_dv_mod11_peso(base)}",
    }


def uuid() -> str:
    """Código único aleatório, sem significado (36 caracteres com hífens)."""
    return str(_uuid.uuid4())


def codigo_barras() -> str:
    """Linha digitável de boleto com 44 dígitos e dígito verificador real."""
    banco = str(int_min_max(1, 999)).zfill(3)
    moeda = "9"
    fator = str(int_min_max(1000, 9999))
    valor = str(int_min_max(100, 9999999999)).zfill(10)
    livre = digitos(25)
    sem_dv = [int(c) for c in banco + moeda + fator + valor] + livre
    return banco + moeda + str(_dv_mod11_peso(sem_dv)) + fator + valor + "".join(map(str, livre))


def moeda(minimo: float = 10, maximo: float = 250000) -> str:
    """Valor em reais no formato brasileiro: 1.500,00."""
    centavos = int_min_max(round(minimo * 100), round(maximo * 100))
    inteiro, fração = divmod(centavos, 100)
    return f"{inteiro:,}".replace(",", ".") + f",{fração:02d}"


def fmt_data(d: date) -> str:
    """Data no formato dd/mm/aaaa, sem hora."""
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def data_cadastro(dias_atras: int = 730) -> str:
    """Data de cadastro recente, só com dia, mês e ano."""
    hoje = date.today()
    d = hoje - timedelta(days=random.randint(0, dias_atras))
    return fmt_data(d)


# ---------------------------------------------------------------------------
# PIX
# ---------------------------------------------------------------------------

TIPOS_PIX = ["cpf", "cnpj", "email", "telefone", "aleatoria"]
NOME_TIPO_PIX = {
    "cpf": "CPF",
    "cnpj": "CNPJ",
    "email": "E-mail",
    "telefone": "Celular",
    "aleatoria": "Chave aleatória",
}


def chave_pix(pessoa: dict, tipo: str | None = None) -> str:
    """Chave PIX montada a partir dos dados da própria linha."""
    escolha = tipo or escolher(TIPOS_PIX)
    if escolha == "cpf":
        return _somente_digitos(pessoa["cpf"])
    if escolha == "cnpj":
        return _somente_digitos(pessoa["cnpj"])
    if escolha == "email":
        return pessoa["email"]
    if escolha == "telefone":
        return _somente_digitos(pessoa["celular"])
    return uuid()
