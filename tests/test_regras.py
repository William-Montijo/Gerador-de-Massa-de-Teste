"""
Testes das regras do QAhub: coerência regional, dígitos verificadores,
sujeira na planilha, validador, modelos e nome do arquivo.
"""

import re
from datetime import date, datetime

import pytest

from qahub import brasil, config as cfg_mod, geradores, historico, planilha


def OPC(**sob):
    o = geradores.opcoes_padrao()
    o.update(sob)
    return o


def linha(cols, **sob):
    return geradores.gerar_registro(cols, OPC(**sob), 0)


def linhas(n, cols, **sob):
    return [geradores.gerar_registro(cols, OPC(**sob), i) for i in range(n)]


def real(v):
    return float(str(v).replace(".", "").replace(",", "."))


# ---------------------------------------------------------------------------
# Coerência regional
# ---------------------------------------------------------------------------


def test_cep_cidade_uf_e_ddd_sao_da_mesma_regiao():
    cols = ["Cidade", "Estado (UF)", "CEP", "Celular"]
    for i in range(80):
        r = geradores.gerar_registro(cols, OPC(), i)
        uf = r["Estado (UF)"]
        cep = int(re.sub(r"\D", "", r["CEP"]))
        assert any(a <= cep <= b for a, b in brasil.CEP_POR_UF[uf]), r
        assert int(r["Celular"][1:3]) in brasil.DDDS_POR_UF[uf], r
        assert brasil.UF_DA_CIDADE[r["Cidade"]] == uf, r


def test_nenhuma_cidade_aparece_em_dois_estados():
    vistos = {}
    for uf, cidades in brasil.CIDADES_POR_UF.items():
        for c in cidades:
            assert c not in vistos, f"{c} está em {vistos.get(c)} e em {uf}"
            vistos[c] = uf


def test_restringe_ao_estado_marcado():
    for i in range(40):
        r = geradores.gerar_registro(["Estado (UF)", "Cidade"], OPC(estados=["MG"]), i)
        assert r["Estado (UF)"] == "MG"
        assert brasil.UF_DA_CIDADE[r["Cidade"]] == "MG"


def test_respeita_a_faixa_de_cep_pedida():
    for i in range(40):
        n = int(geradores.gerar_registro(["CEP"], OPC(cep_min=38400000, cep_max=38499999), i)["CEP"])
        assert 38400000 <= n <= 38499999


def test_usa_so_as_cidades_escolhidas():
    for i in range(30):
        r = geradores.gerar_registro(["Cidade"], OPC(cidades=["Uberlândia", "Belo Horizonte"]), i)
        assert r["Cidade"] in ("Uberlândia", "Belo Horizonte")


# ---------------------------------------------------------------------------
# Dígitos verificadores
# ---------------------------------------------------------------------------


def test_cnh_pis_titulo_e_codigo_de_barras_saem_validos():
    for _ in range(40):
        assert brasil.cnh_valida(brasil.cnh())
        assert brasil.pis_valido(brasil.pis())
        assert brasil.titulo_valido(brasil.titulo_de_eleitor())
        barra = brasil.codigo_barras()
        assert brasil.codigo_barras_valido(barra)
        quebrada = barra[:4] + str((int(barra[4]) + 1) % 10) + barra[5:]
        assert not brasil.codigo_barras_valido(quebrada)


def test_placa_uuid_e_valor_vem_no_formato_brasileiro():
    for _ in range(30):
        assert re.match(r"^[A-Z]{3}\d[A-Z]\d{2}$", brasil.placa_mercosul())
        assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
                        brasil.uuid(), re.I)
        assert re.match(r"^\d{1,3}(\.\d{3})*,\d{2}$", brasil.moeda())


def test_cpf_e_cnpj_gerados_passam_na_conferencia():
    for _ in range(40):
        assert brasil.cpf_valido(geradores.cpf())
        assert brasil.cnpj_valido(geradores.cnpj())
        assert brasil.luhn_valido(geradores.cartao("Visa"))


# ---------------------------------------------------------------------------
# PIX ligado à linha
# ---------------------------------------------------------------------------


def test_cada_tipo_de_pix_usa_o_dado_da_mesma_linha():
    cols = ["CPF", "CNPJ", "E-mail", "Celular", "PIX"]
    for i in range(20):
        a = geradores.gerar_registro(cols, OPC(pix_tipo="cpf"), i)
        assert a["PIX"] == re.sub(r"\D", "", a["CPF"])
        b = geradores.gerar_registro(cols, OPC(pix_tipo="cnpj"), i)
        assert b["PIX"] == re.sub(r"\D", "", b["CNPJ"])
        c = geradores.gerar_registro(cols, OPC(pix_tipo="email"), i)
        assert c["PIX"] == c["E-mail"]
        d = geradores.gerar_registro(cols, OPC(pix_tipo="telefone"), i)
        assert d["PIX"] == re.sub(r"\D", "", d["Celular"])
        e = geradores.gerar_registro(cols, OPC(pix_tipo="aleatoria"), i)
        assert re.match(r"^[0-9a-f-]{36}$", e["PIX"], re.I)


def test_pix_sorteado_cai_em_um_dos_cinco_formatos():
    vistos = set()
    for _ in range(300):
        k = brasil.chave_pix({"cpf": "12345678909", "cnpj": "12345678000199",
                              "email": "nome.sobren@empresa.com", "celular": "34998765432"})
        if k == "12345678909":
            vistos.add("cpf")
        elif k == "12345678000199":
            vistos.add("cnpj")
        elif "@" in k:
            vistos.add("email")
        elif k == "34998765432":
            vistos.add("telefone")
        else:
            vistos.add("aleatoria")
    assert vistos == {"cpf", "cnpj", "email", "telefone", "aleatoria"}


# ---------------------------------------------------------------------------
# Sujeira na planilha
# ---------------------------------------------------------------------------


def test_linhas_duplicadas_sao_copias_exatas():
    cols = ["Nome completo", "CPF"]
    regs = linhas(20, cols)
    geradores.aplicar_sujeira(regs, cols, {**cfg_mod.SUJEIRA_PADRAO, "duplicadas": 3})
    assert len(regs) == 20
    assert len({tuple(sorted(r.items())) for r in regs}) < 20


def test_mesmo_cpf_aparece_em_nomes_diferentes():
    cols = ["Nome completo", "CPF"]
    regs = linhas(30, cols)
    geradores.aplicar_sujeira(regs, cols, {**cfg_mod.SUJEIRA_PADRAO, "cpf_repetido": 5})
    por_cpf = {}
    for r in regs:
        por_cpf.setdefault(str(r["CPF"]), []).append(str(r["Nome completo"]))
    repetido = next((nomes for nomes in por_cpf.values() if len(nomes) > 1), None)
    assert repetido is not None
    assert len(set(repetido)) > 1


def test_email_sai_com_caixa_diferente_espacos_ou_arroba_solto():
    cols = ["E-mail"]
    regs = linhas(30, cols)
    antes = [r["E-mail"] for r in regs]
    geradores.aplicar_sujeira(regs, cols, {**cfg_mod.SUJEIRA_PADRAO, "email_variacao": 10})
    mudadas = [r["E-mail"] for r, a in zip(regs, antes) if r["E-mail"] != a]
    assert mudadas
    assert all(m != m.strip() or m != m.lower() or " @ " in m for m in mudadas)


def test_espacos_sobrando_entram_no_comeco_e_no_fim():
    cols = ["Nome completo", "Endereço", "Bairro"]
    regs = linhas(30, cols)
    antes = [dict(r) for r in regs]
    geradores.aplicar_sujeira(regs, cols, {**cfg_mod.SUJEIRA_PADRAO, "espacos": 8})
    mudadas = [r for r, a in zip(regs, antes) if r != a]
    assert mudadas
    for r in mudadas:
        assert any(isinstance(v, str) and v.startswith("  ") and v != v.strip() for v in r.values())


def test_campo_vazio_e_linha_em_branco_aparecem():
    cols = ["Nome completo", "CPF", "E-mail"]
    regs = linhas(20, cols)
    geradores.aplicar_sujeira(regs, cols, {**cfg_mod.SUJEIRA_PADRAO, "vazios": 4, "linha_branca": 2})
    assert len(regs) == 22
    assert sum(1 for r in regs if all(r[c] == "" for c in cols)) >= 2
    assert any(any(r[c] == "" for c in cols) and any(r[c] != "" for c in cols) for r in regs)


def test_sem_sujeira_a_planilha_fica_intacta():
    cols = ["Nome completo", "CPF"]
    regs = linhas(10, cols)
    antes = [dict(r) for r in regs]
    geradores.aplicar_sujeira(regs, cols, cfg_mod.SUJEIRA_PADRAO)
    assert regs == antes


# ---------------------------------------------------------------------------
# Validador
# ---------------------------------------------------------------------------


def test_validador_confere_os_tipos():
    assert geradores.validar_valor(geradores.cpf())["tipo"] == "CPF"
    assert geradores.validar_valor(geradores.cpf())["valido"] is True
    assert geradores.validar_valor("11.222.333/0001-81")["tipo"] == "CNPJ"
    assert geradores.validar_valor("11.222.333/0001-81")["valido"] is True
    assert geradores.validar_valor(geradores.cartao("Visa"))["tipo"] == "Cartão de crédito"
    assert geradores.validar_valor("01001-000")["tipo"] == "CEP"
    assert geradores.validar_valor("nome.sobren@empresa.com")["tipo"] == "E-mail"
    assert geradores.validar_valor("ABC1D23")["tipo"] == "Placa Mercosul"


def test_validador_rejeita_o_que_esta_errado():
    assert geradores.validar_valor("12.345.678/0001-99")["valido"] is False
    assert geradores.validar_valor("120.26807.06-9")["valido"] is False
    assert geradores.validar_valor("123")["tipo"] == "não reconhecido"
    assert geradores.validar_valor("")["tipo"] == "vazio"


# ---------------------------------------------------------------------------
# Escolaridade, renda, valor e data
# ---------------------------------------------------------------------------


def test_escolaridade_fixa_sai_em_todas_as_linhas():
    for r in linhas(30, ["Escolaridade"], escolaridade="Superior completo"):
        assert r["Escolaridade"] == "Superior completo"


def test_sem_filtro_a_escolaridade_e_um_dos_tipos():
    for r in linhas(30, ["Escolaridade"]):
        assert r["Escolaridade"] in brasil.ESCOLARIDADES


def test_a_renda_respeita_a_faixa_informada():
    for r in linhas(50, ["Renda mensal"], renda_min=2500, renda_max=4000):
        assert 2500 <= real(r["Renda mensal"]) <= 4000


def test_sem_faixa_a_renda_fica_no_padrao():
    for r in linhas(50, ["Renda mensal"]):
        assert 1412 <= real(r["Renda mensal"]) <= 30000


def test_valor_fixo_repete_o_mesmo_valor():
    for r in linhas(30, ["Valor"], valor_fixo=1500):
        assert r["Valor"] == "1.500,00"
        assert real(r["Valor"]) == 1500


def test_valor_fixo_aceita_centavos():
    for r in linhas(10, ["Valor"], valor_fixo=89.9):
        assert r["Valor"] == "89,90"


def test_a_faixa_de_valor_e_respeitada():
    for r in linhas(50, ["Valor"], valor_min=2500, valor_max=4000):
        assert 2500 <= real(r["Valor"]) <= 4000


def test_sem_valor_definido_fica_no_padrao():
    for r in linhas(50, ["Valor"]):
        assert 10 <= real(r["Valor"]) <= 250000


def test_a_data_de_cadastro_soz_com_dia_mes_e_ano():
    for r in linhas(30, ["Data de cadastro"]):
        assert re.match(r"^\d{2}/\d{2}/\d{4}$", r["Data de cadastro"])


# ---------------------------------------------------------------------------
# Dado único, modelos, arquivo e histórico
# ---------------------------------------------------------------------------


def test_gera_cada_tipo_avulso_com_os_campos_esperados():
    o = {"bandeira": "Visa", "sem_pontuacao": True, "senha": geradores.SENHA_PADRAO,
         "cep_min": None, "cep_max": None, "email_dominio": None,
         "valor_fixo": None, "valor_min": None, "valor_max": None}
    assert [x[0] for x in geradores.gerar_dado_unico("Cartão de crédito", o)] == ["Número", "Validade", "CVV"]
    assert [x[0] for x in geradores.gerar_dado_unico("Conta bancária", o)] == ["Banco", "Agência", "Conta"]
    assert re.match(r"^\d{11}$", geradores.gerar_dado_unico("CPF", o)[0][1])
    assert re.match(r"^\d{14}$", geradores.gerar_dado_unico("CNPJ", o)[0][1])
    assert geradores.gerar_dado_unico("PIX", o)[0][0] == "Chave PIX"
    assert re.match(r"^\d{11}$", geradores.gerar_dado_unico("CNH", o)[0][1])
    assert re.match(r"^\d{12}$", geradores.gerar_dado_unico("Título de eleitor", o)[0][1])
    assert re.match(r"^\d{2}/\d{2}/\d{4}$", geradores.gerar_dado_unico("Data de cadastro", o)[0][1])


def test_todo_modelo_usa_colunas_que_existem():
    for m in cfg_mod.MODELOS:
        assert m["colunas"]
        for c in m["colunas"]:
            assert c in geradores.COLUNAS_DISPONIVEIS


def test_nome_do_arquivo_traz_a_base_a_data_e_a_extensao():
    quando = datetime(2026, 5, 17, 14, 5)
    assert planilha.nome_arquivo("massa_cadastro", "csv", quando) == "massa_cadastro_2026-05-17_1405.csv"
    assert planilha.nome_arquivo("massa", "xlsx", quando) == "massa_2026-05-17_1405.xlsx"
    assert planilha.nome_arquivo("meu/arquivo", "json", quando) == "meu-arquivo_2026-05-17_1405.json"
    assert planilha.nome_arquivo("   ", "xlsx", quando) == "massa_de_teste_2026-05-17_1405.xlsx"


def test_configuracao_comeca_sem_restricao_sem_sujeira_e_sem_coluna():
    c = cfg_mod.config_inicial()
    assert c["colunas"] == []
    assert c["estados"] == []
    assert c["cidades"] == []
    assert c["cep_min"] is None
    assert c["dominio"] == ""
    assert c["sujeira"] == {"duplicadas": 0, "cpf_repetido": 0, "email_variacao": 0,
                            "espacos": 0, "vazios": 0, "linha_branca": 0}
    assert c["rg_sem_pontos"] is False
    assert c["telefone_sem_pontos"] is False
    assert c["celular_sem_pontos"] is False


def test_arquivos_exportados_tem_o_mesmo_numero_de_linhas():
    cols = ["Nome completo", "CPF", "E-mail"]
    regs = linhas(12, cols)
    nome, xlsx, _ = planilha.gerar_arquivo(cols, regs, True, "xlsx", "teste")
    _, csv, _ = planilha.gerar_arquivo(cols, regs, True, "csv", "teste")
    _, js, _ = planilha.gerar_arquivo(cols, regs, True, "json", "teste")
    assert xlsx[:2] == b"PK"
    assert csv.decode("utf-8-sig").strip().count("\n") == 12
    assert js.decode("utf-8").count("CPF") == 12
    assert nome.endswith(".xlsx")


def test_historico_guarda_no_maximo_oito_e_a_mais_recente_primeiro():
    itens = []
    for i in range(10):
        itens = historico.registrar(itens, {"token": i, "colunas": ["CPF"], "quantidade": i,
                                            "nome_base": "", "com_titulo": True, "quando": ""})
    assert len(itens) == 8
    assert itens[0]["token"] == 9
    assert itens[-1]["token"] == 2


# ---------------------------------------------------------------------------
# RG, telefone e celular com ou sem pontuação
# ---------------------------------------------------------------------------


def test_rg_sai_com_pontos_e_traco_por_padrao():
    assert re.fullmatch(r"\d{2}\.\d{3}\.\d{3}-[0-9X]", linha(["RG"])["RG"])


def test_rg_sem_pontos_mantem_o_digito_x():
    assert re.fullmatch(r"\d{8}[0-9X]", linha(["RG"], rg_sem_pontos=True)["RG"])


def test_telefone_so_numeros_quando_marcado():
    assert re.fullmatch(r"\(\d{2}\) \d{4}-\d{4}", linha(["Telefone"])["Telefone"])
    assert re.fullmatch(r"\d{10}", linha(["Telefone"], telefone_sem_pontos=True)["Telefone"])


def test_celular_so_numeros_quando_marcado():
    assert re.fullmatch(r"\(\d{2}\) 9\d{4}-\d{4}", linha(["Celular"])["Celular"])
    assert re.fullmatch(r"\d{11}", linha(["Celular"], celular_sem_pontos=True)["Celular"])


def test_dado_unico_sem_pontuacao_para_rg_telefone_e_celular():
    assert re.fullmatch(r"\d{8}[0-9X]", geradores.gerar_dado_unico("RG", {"sem_pontuacao": True})[0][1])
    assert re.fullmatch(r"\d{10}", geradores.gerar_dado_unico("Telefone", {"sem_pontuacao": True})[0][1])
    assert re.fullmatch(r"\d{11}", geradores.gerar_dado_unico("Celular", {"sem_pontuacao": True})[0][1])
    assert re.fullmatch(r"\(\d{2}\) 9\d{4}-\d{4}", geradores.gerar_dado_unico("Celular", {})[0][1])


def test_montar_opcoes_repassa_as_tres_escolhas():
    opc = cfg_mod.montar_opcoes({**cfg_mod.config_inicial(), "rg_sem_pontos": True,
                                 "telefone_sem_pontos": True, "celular_sem_pontos": False})
    assert opc["rg_sem_pontos"] is True
    assert opc["telefone_sem_pontos"] is True
    assert opc["celular_sem_pontos"] is False


# ---------------------------------------------------------------------------
# Filtro de estado (DDD) na geração de dado único
# ---------------------------------------------------------------------------


def _ddds_de(tipo, estados, n=40):
    s = set()
    for _ in range(n):
        v = geradores.gerar_dado_unico(tipo, {"estados": estados})[0][1]
        m = re.match(r"\((\d{2})\)", v)
        s.add(m.group(1))
    return s


def test_dado_unico_de_telefone_respeita_o_estado_filtrado():
    assert _ddds_de("Telefone", ["SP"]) <= {"11", "12", "13", "14", "15", "16", "17", "18", "19"}


def test_dado_unico_de_celular_respeita_o_estado_filtrado():
    assert _ddds_de("Celular", ["RJ"]) <= {"21", "22", "24"}


def test_dado_unico_de_cep_respeita_o_estado_filtrado():
    cep = int(geradores.gerar_dado_unico("CEP", {"estados": ["RJ"]})[0][1])
    assert 20000000 <= cep <= 28999999


def test_dado_unico_sem_filtro_sai_de_estados_diferentes():
    assert len(_ddds_de("Telefone", None, 80)) > 1


def test_cpf_nono_digito_da_regiao_fiscal():
    for uf, dig in (("RJ", 7), ("SP", 8), ("RS", 0), ("SC", 9)):
        for _ in range(30):
            c = geradores.cpf(uf)
            assert brasil.cpf_valido(c)
            assert int(re.sub(r"\D", "", c)[8]) == dig


def test_cpf_da_planilha_e_do_dado_unico_seguem_o_estado():
    for _ in range(30):
        r = geradores.gerar_registro(["CPF", "Estado"], {"estados": ["RJ"]}, 0)
        assert re.sub(r"\D", "", r["CPF"])[8] == "7"
        v = geradores.gerar_dado_unico("CPF", {"estados": ["SP"]})[0][1]
        assert re.sub(r"\D", "", v)[8] == "8"
