"""
QAhub - Gerador de Massa de Teste
----------------------------------
Programa com interface grafica moderna para gerar dados fake (nome, CPF, CNPJ,
cartao de credito, etc.) para massa de teste de QA:

  - Aba "Gerar planilha": cria uma planilha Excel (.xlsx) com as colunas
    escolhidas e a quantidade de registros desejada.
  - Aba "Dado unico": gera um unico valor na tela (CPF, CNPJ, cartao com
    bandeira + validade + CVV, RG...) com botao de copiar.

Como usar:
    1. pip install -r requirements.txt
    2. python gerador_massa_teste.py
"""

import json
import os
import re
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd
from faker import Faker
from PIL import Image

fake = Faker("pt_BR")

# ---------------------------------------------------------------------------
# Identidade visual QAhub
# ---------------------------------------------------------------------------
COR_LARANJA = "#FF7729"
COR_LARANJA_HOVER = "#E56418"
COR_LARANJA_CLARO = "#FFF1E8"
COR_LARANJA_CLARO_HOVER = "#FFE1CC"
COR_PRETO = "#1A1A1A"
COR_FUNDO = "#F3F4F6"
COR_CARD = "#FFFFFF"
COR_BORDA = "#E5E7EB"
COR_TEXTO_SUAVE = "#6B7280"
COR_ERRO = "#DC2626"
COR_SUCESSO = "#16A34A"

FONTE = "Segoe UI"
FONTE_MONO = "Consolas"

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
CAMINHO_LOGO = os.path.join(PASTA_SCRIPT, "logo-qahub.png")
ARQUIVO_EXTRAS = os.path.join(PASTA_SCRIPT, "colunas_personalizadas.json")


# ---------------------------------------------------------------------------
# Dados e geradores
# ---------------------------------------------------------------------------
BANDEIRAS_CARTAO = {
    "Visa": "visa16",
    "Mastercard": "mastercard",
    "American Express": "amex",
    "Discover": "discover",
    "Diners Club": "diners",
    "JCB": "jcb16",
    "Maestro": "maestro",
}
NOME_DA_BANDEIRA = {codigo: nome for nome, codigo in BANDEIRAS_CARTAO.items()}

# (sigla, nome) de todos os estados brasileiros, na mesma ordem usada pelo Faker.
ESTADOS_BR = (
    ("AC", "Acre"), ("AL", "Alagoas"), ("AP", "Amapá"), ("AM", "Amazonas"),
    ("BA", "Bahia"), ("CE", "Ceará"), ("DF", "Distrito Federal"),
    ("ES", "Espírito Santo"), ("GO", "Goiás"), ("MA", "Maranhão"),
    ("MT", "Mato Grosso"), ("MS", "Mato Grosso do Sul"), ("MG", "Minas Gerais"),
    ("PA", "Pará"), ("PB", "Paraíba"), ("PR", "Paraná"), ("PE", "Pernambuco"),
    ("PI", "Piauí"), ("RJ", "Rio de Janeiro"), ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"), ("RO", "Rondônia"), ("RR", "Roraima"),
    ("SC", "Santa Catarina"), ("SP", "São Paulo"), ("SE", "Sergipe"),
    ("TO", "Tocantins"),
)
SIGLAS_BR = [sigla for sigla, _nome in ESTADOS_BR]
NOME_DO_ESTADO = dict(ESTADOS_BR)

TIPOS_DADO_UNICO = [
    "CPF",
    "CNPJ",
    "Cartão de crédito",
    "RG",
    "Telefone",
    "Celular",
    "CEP",
    "E-mail",
    "Senha",
]

COLUNAS_DISPONIVEIS = [
    "Nome completo",
    "CPF",
    "CNPJ",
    "Nome da empresa",
    "Data de nascimento",
    "Idade",
    "Sexo",
    "Estado civil",
    "E-mail",
    "Telefone",
    "Celular",
    "RG",
    "Endereço",
    "Bairro",
    "Cidade",
    "Estado (UF)",
    "CEP",
    "Senha",
    "Cartão de crédito",
    "Bandeira do cartão",
    "Validade do cartão",
    "CVV do cartão",
]

# Colunas que ja vem marcadas ao abrir o programa (nenhuma: o usuario escolhe).
COLUNAS_PADRAO: set[str] = set()

NASCIMENTO_PADRAO = {"modo": "idade", "idade_min": 18, "idade_max": 80}
SENHA_PADRAO = {
    "length": 10,
    "upper_case": True,
    "lower_case": True,
    "digits": True,
    "special_chars": True,
}


def _calcular_idade(nascimento: date) -> int:
    hoje = date.today()
    idade = hoje.year - nascimento.year
    if (hoje.month, hoje.day) < (nascimento.month, nascimento.day):
        idade -= 1
    return idade


def gerar_data_nascimento(config: dict) -> date:
    """Gera a data de nascimento respeitando o filtro escolhido pelo usuario."""
    if config.get("modo") == "ano":
        inicio = date(config["ano_min"], 1, 1)
        fim = min(date(config["ano_max"], 12, 31), date.today())
        return fake.date_between(start_date=inicio, end_date=fim)
    return fake.date_of_birth(
        minimum_age=config.get("idade_min", 18), maximum_age=config.get("idade_max", 80)
    )


def _somente_numeros(valor: str, ativo: bool) -> str:
    """Remove pontos/traços/barras de CPF e CNPJ quando a opcao esta ligada."""
    return re.sub(r"\D", "", valor) if ativo else valor


def gerar_cep(cep_min: int | None, cep_max: int | None) -> str:
    """Gera um CEP dentro da faixa numerica escolhida (8 digitos, sem traco)."""
    if cep_min is None or cep_max is None:
        return fake.postcode()
    return str(fake.random_int(min=cep_min, max=cep_max)).zfill(8)


def aplicar_duplicatas(registros: list[dict], quantidade: int) -> None:
    """Substitui `quantidade` linhas por copias exatas de linhas anteriores (in-place)."""
    quantidade = min(max(0, quantidade), max(0, len(registros) - 1))
    if quantidade <= 0:
        return
    alvos = fake.random.sample(range(1, len(registros)), quantidade)
    for alvo in alvos:
        origem = fake.random.randint(0, alvo - 1)
        registros[alvo] = dict(registros[origem])


def gerar_senha(config: dict | None = None) -> str:
    """Gera uma senha respeitando as regras escolhidas pelo usuario."""
    config = config or SENHA_PADRAO
    if not any(
        (config.get("upper_case"), config.get("lower_case"), config.get("digits"), config.get("special_chars"))
    ):
        # Faker exige pelo menos um tipo de caractere ligado; sem isso, cai para minusculas.
        config = {**config, "lower_case": True}
    return fake.password(
        length=max(1, config.get("length", 10)),
        special_chars=bool(config.get("special_chars", True)),
        digits=bool(config.get("digits", True)),
        upper_case=bool(config.get("upper_case", True)),
        lower_case=bool(config.get("lower_case", True)),
    )


def gerar_registro(
    colunas: list[str],
    config_nascimento: dict | None = None,
    extras: dict[str, dict] | None = None,
    indice: int = 0,
    config_senha: dict | None = None,
    cpf_sem_pontos: bool = False,
    cnpj_sem_pontos: bool = False,
    estados: list[str] | None = None,
    cidades: list[str] | None = None,
    cep_min: int | None = None,
    cep_max: int | None = None,
    sexo_fixo: str | None = None,
    email_dominio: str | None = None,
) -> dict:
    """Gera uma linha da planilha, na ordem das colunas recebidas.

    extras: colunas personalizadas {nome: {"valores": [...], "sequencial": bool}}.
    indice: numero da linha (usado pelas colunas personalizadas em sequencia).
    estados: siglas de UF permitidas para a coluna "Estado (UF)" (None = todas).
    cidades: nomes de cidade permitidos para a coluna "Cidade" (None = qualquer uma).
    cep_min, cep_max: faixa numerica do CEP (None = sem faixa, usa o padrao do Faker).
    sexo_fixo: "Feminino" ou "Masculino" para nao sortear (None = sorteia).
    email_dominio: dominio fixo para a coluna "E-mail" (None = dominio aleatorio).
    """
    nascimento = gerar_data_nascimento(config_nascimento or NASCIMENTO_PADRAO)

    # Valores sorteados uma unica vez por linha, para os campos ficarem coerentes:
    # nome x sexo, e numero x bandeira x CVV x validade do cartao.
    sexo = sexo_fixo if sexo_fixo in ("Feminino", "Masculino") else fake.random_element(
        elements=("Feminino", "Masculino")
    )
    nome = fake.name_female() if sexo == "Feminino" else fake.name_male()
    tipo_cartao = fake.random_element(elements=tuple(BANDEIRAS_CARTAO.values()))
    lista_estados = estados or SIGLAS_BR

    valores = {
        "Nome completo": lambda: nome,
        "CPF": lambda: _somente_numeros(fake.cpf(), cpf_sem_pontos),
        "CNPJ": lambda: _somente_numeros(fake.cnpj(), cnpj_sem_pontos),
        "Nome da empresa": fake.company,
        "Data de nascimento": lambda: nascimento.strftime("%d/%m/%Y"),
        "Idade": lambda: _calcular_idade(nascimento),
        "Sexo": lambda: sexo,
        "Estado civil": lambda: fake.random_element(
            elements=("Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)")
        ),
        "E-mail": lambda: fake.email(domain=email_dominio) if email_dominio else fake.email(),
        "Telefone": fake.phone_number,
        "Celular": fake.cellphone_number,
        "RG": fake.rg,
        "Endereço": fake.street_address,
        "Bairro": fake.bairro,
        "Cidade": lambda: fake.random_element(elements=cidades) if cidades else fake.city(),
        "Estado (UF)": lambda: fake.random_element(elements=lista_estados),
        "CEP": lambda: gerar_cep(cep_min, cep_max),
        "Senha": lambda: gerar_senha(config_senha),
        "Cartão de crédito": lambda: fake.credit_card_number(card_type=tipo_cartao),
        "Bandeira do cartão": lambda: NOME_DA_BANDEIRA[tipo_cartao],
        "Validade do cartão": fake.credit_card_expire,
        "CVV do cartão": lambda: fake.credit_card_security_code(card_type=tipo_cartao),
    }
    resultado = {}
    for coluna in colunas:
        if coluna in valores:
            resultado[coluna] = valores[coluna]()
        elif extras and coluna in extras:
            opcoes = extras[coluna]["valores"]
            if extras[coluna].get("sequencial"):
                resultado[coluna] = opcoes[indice % len(opcoes)]
            else:
                resultado[coluna] = fake.random.choice(opcoes)
    return resultado


def validar_coluna_extra(nome: str, texto_valores: str, nomes_usados) -> tuple[list[str] | None, str | None]:
    """Valida uma coluna personalizada. Devolve (valores, erro); se houver erro, valores e None."""
    nome = nome.strip()
    if not nome:
        return None, "Dê um nome para a coluna."
    if len(nome) > 60:
        return None, "O nome pode ter no máximo 60 caracteres."
    if nome.lower() in {n.lower() for n in nomes_usados}:
        return None, "Já existe uma coluna com esse nome."
    valores = [linha.strip() for linha in texto_valores.splitlines() if linha.strip()]
    if not valores:
        return None, "Informe pelo menos um valor possível (um por linha)."
    return valores, None


def carregar_colunas_extras() -> list[dict]:
    """Le as colunas personalizadas salvas (ignora arquivo ausente ou invalido)."""
    try:
        with open(ARQUIVO_EXTRAS, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return []

    usados = {c.lower() for c in COLUNAS_DISPONIVEIS}
    extras = []
    for item in dados if isinstance(dados, list) else []:
        try:
            nome = str(item["nome"]).strip()
            valores = [str(v) for v in item["valores"] if str(v).strip()]
            sequencial = bool(item.get("sequencial", False))
        except (KeyError, TypeError, AttributeError):
            continue
        if nome and valores and nome.lower() not in usados:
            usados.add(nome.lower())
            extras.append({"nome": nome, "valores": valores, "sequencial": sequencial})
    return extras


def salvar_colunas_extras(extras: list[dict]) -> bool:
    """Grava as colunas personalizadas em disco. Devolve False se nao conseguiu."""
    try:
        with open(ARQUIVO_EXTRAS, "w", encoding="utf-8") as arquivo:
            json.dump(extras, arquivo, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def gerar_dado_unico(
    tipo: str,
    bandeira: str | None = None,
    sem_pontuacao: bool = False,
    config_senha: dict | None = None,
    cep_min: int | None = None,
    cep_max: int | None = None,
    email_dominio: str | None = None,
) -> list[tuple[str, str]]:
    """Gera um valor avulso. Devolve uma lista de (rotulo, valor)."""
    if tipo == "Cartão de crédito":
        card_type = BANDEIRAS_CARTAO.get(bandeira, "visa16")
        return [
            ("Número", fake.credit_card_number(card_type=card_type)),
            ("Validade", fake.credit_card_expire()),
            ("CVV", fake.credit_card_security_code(card_type=card_type)),
        ]
    if tipo == "Senha":
        return [("Senha", gerar_senha(config_senha))]
    if tipo in ("CPF", "CNPJ"):
        valor = fake.cpf() if tipo == "CPF" else fake.cnpj()
        return [(tipo, _somente_numeros(valor, sem_pontuacao))]
    if tipo == "CEP":
        return [("CEP", gerar_cep(cep_min, cep_max))]
    if tipo == "E-mail":
        return [("E-mail", fake.email(domain=email_dominio) if email_dominio else fake.email())]

    geradores = {
        "RG": fake.rg,
        "Telefone": fake.phone_number,
        "Celular": fake.cellphone_number,
    }
    return [(tipo, str(geradores[tipo]()))]


def salvar_planilha(df: pd.DataFrame, caminho: str, com_titulo: bool = True) -> None:
    """Salva o DataFrame em .xlsx. Com titulo: cabecalho laranja e linha congelada."""
    from openpyxl.styles import Alignment, Font, PatternFill

    nome_aba = "Massa de teste"
    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, header=com_titulo, sheet_name=nome_aba)
        aba = writer.sheets[nome_aba]

        if com_titulo:
            preenchimento = PatternFill("solid", fgColor=COR_LARANJA.lstrip("#"))
            for celula in aba[1]:
                celula.fill = preenchimento
                celula.font = Font(bold=True, color="FFFFFF")
                celula.alignment = Alignment(horizontal="center", vertical="center")
            aba.freeze_panes = "A2"

        for coluna in aba.columns:
            maior = max(len(str(c.value)) if c.value is not None else 0 for c in coluna[:300])
            aba.column_dimensions[coluna[0].column_letter].width = min(maior + 4, 45)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("light")


def _botao_suave(parent, texto, comando, largura=120, altura=32):
    return ctk.CTkButton(
        parent, text=texto, command=comando, width=largura, height=altura,
        fg_color=COR_LARANJA_CLARO, hover_color=COR_LARANJA_CLARO_HOVER,
        text_color=COR_LARANJA_HOVER, corner_radius=10, font=(FONTE, 12, "bold"),
    )


def _botao_principal(parent, texto, comando, altura=52):
    return ctk.CTkButton(
        parent, text=texto, command=comando, height=altura,
        fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color="white",
        corner_radius=14, font=(FONTE, 16, "bold"),
    )


def _checkbox_padrao(parent, texto, var, comando=None, negrito=False):
    return ctk.CTkCheckBox(
        parent, text=texto, variable=var, command=comando,
        fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER,
        border_color="#9CA3AF", checkmark_color="white", text_color=COR_PRETO,
        font=(FONTE, 13, "bold" if negrito else "normal"),
        checkbox_width=22, checkbox_height=22, corner_radius=6,
    )


def _gear(parent, comando):
    return ctk.CTkButton(
        parent, text="⚙", width=28, height=28, corner_radius=8,
        fg_color=COR_LARANJA_CLARO, hover_color=COR_LARANJA_CLARO_HOVER,
        text_color=COR_LARANJA_HOVER, font=(FONTE, 14), command=comando,
    )


def resumo_senha(config: dict) -> str:
    tipos = []
    if config.get("upper_case"):
        tipos.append("maiúsculas")
    if config.get("lower_case"):
        tipos.append("minúsculas")
    if config.get("digits"):
        tipos.append("números")
    if config.get("special_chars"):
        tipos.append("símbolos")
    lista = ", ".join(tipos) if tipos else "letras minúsculas"
    return f"{config.get('length', 10)} caracteres, com {lista}"


def resumo_estados(selecionados: set[str]) -> str:
    if len(selecionados) == len(SIGLAS_BR):
        return "Todos os estados"
    if not selecionados:
        return "Nenhum estado selecionado"
    if len(selecionados) <= 5:
        return ", ".join(sorted(selecionados))
    return f"{len(selecionados)} estados selecionados"


def resumo_cidades(cidades: list[str]) -> str:
    if not cidades:
        return "Qualquer cidade"
    if len(cidades) <= 3:
        return ", ".join(cidades)
    return f"{len(cidades)} cidades selecionadas"


def resumo_cep(cep_min: int | None, cep_max: int | None) -> str:
    if cep_min is None or cep_max is None:
        return "Qualquer CEP"
    return f"De {cep_min:08d} até {cep_max:08d}"


def resumo_sexo(sexo: str | None) -> str:
    if sexo == "Feminino":
        return "Somente feminino"
    if sexo == "Masculino":
        return "Somente masculino"
    return "Sorteado (ambos)"


def resumo_email(dominio: str) -> str:
    return f"Sempre @{dominio}" if dominio else "Domínio aleatório"


def resumo_duplicatas(ativo: bool, quantidade: int) -> str:
    if not ativo or quantidade <= 0:
        return "Nenhuma (todas as linhas únicas)"
    return f"{quantidade} linha{'s' if quantidade != 1 else ''} duplicada{'s' if quantidade != 1 else ''} de propósito"


class GeradorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QAhub | Gerador de Massa de Teste")
        self.configure(fg_color=COR_FUNDO)

        largura = min(1240, self.winfo_screenwidth() - 40)
        altura = min(840, self.winfo_screenheight() - 90)
        x = max(0, (self.winfo_screenwidth() - largura) // 2)
        y = max(0, (self.winfo_screenheight() - altura) // 2 - 20)
        self.geometry(f"{largura}x{altura}+{x}+{y}")
        self.minsize(1100, 700)

        self.checkbox_vars: dict[str, tk.IntVar] = {}
        # ordem em que as colunas aparecem na planilha (= ordem de selecao)
        self.ordem_colunas = [c for c in COLUNAS_DISPONIVEIS if c in COLUNAS_PADRAO]
        self._linhas_ordem = []
        self.config_nascimento = dict(NASCIMENTO_PADRAO)
        self.config_senha = dict(SENHA_PADRAO)
        self.estados_selecionados = set(SIGLAS_BR)
        self.cidades_personalizadas: list[str] = []
        self.cep_min: int | None = None
        self.cep_max: int | None = None
        self.sexo_fixo: str | None = None
        self.email_dominio: str = ""
        self.duplicatas_ativo = tk.IntVar(value=0)
        self._dialogo = None
        self._dialogo_extra = None
        self._dialogo_senha = None
        self._dialogo_estados = None
        self._dialogo_cidades = None
        self._dialogo_cep = None
        self._dialogo_sexo = None
        self._dialogo_email = None

        # variaveis de marcacao: primeiro as colunas padrao, depois as personalizadas
        for coluna in COLUNAS_DISPONIVEIS:
            self.checkbox_vars[coluna] = tk.IntVar(value=1 if coluna in COLUNAS_PADRAO else 0)
        self.colunas_extras = carregar_colunas_extras()
        for extra in self.colunas_extras:
            self.checkbox_vars[extra["nome"]] = tk.IntVar(value=0)

        self.cpf_sem_pontos_var = tk.IntVar(value=0)
        self.cnpj_sem_pontos_var = tk.IntVar(value=0)

        self._definir_icone()
        self._montar_cabecalho()
        self._montar_abas()
        self._gerar_dado_unico()

    # -- helpers ---------------------------------------------------------
    def _definir_icone(self):
        if not os.path.exists(CAMINHO_LOGO):
            return
        try:
            self._icone = tk.PhotoImage(file=CAMINHO_LOGO)
            # o CustomTkinter troca o icone logo apos abrir; reaplicamos depois
            self.after(300, lambda: self.iconphoto(False, self._icone))
        except tk.TclError:
            pass

    @staticmethod
    def _card(parent):
        return ctk.CTkFrame(
            parent, fg_color=COR_CARD, corner_radius=18, border_width=1, border_color=COR_BORDA
        )

    @staticmethod
    def _titulo_card(parent, texto, subtitulo=None):
        ctk.CTkLabel(
            parent, text=texto, font=(FONTE, 18, "bold"), text_color=COR_PRETO
        ).pack(anchor="w", padx=24, pady=(22, 0 if subtitulo else 12))
        if subtitulo:
            ctk.CTkLabel(
                parent, text=subtitulo, font=(FONTE, 12), text_color=COR_TEXTO_SUAVE
            ).pack(anchor="w", padx=24, pady=(2, 12))

    # -- cabecalho -------------------------------------------------------
    def _montar_cabecalho(self):
        cabecalho = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=0, height=92)
        cabecalho.pack(fill="x")
        cabecalho.pack_propagate(False)

        logo = None
        if os.path.exists(CAMINHO_LOGO):
            try:
                imagem = Image.open(CAMINHO_LOGO)
                self._logo = ctk.CTkImage(light_image=imagem, size=(165, 60))
                logo = ctk.CTkLabel(cabecalho, image=self._logo, text="")
            except OSError:
                logo = None
        if logo is None:
            logo = ctk.CTkLabel(
                cabecalho, text="QAhub", font=(FONTE, 30, "bold"), text_color=COR_LARANJA
            )
        logo.pack(side="left", padx=(32, 22))

        ctk.CTkFrame(cabecalho, fg_color=COR_BORDA, width=1, height=46).pack(side="left")

        textos = ctk.CTkFrame(cabecalho, fg_color="transparent")
        textos.pack(side="left", padx=22)
        ctk.CTkLabel(
            textos, text="Gerador de Massa de Teste", font=(FONTE, 22, "bold"),
            text_color=COR_PRETO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            textos, text="Dados fictícios para acelerar os seus testes de QA",
            font=(FONTE, 13), text_color=COR_TEXTO_SUAVE,
        ).pack(anchor="w")

        ctk.CTkFrame(self, fg_color=COR_LARANJA, height=3, corner_radius=0).pack(fill="x")

    # -- abas ------------------------------------------------------------
    def _montar_abas(self):
        self.abas = ctk.CTkTabview(
            self, fg_color=COR_FUNDO, corner_radius=14,
            segmented_button_fg_color="#E5E7EB",
            segmented_button_selected_color=COR_LARANJA,
            segmented_button_selected_hover_color=COR_LARANJA_HOVER,
            segmented_button_unselected_color="#E5E7EB",
            segmented_button_unselected_hover_color="#D9DCE1",
            text_color=COR_PRETO,
        )
        self.abas.pack(fill="both", expand=True, padx=26, pady=(14, 20))
        try:
            self.abas._segmented_button.configure(font=(FONTE, 14, "bold"), height=38)
        except Exception:
            pass

        self._montar_aba_planilha(self.abas.add("Gerar planilha"))
        self._montar_aba_unico(self.abas.add("Dado único"))

    # =====================================================================
    # ABA 1: GERAR PLANILHA
    # =====================================================================
    def _montar_aba_planilha(self, aba):
        aba.grid_columnconfigure(0, weight=4, minsize=440)
        aba.grid_columnconfigure(1, weight=3, minsize=320)
        aba.grid_columnconfigure(2, weight=3, minsize=320)
        aba.grid_rowconfigure(0, weight=1)

        # ---- card 1: escolha das colunas ----
        esquerdo = self._card(aba)
        esquerdo.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        topo = ctk.CTkFrame(esquerdo, fg_color="transparent")
        topo.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(
            topo, text="Colunas da planilha", font=(FONTE, 18, "bold"), text_color=COR_PRETO
        ).pack(side="left")
        _botao_suave(topo, "Limpar", self._limpar_selecao, largura=80).pack(side="right")
        _botao_suave(
            topo, "Selecionar todas", self._selecionar_todas, largura=130
        ).pack(side="right", padx=(0, 8))

        _botao_suave(
            esquerdo, "＋  Nova coluna personalizada",
            lambda: self._abrir_dialogo_coluna_extra(), largura=200, altura=36,
        ).pack(fill="x", padx=24, pady=(2, 6))

        self.grade = ctk.CTkScrollableFrame(esquerdo, fg_color="transparent")
        self.grade.pack(fill="both", expand=True, padx=(16, 8), pady=(4, 14))
        self.grade.grid_columnconfigure((0, 1), weight=1, uniform="col")
        self._montar_grade()

        # ---- card 2: ordem das colunas ----
        meio = self._card(aba)
        meio.grid(row=0, column=1, sticky="nsew", padx=8, pady=4)
        self._titulo_card(meio, "Ordem na planilha")

        aviso = ctk.CTkFrame(meio, fg_color=COR_LARANJA_CLARO, corner_radius=12)
        aviso.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(
            aviso,
            text="ℹ  As colunas ficam na planilha na ordem em que você as seleciona. "
                 "Use ▲ e ▼ para reorganizar.",
            font=(FONTE, 12), text_color=COR_LARANJA_HOVER, wraplength=232, justify="left",
        ).pack(padx=12, pady=10, anchor="w")

        self.lista_ordem = ctk.CTkScrollableFrame(meio, fg_color="transparent")
        self.lista_ordem.pack(fill="both", expand=True, padx=(14, 8), pady=(0, 14))

        # ---- card 3: configuracao (com area rolavel) ----
        direito = self._card(aba)
        direito.grid(row=0, column=2, sticky="nsew", padx=(8, 0), pady=4)

        self._titulo_card(direito, "Configuração")

        rodape = ctk.CTkFrame(direito, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=24, pady=(4, 22))
        self.contagem_label = ctk.CTkLabel(
            rodape, text="", font=(FONTE, 12), text_color=COR_TEXTO_SUAVE
        )
        self.contagem_label.pack(pady=(0, 8))
        self.gerar_btn = _botao_principal(rodape, "Gerar planilha", self._gerar_planilha)
        self.gerar_btn.pack(fill="x")
        self.status_label = ctk.CTkLabel(rodape, text="", font=(FONTE, 12), text_color=COR_SUCESSO)
        self.status_label.pack(pady=(10, 0))

        conteudo = ctk.CTkScrollableFrame(direito, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=(6, 2), pady=(0, 4))

        ctk.CTkLabel(
            conteudo, text="Quantidade de registros", font=(FONTE, 13, "bold"),
            text_color=COR_PRETO,
        ).pack(anchor="w", padx=18)
        self.qtd_entry = ctk.CTkEntry(
            conteudo, height=42, corner_radius=10, font=(FONTE, 15),
            border_color=COR_BORDA, fg_color=COR_FUNDO, text_color=COR_PRETO, justify="center",
        )
        self.qtd_entry.insert(0, "100")
        self.qtd_entry.pack(fill="x", padx=18, pady=(6, 2))
        ctk.CTkLabel(
            conteudo, text="Número de linhas que a planilha terá",
            font=(FONTE, 11), text_color=COR_TEXTO_SUAVE,
        ).pack(anchor="w", padx=18)

        self.com_titulo_var = tk.IntVar(value=1)
        _checkbox_padrao(
            conteudo, "Incluir título na planilha", self.com_titulo_var, negrito=True
        ).pack(anchor="w", padx=18, pady=(18, 2))
        ctk.CTkLabel(
            conteudo, text="Primeira linha com o nome de cada coluna.\nDesmarque para gerar só os dados.",
            font=(FONTE, 11), text_color=COR_TEXTO_SUAVE, justify="left",
        ).pack(anchor="w", padx=18)

        def _separador():
            ctk.CTkFrame(conteudo, fg_color=COR_BORDA, height=1).pack(fill="x", padx=18, pady=16)

        _separador()

        # -- Data de nascimento / Idade --
        ctk.CTkLabel(
            conteudo, text="Data de nascimento / Idade", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).pack(anchor="w", padx=18)
        self.resumo_nascimento = ctk.CTkLabel(
            conteudo, text="", font=(FONTE, 13), text_color=COR_TEXTO_SUAVE,
            wraplength=270, justify="left",
        )
        self.resumo_nascimento.pack(anchor="w", padx=18, pady=(4, 8))
        _botao_suave(
            conteudo, "Alterar limite", self._abrir_config_nascimento, largura=140, altura=34
        ).pack(anchor="w", padx=18)
        self._atualizar_resumo_nascimento()

        _separador()

        # -- Senha --
        ctk.CTkLabel(
            conteudo, text="Senha", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).pack(anchor="w", padx=18)
        self.resumo_senha_label = ctk.CTkLabel(
            conteudo, text="", font=(FONTE, 13), text_color=COR_TEXTO_SUAVE,
            wraplength=270, justify="left",
        )
        self.resumo_senha_label.pack(anchor="w", padx=18, pady=(4, 8))
        _botao_suave(
            conteudo, "Alterar regras", lambda: self._abrir_config_senha(), largura=140, altura=34
        ).pack(anchor="w", padx=18)
        self._atualizar_resumo_senha()

        _separador()

        # -- Estados --
        ctk.CTkLabel(
            conteudo, text="Estados incluídos (Estado UF)", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).pack(anchor="w", padx=18)
        self.resumo_estados_label = ctk.CTkLabel(
            conteudo, text="", font=(FONTE, 13), text_color=COR_TEXTO_SUAVE,
            wraplength=270, justify="left",
        )
        self.resumo_estados_label.pack(anchor="w", padx=18, pady=(4, 8))
        _botao_suave(
            conteudo, "Alterar estados", self._abrir_config_estados, largura=140, altura=34
        ).pack(anchor="w", padx=18)
        self._atualizar_resumo_estados()

        _separador()

        # -- Cidade --
        ctk.CTkLabel(
            conteudo, text="Cidade", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).pack(anchor="w", padx=18)
        self.resumo_cidades_label = ctk.CTkLabel(
            conteudo, text="", font=(FONTE, 13), text_color=COR_TEXTO_SUAVE,
            wraplength=270, justify="left",
        )
        self.resumo_cidades_label.pack(anchor="w", padx=18, pady=(4, 8))
        _botao_suave(
            conteudo, "Alterar cidades", self._abrir_config_cidades, largura=140, altura=34
        ).pack(anchor="w", padx=18)
        self._atualizar_resumo_cidades()

        _separador()

        # -- CEP --
        ctk.CTkLabel(
            conteudo, text="CEP", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).pack(anchor="w", padx=18)
        self.resumo_cep_label = ctk.CTkLabel(
            conteudo, text="", font=(FONTE, 13), text_color=COR_TEXTO_SUAVE,
            wraplength=270, justify="left",
        )
        self.resumo_cep_label.pack(anchor="w", padx=18, pady=(4, 8))
        _botao_suave(
            conteudo, "Alterar faixa", self._abrir_config_cep, largura=140, altura=34
        ).pack(anchor="w", padx=18)
        self._atualizar_resumo_cep()

        _separador()

        # -- Sexo --
        ctk.CTkLabel(
            conteudo, text="Nome / Sexo", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).pack(anchor="w", padx=18)
        self.resumo_sexo_label = ctk.CTkLabel(
            conteudo, text="", font=(FONTE, 13), text_color=COR_TEXTO_SUAVE,
            wraplength=270, justify="left",
        )
        self.resumo_sexo_label.pack(anchor="w", padx=18, pady=(4, 8))
        _botao_suave(
            conteudo, "Alterar", self._abrir_config_sexo, largura=140, altura=34
        ).pack(anchor="w", padx=18)
        self._atualizar_resumo_sexo()

        _separador()

        # -- E-mail --
        ctk.CTkLabel(
            conteudo, text="E-mail", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).pack(anchor="w", padx=18)
        self.resumo_email_label = ctk.CTkLabel(
            conteudo, text="", font=(FONTE, 13), text_color=COR_TEXTO_SUAVE,
            wraplength=270, justify="left",
        )
        self.resumo_email_label.pack(anchor="w", padx=18, pady=(4, 8))
        _botao_suave(
            conteudo, "Alterar domínio", self._abrir_config_email, largura=140, altura=34
        ).pack(anchor="w", padx=18)
        self._atualizar_resumo_email()

        _separador()

        # -- Duplicatas propositais --
        ctk.CTkLabel(
            conteudo, text="Duplicatas propositais", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).pack(anchor="w", padx=18)
        ctk.CTkLabel(
            conteudo, text="Repete linhas inteiras de propósito, para testar detecção de duplicidade.",
            font=(FONTE, 11), text_color=COR_TEXTO_SUAVE, wraplength=270, justify="left",
        ).pack(anchor="w", padx=18, pady=(2, 8))
        _checkbox_padrao(
            conteudo, "Incluir duplicatas propositais", self.duplicatas_ativo,
            comando=self._atualizar_resumo_duplicatas,
        ).pack(anchor="w", padx=18)
        linha_dup = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha_dup.pack(anchor="w", padx=18, pady=(8, 0))
        ctk.CTkLabel(
            linha_dup, text="Quantidade de linhas duplicadas:", font=(FONTE, 12), text_color=COR_PRETO
        ).pack(side="left")
        self.qtd_duplicatas_entry = ctk.CTkEntry(
            linha_dup, height=32, width=70, corner_radius=8, font=(FONTE, 13), justify="center",
            border_color=COR_BORDA, fg_color=COR_FUNDO, text_color=COR_PRETO,
        )
        self.qtd_duplicatas_entry.insert(0, "5")
        self.qtd_duplicatas_entry.pack(side="left", padx=(8, 0))
        self.resumo_duplicatas_label = ctk.CTkLabel(
            conteudo, text="", font=(FONTE, 11), text_color=COR_TEXTO_SUAVE,
            wraplength=270, justify="left",
        )
        self.resumo_duplicatas_label.pack(anchor="w", padx=18, pady=(6, 0))
        self._atualizar_resumo_duplicatas()

        self._atualizar_contagem()
        self._renderizar_ordem()

    def _atualizar_contagem(self):
        n = len(self.ordem_colunas)
        self.contagem_label.configure(
            text=f"{n} coluna{'s' if n != 1 else ''} selecionada{'s' if n != 1 else ''}"
        )

    def _selecionar_todas(self):
        for coluna, var in self.checkbox_vars.items():
            var.set(1)
            if coluna not in self.ordem_colunas:
                self.ordem_colunas.append(coluna)
        self._atualizar_contagem()
        self._renderizar_ordem()

    def _limpar_selecao(self):
        for var in self.checkbox_vars.values():
            var.set(0)
        self.ordem_colunas.clear()
        self._atualizar_contagem()
        self._renderizar_ordem()

    # ---- grade de colunas (padrao + personalizadas) ----
    def _checkbox_coluna(self, parent, coluna):
        return _checkbox_padrao(
            parent, coluna, self.checkbox_vars[coluna],
            comando=lambda c=coluna: self._ao_alternar_coluna(c),
        )

    def _montar_grade(self):
        for filho in self.grade.winfo_children():
            filho.destroy()

        por_coluna = -(-len(COLUNAS_DISPONIVEIS) // 2)  # divisao para cima
        for i, coluna in enumerate(COLUNAS_DISPONIVEIS):
            celula = ctk.CTkFrame(self.grade, fg_color="transparent")
            celula.grid(row=i % por_coluna, column=i // por_coluna, sticky="w", pady=4, padx=(0, 10))
            self._checkbox_coluna(celula, coluna).pack(side="left")

            if coluna in ("Data de nascimento", "Idade"):
                _gear(celula, self._abrir_config_nascimento).pack(side="left", padx=(6, 0))
            elif coluna in ("Nome completo", "Sexo"):
                _gear(celula, self._abrir_config_sexo).pack(side="left", padx=(6, 0))
            elif coluna == "Senha":
                _gear(celula, self._abrir_config_senha).pack(side="left", padx=(6, 0))
            elif coluna == "Estado (UF)":
                _gear(celula, self._abrir_config_estados).pack(side="left", padx=(6, 0))
            elif coluna == "Cidade":
                _gear(celula, self._abrir_config_cidades).pack(side="left", padx=(6, 0))
            elif coluna == "CEP":
                _gear(celula, self._abrir_config_cep).pack(side="left", padx=(6, 0))
            elif coluna == "E-mail":
                _gear(celula, self._abrir_config_email).pack(side="left", padx=(6, 0))
            elif coluna == "CPF":
                ctk.CTkCheckBox(
                    celula, text="sem pontos", variable=self.cpf_sem_pontos_var,
                    fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, border_color="#9CA3AF",
                    checkmark_color="white", text_color=COR_TEXTO_SUAVE, font=(FONTE, 11),
                    checkbox_width=16, checkbox_height=16, corner_radius=4,
                ).pack(side="left", padx=(6, 0))
            elif coluna == "CNPJ":
                ctk.CTkCheckBox(
                    celula, text="sem pontos", variable=self.cnpj_sem_pontos_var,
                    fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, border_color="#9CA3AF",
                    checkmark_color="white", text_color=COR_TEXTO_SUAVE, font=(FONTE, 11),
                    checkbox_width=16, checkbox_height=16, corner_radius=4,
                ).pack(side="left", padx=(6, 0))

        linha = por_coluna
        ctk.CTkFrame(self.grade, fg_color=COR_BORDA, height=1).grid(
            row=linha, column=0, columnspan=2, sticky="ew", pady=(12, 10)
        )
        ctk.CTkLabel(
            self.grade, text="Colunas personalizadas", font=(FONTE, 13, "bold"),
            text_color=COR_PRETO,
        ).grid(row=linha + 1, column=0, columnspan=2, sticky="w")

        if not self.colunas_extras:
            ctk.CTkLabel(
                self.grade, text="Nenhuma ainda. Use o botão acima para criar a sua.",
                font=(FONTE, 12), text_color=COR_TEXTO_SUAVE,
            ).grid(row=linha + 2, column=0, columnspan=2, sticky="w", pady=(4, 0))

        for j, extra in enumerate(self.colunas_extras):
            celula = ctk.CTkFrame(self.grade, fg_color="transparent")
            celula.grid(row=linha + 2 + j, column=0, columnspan=2, sticky="w", pady=4)
            self._checkbox_coluna(celula, extra["nome"]).pack(side="left")
            ctk.CTkButton(
                celula, text="✎", width=28, height=28, corner_radius=8,
                fg_color=COR_LARANJA_CLARO, hover_color=COR_LARANJA_CLARO_HOVER,
                text_color=COR_LARANJA_HOVER, font=(FONTE, 14),
                command=lambda e=extra: self._abrir_dialogo_coluna_extra(e),
            ).pack(side="left", padx=(8, 6))
            n = len(extra["valores"])
            ctk.CTkLabel(
                celula, text=f"{n} valor{'es' if n != 1 else ''}",
                font=(FONTE, 11), text_color=COR_TEXTO_SUAVE,
            ).pack(side="left")

    # ---- colunas personalizadas ----
    def _abrir_dialogo_coluna_extra(self, existente=None):
        if self._dialogo_extra is not None and self._dialogo_extra.winfo_exists():
            self._dialogo_extra.focus()
            return

        editar = existente is not None
        d = ctk.CTkToplevel(self)
        self._dialogo_extra = d
        d.title("Editar coluna personalizada" if editar else "Nova coluna personalizada")
        d.configure(fg_color=COR_CARD)
        d.resizable(False, False)
        d.transient(self)
        largura, altura = 500, 620
        x = max(0, self.winfo_x() + (self.winfo_width() - largura) // 2)
        y = max(0, self.winfo_y() + (self.winfo_height() - altura) // 2)
        d.geometry(f"{largura}x{altura}+{x}+{y}")

        botoes = ctk.CTkFrame(d, fg_color="transparent")
        botoes.pack(side="bottom", fill="x", padx=26, pady=(0, 22))

        ctk.CTkLabel(
            d, text="Editar coluna personalizada" if editar else "Nova coluna personalizada",
            font=(FONTE, 18, "bold"), text_color=COR_PRETO,
        ).pack(anchor="w", padx=26, pady=(24, 14))

        ctk.CTkLabel(
            d, text="Nome da coluna", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).pack(anchor="w", padx=26)
        e_nome = ctk.CTkEntry(
            d, height=40, corner_radius=10, font=(FONTE, 14), border_color=COR_BORDA,
            fg_color=COR_FUNDO, text_color=COR_PRETO, placeholder_text="Ex.: Perfil de acesso",
        )
        e_nome.pack(fill="x", padx=26, pady=(6, 14))

        ctk.CTkLabel(
            d, text="Valores possíveis (um por linha)", font=(FONTE, 13, "bold"),
            text_color=COR_PRETO,
        ).pack(anchor="w", padx=26)
        caixa = ctk.CTkTextbox(
            d, height=170, corner_radius=10, border_width=1, border_color=COR_BORDA,
            fg_color=COR_FUNDO, text_color=COR_PRETO, font=(FONTE, 13),
        )
        caixa.pack(fill="x", padx=26, pady=(6, 4))
        ctk.CTkLabel(
            d,
            text="Cada linha é um valor que pode aparecer na coluna. "
                 "Repita um valor para ele sair com mais frequência.",
            font=(FONTE, 11), text_color=COR_TEXTO_SUAVE, wraplength=440, justify="left",
        ).pack(anchor="w", padx=26)

        var_seq = tk.IntVar(value=0)
        _checkbox_padrao(
            d, "Usar os valores em sequência (em vez de sortear)", var_seq
        ).pack(anchor="w", padx=26, pady=(14, 0))
        ctk.CTkLabel(
            d, text="Sequência: 1ª linha = 1º valor, 2ª linha = 2º valor... e volta ao início.",
            font=(FONTE, 11), text_color=COR_TEXTO_SUAVE, wraplength=440, justify="left",
        ).pack(anchor="w", padx=26, pady=(2, 0))

        erro = ctk.CTkLabel(
            d, text="", font=(FONTE, 12), text_color=COR_ERRO, wraplength=440, justify="left"
        )
        erro.pack(anchor="w", padx=26, pady=(10, 0))

        if editar:
            e_nome.insert(0, existente["nome"])
            caixa.insert("1.0", "\n".join(existente["valores"]))
            var_seq.set(1 if existente.get("sequencial") else 0)

        def _salvar():
            usados = set(COLUNAS_DISPONIVEIS) | {
                e["nome"] for e in self.colunas_extras if e is not existente
            }
            valores, msg = validar_coluna_extra(e_nome.get(), caixa.get("1.0", "end"), usados)
            if msg:
                erro.configure(text=msg)
                return
            nova = {
                "nome": e_nome.get().strip(),
                "valores": valores,
                "sequencial": bool(var_seq.get()),
            }
            d.destroy()
            self._salvar_coluna_extra(nova, existente)

        def _excluir():
            if messagebox.askyesno(
                "Excluir coluna", f"Excluir a coluna \"{existente['nome']}\"?", parent=d
            ):
                d.destroy()
                self._excluir_coluna_extra(existente)

        if editar:
            ctk.CTkButton(
                botoes, text="Excluir", width=96, height=40, corner_radius=12,
                fg_color="transparent", border_width=1, border_color="#FCA5A5",
                hover_color="#FEF2F2", text_color=COR_ERRO, font=(FONTE, 13, "bold"),
                command=_excluir,
            ).pack(side="left")
        ctk.CTkButton(
            botoes, text="Salvar", width=130, height=40, corner_radius=12,
            fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color="white",
            font=(FONTE, 13, "bold"), command=_salvar,
        ).pack(side="right")
        ctk.CTkButton(
            botoes, text="Cancelar", width=110, height=40, corner_radius=12,
            fg_color="transparent", border_width=1, border_color=COR_BORDA,
            hover_color=COR_FUNDO, text_color=COR_PRETO, font=(FONTE, 13, "bold"),
            command=d.destroy,
        ).pack(side="right", padx=(0, 8))

        def _prender_foco():
            try:
                d.grab_set()
                e_nome.focus()
            except tk.TclError:
                pass

        d.after(250, _prender_foco)

    def _salvar_coluna_extra(self, nova, antiga=None):
        nome = nova["nome"]
        if antiga is None:
            self.colunas_extras.append(nova)
            self.checkbox_vars[nome] = tk.IntVar(value=1)  # ja entra selecionada
            self.ordem_colunas.append(nome)
        else:
            nome_antigo = antiga["nome"]
            self.colunas_extras[self.colunas_extras.index(antiga)] = nova
            if nome != nome_antigo:  # renomeou: mantem marcacao e posicao na ordem
                self.checkbox_vars[nome] = self.checkbox_vars.pop(nome_antigo)
                if nome_antigo in self.ordem_colunas:
                    self.ordem_colunas[self.ordem_colunas.index(nome_antigo)] = nome
        self._depois_de_mudar_extras()

    def _excluir_coluna_extra(self, extra):
        nome = extra["nome"]
        self.colunas_extras.remove(extra)
        self.checkbox_vars.pop(nome, None)
        if nome in self.ordem_colunas:
            self.ordem_colunas.remove(nome)
        self._depois_de_mudar_extras()

    def _depois_de_mudar_extras(self):
        if not salvar_colunas_extras(self.colunas_extras):
            messagebox.showwarning(
                "Colunas não salvas",
                "Não foi possível gravar as colunas personalizadas nesta pasta. "
                "Elas continuam valendo até você fechar o programa.",
            )
        self._montar_grade()
        self._atualizar_contagem()
        self._renderizar_ordem()

    # ---- ordem das colunas ----
    def _ao_alternar_coluna(self, coluna):
        marcada = bool(self.checkbox_vars[coluna].get())
        if marcada and coluna not in self.ordem_colunas:
            self.ordem_colunas.append(coluna)  # vai para o fim = ordem de selecao
        elif not marcada and coluna in self.ordem_colunas:
            self.ordem_colunas.remove(coluna)
        self._atualizar_contagem()
        self._renderizar_ordem()

        # so abre a caixinha quando o usuario ACABOU de marcar a coluna
        if coluna in ("Data de nascimento", "Idade") and marcada:
            self._abrir_config_nascimento()

    def _renderizar_ordem(self):
        """Reconstroi a lista de ordem (usado quando colunas entram ou saem)."""
        for filho in self.lista_ordem.winfo_children():
            filho.destroy()
        self._linhas_ordem = []

        if not self.ordem_colunas:
            ctk.CTkLabel(
                self.lista_ordem, text="Nenhuma coluna selecionada",
                font=(FONTE, 13), text_color=COR_TEXTO_SUAVE,
            ).pack(pady=28)
            return

        for i in range(len(self.ordem_colunas)):
            linha = ctk.CTkFrame(self.lista_ordem, fg_color=COR_FUNDO, corner_radius=10)
            linha.pack(fill="x", pady=3)
            ctk.CTkLabel(
                linha, text=str(i + 1), width=26, font=(FONTE, 12, "bold"),
                text_color=COR_LARANJA_HOVER,
            ).pack(side="left", padx=(10, 2), pady=6)
            nome = ctk.CTkLabel(
                linha, text="", font=(FONTE, 12), text_color=COR_PRETO, anchor="w"
            )
            nome.pack(side="left", fill="x", expand=True, padx=(2, 4))

            botoes = []
            for simbolo, delta in (("▼", 1), ("▲", -1)):
                b = ctk.CTkButton(
                    linha, text=simbolo, width=26, height=26, corner_radius=8, font=(FONTE, 11),
                    fg_color=COR_LARANJA_CLARO, hover_color=COR_LARANJA_CLARO_HOVER,
                    text_color=COR_LARANJA_HOVER,
                    command=lambda pos=i, d=delta: self._mover_coluna(pos, d),
                )
                b.pack(side="right", padx=(0, 5), pady=6)
                botoes.append(b)
            descer, subir = botoes
            self._linhas_ordem.append((nome, subir, descer))

        self._atualizar_linhas_ordem()

    def _atualizar_linhas_ordem(self):
        """Atualiza textos e setas sem recriar os widgets (evita destruir o botao clicado)."""
        ultimo = len(self.ordem_colunas) - 1
        for i, (nome, subir, descer) in enumerate(self._linhas_ordem):
            nome.configure(text=self.ordem_colunas[i])
            for botao, ativo in ((subir, i > 0), (descer, i < ultimo)):
                botao.configure(
                    state="normal" if ativo else "disabled",
                    fg_color=COR_LARANJA_CLARO if ativo else "transparent",
                    text_color=COR_LARANJA_HOVER if ativo else "#D1D5DB",
                )

    def _mover_coluna(self, posicao, delta):
        destino = posicao + delta
        if 0 <= destino < len(self.ordem_colunas):
            ordem = self.ordem_colunas
            ordem[posicao], ordem[destino] = ordem[destino], ordem[posicao]
            self._atualizar_linhas_ordem()

    def _atualizar_resumo_nascimento(self):
        c = self.config_nascimento
        if c["modo"] == "ano":
            texto = f"Nascidos entre {c['ano_min']} e {c['ano_max']}"
        else:
            texto = f"Pessoas de {c['idade_min']} a {c['idade_max']} anos"
        self.resumo_nascimento.configure(text=texto)

    def _atualizar_resumo_senha(self):
        self.resumo_senha_label.configure(text=resumo_senha(self.config_senha))

    def _atualizar_resumo_estados(self):
        self.resumo_estados_label.configure(text=resumo_estados(self.estados_selecionados))

    def _atualizar_resumo_cidades(self):
        self.resumo_cidades_label.configure(text=resumo_cidades(self.cidades_personalizadas))

    def _atualizar_resumo_cep(self):
        self.resumo_cep_label.configure(text=resumo_cep(self.cep_min, self.cep_max))

    def _atualizar_resumo_sexo(self):
        self.resumo_sexo_label.configure(text=resumo_sexo(self.sexo_fixo))

    def _atualizar_resumo_email(self):
        self.resumo_email_label.configure(text=resumo_email(self.email_dominio))

    def _atualizar_resumo_duplicatas(self):
        try:
            quantidade = int(self.qtd_duplicatas_entry.get())
        except (ValueError, AttributeError):
            quantidade = 0
        self.resumo_duplicatas_label.configure(
            text=resumo_duplicatas(bool(self.duplicatas_ativo.get()), quantidade)
        )

    # ---- caixinha de limite de idade / ano ----
    def _abrir_config_nascimento(self):
        if self._dialogo is not None and self._dialogo.winfo_exists():
            self._dialogo.focus()
            return

        d = ctk.CTkToplevel(self)
        self._dialogo = d
        d.title("Limite da data de nascimento")
        d.configure(fg_color=COR_CARD)
        d.resizable(False, False)
        d.transient(self)
        largura, altura = 460, 350
        x = self.winfo_x() + (self.winfo_width() - largura) // 2
        y = self.winfo_y() + (self.winfo_height() - altura) // 2
        d.geometry(f"{largura}x{altura}+{x}+{y}")

        def _prender_foco():
            try:
                d.grab_set()
                d.focus()
            except tk.TclError:
                pass

        d.after(200, _prender_foco)

        ctk.CTkLabel(
            d, text="Como quer limitar a data de nascimento?\n(vale para \"Data de nascimento\" e \"Idade\")",
            font=(FONTE, 15, "bold"), text_color=COR_PRETO, justify="center",
        ).pack(padx=24, pady=(24, 14))

        modo_atual = self.config_nascimento["modo"]
        seletor = ctk.CTkSegmentedButton(
            d, values=["Por idade", "Por ano de nascimento"],
            selected_color=COR_LARANJA, selected_hover_color=COR_LARANJA_HOVER,
            unselected_color="#E5E7EB", unselected_hover_color="#D9DCE1",
            text_color=COR_PRETO, font=(FONTE, 13, "bold"), height=36,
            command=lambda v: _trocar(v),
        )
        seletor.set("Por idade" if modo_atual == "idade" else "Por ano de nascimento")
        seletor.pack(padx=24, pady=(0, 16))

        def _campo(parent, valor, largura=100):
            entrada = ctk.CTkEntry(
                parent, width=largura, height=38, justify="center", font=(FONTE, 14),
                border_color=COR_BORDA, fg_color=COR_FUNDO, text_color=COR_PRETO,
            )
            entrada.insert(0, str(valor))
            return entrada

        def _rotulo(parent, texto):
            return ctk.CTkLabel(parent, text=texto, font=(FONTE, 13), text_color=COR_PRETO)

        # -- modo idade --
        f_idade = ctk.CTkFrame(d, fg_color="transparent")
        _rotulo(f_idade, "De").pack(side="left", padx=6)
        e_idade_min = _campo(f_idade, self.config_nascimento.get("idade_min", 18))
        e_idade_min.pack(side="left")
        _rotulo(f_idade, "até").pack(side="left", padx=6)
        e_idade_max = _campo(f_idade, self.config_nascimento.get("idade_max", 80))
        e_idade_max.pack(side="left")
        _rotulo(f_idade, "anos").pack(side="left", padx=6)

        # -- modo ano --
        ano_atual = date.today().year
        f_ano = ctk.CTkFrame(d, fg_color="transparent")
        _rotulo(f_ano, "De").pack(side="left", padx=6)
        e_ano_min = _campo(f_ano, self.config_nascimento.get("ano_min", 1990))
        e_ano_min.pack(side="left")
        _rotulo(f_ano, "até").pack(side="left", padx=6)
        e_ano_max = _campo(f_ano, self.config_nascimento.get("ano_max", ano_atual))
        e_ano_max.pack(side="left")

        dica = ctk.CTkLabel(d, text="", font=(FONTE, 12), text_color=COR_TEXTO_SUAVE)
        erro = ctk.CTkLabel(
            d, text="", font=(FONTE, 12), text_color=COR_ERRO, wraplength=400
        )
        botoes = ctk.CTkFrame(d, fg_color="transparent")

        def _trocar(valor):
            if valor == "Por idade":
                f_ano.pack_forget()
                f_idade.pack(before=dica, pady=(0, 6))
                dica.configure(text="Exemplo: de 14 a 64 anos")
            else:
                f_idade.pack_forget()
                f_ano.pack(before=dica, pady=(0, 6))
                dica.configure(text="Exemplo: nascidos de 1990 a 2015")
            erro.configure(text="")

        dica.pack()
        erro.pack(pady=(6, 0))
        botoes.pack(side="bottom", pady=22)
        _trocar(seletor.get())

        def _confirmar():
            try:
                if seletor.get() == "Por idade":
                    minimo, maximo = int(e_idade_min.get()), int(e_idade_max.get())
                    if not (0 <= minimo <= maximo <= 120):
                        raise ValueError("As idades devem ficar entre 0 e 120, com o mínimo menor ou igual ao máximo.")
                    novo = {"modo": "idade", "idade_min": minimo, "idade_max": maximo}
                else:
                    minimo, maximo = int(e_ano_min.get()), int(e_ano_max.get())
                    if not (1900 <= minimo <= maximo <= ano_atual):
                        raise ValueError(f"Os anos devem ficar entre 1900 e {ano_atual}, com o inicial menor ou igual ao final.")
                    novo = {"modo": "ano", "ano_min": minimo, "ano_max": maximo}
            except ValueError as e:
                texto = str(e)
                erro.configure(text=texto if "devem" in texto else "Digite apenas números inteiros.")
                return
            self.config_nascimento = novo
            self._atualizar_resumo_nascimento()
            d.destroy()

        ctk.CTkButton(
            botoes, text="Cancelar", width=120, height=40, corner_radius=12,
            fg_color="transparent", border_width=1, border_color=COR_BORDA,
            hover_color=COR_FUNDO, text_color=COR_PRETO, font=(FONTE, 13, "bold"),
            command=d.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            botoes, text="Salvar", width=140, height=40, corner_radius=12,
            fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color="white",
            font=(FONTE, 13, "bold"), command=_confirmar,
        ).pack(side="left", padx=6)

    # ---- caixinha de regras da senha ----
    def _abrir_config_senha(self, ao_salvar=None):
        """Abre a caixinha de regras da senha. Se ao_salvar for passado, chama
        essa funcao com o novo config ao salvar (usado pela aba Dado unico)."""
        if self._dialogo_senha is not None and self._dialogo_senha.winfo_exists():
            self._dialogo_senha.focus()
            return

        d = ctk.CTkToplevel(self)
        self._dialogo_senha = d
        d.title("Regras da senha")
        d.configure(fg_color=COR_CARD)
        d.resizable(False, False)
        d.transient(self)
        largura, altura = 420, 480
        x = self.winfo_x() + (self.winfo_width() - largura) // 2
        y = self.winfo_y() + (self.winfo_height() - altura) // 2
        d.geometry(f"{largura}x{altura}+{x}+{y}")

        def _prender_foco():
            try:
                d.grab_set()
                d.focus()
            except tk.TclError:
                pass

        d.after(200, _prender_foco)

        ctk.CTkLabel(
            d, text="O que a senha deve ter?", font=(FONTE, 17, "bold"), text_color=COR_PRETO,
        ).pack(padx=24, pady=(24, 16))

        linha_tam = ctk.CTkFrame(d, fg_color="transparent")
        linha_tam.pack(padx=24, fill="x")
        ctk.CTkLabel(
            linha_tam, text="Quantidade de caracteres", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).pack(anchor="w")
        e_tamanho = ctk.CTkEntry(
            linha_tam, height=40, corner_radius=10, font=(FONTE, 14), justify="center",
            border_color=COR_BORDA, fg_color=COR_FUNDO, text_color=COR_PRETO,
        )
        e_tamanho.insert(0, str(self.config_senha.get("length", 10)))
        e_tamanho.pack(fill="x", pady=(6, 16))

        var_upper = tk.IntVar(value=1 if self.config_senha.get("upper_case") else 0)
        var_lower = tk.IntVar(value=1 if self.config_senha.get("lower_case") else 0)
        var_digits = tk.IntVar(value=1 if self.config_senha.get("digits") else 0)
        var_special = tk.IntVar(value=1 if self.config_senha.get("special_chars") else 0)

        opcoes = ctk.CTkFrame(d, fg_color="transparent")
        opcoes.pack(padx=24, fill="x")
        for texto, var in (
            ("Letras maiúsculas (A-Z)", var_upper),
            ("Letras minúsculas (a-z)", var_lower),
            ("Números (0-9)", var_digits),
            ("Caracteres especiais (!@#$...)", var_special),
        ):
            _checkbox_padrao(opcoes, texto, var).pack(anchor="w", pady=4)

        erro = ctk.CTkLabel(
            d, text="", font=(FONTE, 12), text_color=COR_ERRO, wraplength=370, justify="left"
        )
        erro.pack(padx=24, pady=(12, 0), anchor="w")

        botoes = ctk.CTkFrame(d, fg_color="transparent")
        botoes.pack(side="bottom", pady=22)

        def _confirmar():
            try:
                tamanho = int(e_tamanho.get())
                if not (1 <= tamanho <= 128):
                    raise ValueError("O tamanho deve ficar entre 1 e 128 caracteres.")
            except ValueError as e:
                erro.configure(text=str(e) if "deve" in str(e) else "Digite um número inteiro válido.")
                return
            if not (var_upper.get() or var_lower.get() or var_digits.get() or var_special.get()):
                erro.configure(text="Marque pelo menos um tipo de caractere.")
                return
            novo = {
                "length": tamanho,
                "upper_case": bool(var_upper.get()),
                "lower_case": bool(var_lower.get()),
                "digits": bool(var_digits.get()),
                "special_chars": bool(var_special.get()),
            }
            self.config_senha = novo
            self._atualizar_resumo_senha()
            d.destroy()
            if ao_salvar:
                ao_salvar()

        ctk.CTkButton(
            botoes, text="Cancelar", width=120, height=40, corner_radius=12,
            fg_color="transparent", border_width=1, border_color=COR_BORDA,
            hover_color=COR_FUNDO, text_color=COR_PRETO, font=(FONTE, 13, "bold"),
            command=d.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            botoes, text="Salvar", width=140, height=40, corner_radius=12,
            fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color="white",
            font=(FONTE, 13, "bold"), command=_confirmar,
        ).pack(side="left", padx=6)

    # ---- caixinha de estados ----
    def _abrir_config_estados(self):
        if self._dialogo_estados is not None and self._dialogo_estados.winfo_exists():
            self._dialogo_estados.focus()
            return

        d = ctk.CTkToplevel(self)
        self._dialogo_estados = d
        d.title("Estados incluídos")
        d.configure(fg_color=COR_CARD)
        d.resizable(False, False)
        d.transient(self)
        largura, altura = 480, 560
        x = self.winfo_x() + (self.winfo_width() - largura) // 2
        y = self.winfo_y() + (self.winfo_height() - altura) // 2
        d.geometry(f"{largura}x{altura}+{x}+{y}")

        def _prender_foco():
            try:
                d.grab_set()
                d.focus()
            except tk.TclError:
                pass

        d.after(200, _prender_foco)

        ctk.CTkLabel(
            d, text="Quais estados podem aparecer\nna coluna \"Estado (UF)\"?",
            font=(FONTE, 16, "bold"), text_color=COR_PRETO, justify="center",
        ).pack(padx=24, pady=(22, 4))
        ctk.CTkLabel(
            d, text="Deixe todos marcados para não restringir.",
            font=(FONTE, 12), text_color=COR_TEXTO_SUAVE,
        ).pack(pady=(0, 12))

        topo = ctk.CTkFrame(d, fg_color="transparent")
        topo.pack(pady=(0, 8))
        vars_estado: dict[str, tk.IntVar] = {
            sigla: tk.IntVar(value=1 if sigla in self.estados_selecionados else 0)
            for sigla, _nome in ESTADOS_BR
        }

        lista = ctk.CTkScrollableFrame(d, fg_color=COR_FUNDO, corner_radius=12)
        lista.pack(fill="both", expand=True, padx=24, pady=(0, 4))
        lista.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")
        for i, (sigla, nome) in enumerate(ESTADOS_BR):
            ctk.CTkCheckBox(
                lista, text=f"{sigla}", variable=vars_estado[sigla],
                fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, border_color="#9CA3AF",
                checkmark_color="white", text_color=COR_PRETO, font=(FONTE, 13),
                checkbox_width=20, checkbox_height=20, corner_radius=6,
            ).grid(row=i // 3, column=i % 3, sticky="w", padx=10, pady=6)

        def _marcar_todos(valor):
            for var in vars_estado.values():
                var.set(valor)

        _botao_suave(
            topo, "Selecionar todos", lambda: _marcar_todos(1), largura=140
        ).pack(side="left", padx=4)
        _botao_suave(
            topo, "Limpar", lambda: _marcar_todos(0), largura=90
        ).pack(side="left", padx=4)

        erro = ctk.CTkLabel(d, text="", font=(FONTE, 12), text_color=COR_ERRO)
        erro.pack(pady=(4, 0))

        botoes = ctk.CTkFrame(d, fg_color="transparent")
        botoes.pack(side="bottom", pady=16)

        def _confirmar():
            selecionados = {sigla for sigla, var in vars_estado.items() if var.get()}
            if not selecionados:
                erro.configure(text="Selecione pelo menos um estado.")
                return
            self.estados_selecionados = selecionados
            self._atualizar_resumo_estados()
            d.destroy()

        ctk.CTkButton(
            botoes, text="Cancelar", width=120, height=40, corner_radius=12,
            fg_color="transparent", border_width=1, border_color=COR_BORDA,
            hover_color=COR_FUNDO, text_color=COR_PRETO, font=(FONTE, 13, "bold"),
            command=d.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            botoes, text="Salvar", width=140, height=40, corner_radius=12,
            fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color="white",
            font=(FONTE, 13, "bold"), command=_confirmar,
        ).pack(side="left", padx=6)

    # ---- caixinha de cidades personalizadas ----
    def _abrir_config_cidades(self):
        if self._dialogo_cidades is not None and self._dialogo_cidades.winfo_exists():
            self._dialogo_cidades.focus()
            return

        d = ctk.CTkToplevel(self)
        self._dialogo_cidades = d
        d.title("Cidades incluídas")
        d.configure(fg_color=COR_CARD)
        d.resizable(False, False)
        d.transient(self)
        largura, altura = 460, 460
        x = self.winfo_x() + (self.winfo_width() - largura) // 2
        y = self.winfo_y() + (self.winfo_height() - altura) // 2
        d.geometry(f"{largura}x{altura}+{x}+{y}")

        def _prender_foco():
            try:
                d.grab_set()
                d.focus()
            except tk.TclError:
                pass

        d.after(200, _prender_foco)

        ctk.CTkLabel(
            d, text="Quais cidades podem aparecer\nna coluna \"Cidade\"?",
            font=(FONTE, 16, "bold"), text_color=COR_PRETO, justify="center",
        ).pack(padx=24, pady=(22, 4))
        ctk.CTkLabel(
            d, text="Uma cidade por linha. Deixe em branco para não restringir\n"
                    "(qualquer cidade brasileira pode sair).",
            font=(FONTE, 12), text_color=COR_TEXTO_SUAVE, justify="center",
        ).pack(pady=(0, 12))

        caixa = ctk.CTkTextbox(
            d, height=200, corner_radius=10, border_width=1, border_color=COR_BORDA,
            fg_color=COR_FUNDO, text_color=COR_PRETO, font=(FONTE, 13),
        )
        caixa.pack(fill="both", expand=True, padx=24, pady=(0, 4))
        if self.cidades_personalizadas:
            caixa.insert("1.0", "\n".join(self.cidades_personalizadas))

        botoes = ctk.CTkFrame(d, fg_color="transparent")
        botoes.pack(side="bottom", pady=16)

        def _confirmar():
            cidades = [linha.strip() for linha in caixa.get("1.0", "end").splitlines() if linha.strip()]
            self.cidades_personalizadas = cidades
            self._atualizar_resumo_cidades()
            d.destroy()

        ctk.CTkButton(
            botoes, text="Cancelar", width=120, height=40, corner_radius=12,
            fg_color="transparent", border_width=1, border_color=COR_BORDA,
            hover_color=COR_FUNDO, text_color=COR_PRETO, font=(FONTE, 13, "bold"),
            command=d.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            botoes, text="Salvar", width=140, height=40, corner_radius=12,
            fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color="white",
            font=(FONTE, 13, "bold"), command=_confirmar,
        ).pack(side="left", padx=6)

    # ---- caixinha de faixa de CEP ----
    def _abrir_config_cep(self, ao_salvar=None):
        if self._dialogo_cep is not None and self._dialogo_cep.winfo_exists():
            self._dialogo_cep.focus()
            return

        d = ctk.CTkToplevel(self)
        self._dialogo_cep = d
        d.title("Faixa de CEP")
        d.configure(fg_color=COR_CARD)
        d.resizable(False, False)
        d.transient(self)
        largura, altura = 440, 320
        x = self.winfo_x() + (self.winfo_width() - largura) // 2
        y = self.winfo_y() + (self.winfo_height() - altura) // 2
        d.geometry(f"{largura}x{altura}+{x}+{y}")

        def _prender_foco():
            try:
                d.grab_set()
                d.focus()
            except tk.TclError:
                pass

        d.after(200, _prender_foco)

        ctk.CTkLabel(
            d, text="Em que faixa de CEP gerar?", font=(FONTE, 17, "bold"), text_color=COR_PRETO,
        ).pack(padx=24, pady=(24, 6))
        ctk.CTkLabel(
            d, text="8 dígitos, com ou sem traço. Deixe em branco para não restringir.",
            font=(FONTE, 12), text_color=COR_TEXTO_SUAVE, wraplength=380, justify="center",
        ).pack(pady=(0, 16))

        linha = ctk.CTkFrame(d, fg_color="transparent")
        linha.pack()
        ctk.CTkLabel(linha, text="De", font=(FONTE, 13), text_color=COR_PRETO).pack(side="left", padx=6)
        e_min = ctk.CTkEntry(
            linha, width=130, height=38, justify="center", font=(FONTE, 14),
            border_color=COR_BORDA, fg_color=COR_FUNDO, text_color=COR_PRETO,
            placeholder_text="00000-000",
        )
        if self.cep_min is not None:
            e_min.insert(0, f"{self.cep_min:08d}")
        e_min.pack(side="left")
        ctk.CTkLabel(linha, text="até", font=(FONTE, 13), text_color=COR_PRETO).pack(side="left", padx=6)
        e_max = ctk.CTkEntry(
            linha, width=130, height=38, justify="center", font=(FONTE, 14),
            border_color=COR_BORDA, fg_color=COR_FUNDO, text_color=COR_PRETO,
            placeholder_text="99999-999",
        )
        if self.cep_max is not None:
            e_max.insert(0, f"{self.cep_max:08d}")
        e_max.pack(side="left")

        dica = ctk.CTkLabel(
            d, text="Dica: no CEP brasileiro, o primeiro dígito indica a região "
                    "(0-1 SP, 2-3 RJ/ES/MG, 4 BA/SE, 5 PE/AL/PB/RN, 6 Norte/Nordeste, "
                    "7 Centro-Oeste, 8 PR/SC, 9 RS).",
            font=(FONTE, 11), text_color=COR_TEXTO_SUAVE, wraplength=380, justify="left",
        )
        dica.pack(padx=24, pady=(14, 0))

        erro = ctk.CTkLabel(d, text="", font=(FONTE, 12), text_color=COR_ERRO, wraplength=380)
        erro.pack(pady=(8, 0))

        botoes = ctk.CTkFrame(d, fg_color="transparent")
        botoes.pack(side="bottom", pady=16)

        def _confirmar():
            texto_min = re.sub(r"\D", "", e_min.get())
            texto_max = re.sub(r"\D", "", e_max.get())
            if not texto_min and not texto_max:
                self.cep_min = self.cep_max = None
                self._atualizar_resumo_cep()
                d.destroy()
                if ao_salvar:
                    ao_salvar()
                return
            if len(texto_min) != 8 or len(texto_max) != 8:
                erro.configure(text="Preencha os dois CEPs com 8 dígitos, ou deixe os dois em branco.")
                return
            minimo, maximo = int(texto_min), int(texto_max)
            if minimo > maximo:
                erro.configure(text="O CEP inicial deve ser menor ou igual ao final.")
                return
            self.cep_min, self.cep_max = minimo, maximo
            self._atualizar_resumo_cep()
            d.destroy()
            if ao_salvar:
                ao_salvar()

        ctk.CTkButton(
            botoes, text="Cancelar", width=120, height=40, corner_radius=12,
            fg_color="transparent", border_width=1, border_color=COR_BORDA,
            hover_color=COR_FUNDO, text_color=COR_PRETO, font=(FONTE, 13, "bold"),
            command=d.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            botoes, text="Salvar", width=140, height=40, corner_radius=12,
            fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color="white",
            font=(FONTE, 13, "bold"), command=_confirmar,
        ).pack(side="left", padx=6)

    # ---- caixinha de sexo fixo ----
    def _abrir_config_sexo(self):
        if self._dialogo_sexo is not None and self._dialogo_sexo.winfo_exists():
            self._dialogo_sexo.focus()
            return

        d = ctk.CTkToplevel(self)
        self._dialogo_sexo = d
        d.title("Nome e sexo")
        d.configure(fg_color=COR_CARD)
        d.resizable(False, False)
        d.transient(self)
        largura, altura = 400, 300
        x = self.winfo_x() + (self.winfo_width() - largura) // 2
        y = self.winfo_y() + (self.winfo_height() - altura) // 2
        d.geometry(f"{largura}x{altura}+{x}+{y}")

        def _prender_foco():
            try:
                d.grab_set()
                d.focus()
            except tk.TclError:
                pass

        d.after(200, _prender_foco)

        ctk.CTkLabel(
            d, text="Nomes de que sexo gerar?\n(vale para \"Nome completo\" e \"Sexo\")",
            font=(FONTE, 15, "bold"), text_color=COR_PRETO, justify="center",
        ).pack(padx=24, pady=(24, 16))

        var = tk.StringVar(value=self.sexo_fixo or "Ambos")
        opcoes = ctk.CTkFrame(d, fg_color="transparent")
        opcoes.pack()
        for texto in ("Ambos (sorteado)", "Somente feminino", "Somente masculino"):
            valor = {"Ambos (sorteado)": "Ambos", "Somente feminino": "Feminino", "Somente masculino": "Masculino"}[texto]
            ctk.CTkRadioButton(
                opcoes, text=texto, variable=var, value=valor,
                fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color=COR_PRETO,
                font=(FONTE, 13),
            ).pack(anchor="w", pady=6)

        botoes = ctk.CTkFrame(d, fg_color="transparent")
        botoes.pack(side="bottom", pady=22)

        def _confirmar():
            self.sexo_fixo = None if var.get() == "Ambos" else var.get()
            self._atualizar_resumo_sexo()
            d.destroy()

        ctk.CTkButton(
            botoes, text="Cancelar", width=120, height=40, corner_radius=12,
            fg_color="transparent", border_width=1, border_color=COR_BORDA,
            hover_color=COR_FUNDO, text_color=COR_PRETO, font=(FONTE, 13, "bold"),
            command=d.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            botoes, text="Salvar", width=140, height=40, corner_radius=12,
            fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color="white",
            font=(FONTE, 13, "bold"), command=_confirmar,
        ).pack(side="left", padx=6)

    # ---- caixinha de dominio de e-mail ----
    def _abrir_config_email(self, ao_salvar=None):
        if self._dialogo_email is not None and self._dialogo_email.winfo_exists():
            self._dialogo_email.focus()
            return

        d = ctk.CTkToplevel(self)
        self._dialogo_email = d
        d.title("Domínio do e-mail")
        d.configure(fg_color=COR_CARD)
        d.resizable(False, False)
        d.transient(self)
        largura, altura = 420, 260
        x = self.winfo_x() + (self.winfo_width() - largura) // 2
        y = self.winfo_y() + (self.winfo_height() - altura) // 2
        d.geometry(f"{largura}x{altura}+{x}+{y}")

        def _prender_foco():
            try:
                d.grab_set()
                e_dominio.focus()
            except tk.TclError:
                pass

        ctk.CTkLabel(
            d, text="Domínio fixo para o e-mail", font=(FONTE, 16, "bold"), text_color=COR_PRETO,
        ).pack(padx=24, pady=(24, 6))
        ctk.CTkLabel(
            d, text="Deixe em branco para usar domínios aleatórios (ex.: example.org).",
            font=(FONTE, 12), text_color=COR_TEXTO_SUAVE, wraplength=370, justify="center",
        ).pack(pady=(0, 14))

        e_dominio = ctk.CTkEntry(
            d, height=42, corner_radius=10, font=(FONTE, 14), justify="center",
            border_color=COR_BORDA, fg_color=COR_FUNDO, text_color=COR_PRETO,
            placeholder_text="empresa.com.br",
        )
        if self.email_dominio:
            e_dominio.insert(0, self.email_dominio)
        e_dominio.pack(fill="x", padx=24)
        d.after(200, _prender_foco)

        erro = ctk.CTkLabel(d, text="", font=(FONTE, 12), text_color=COR_ERRO, wraplength=370)
        erro.pack(pady=(8, 0))

        botoes = ctk.CTkFrame(d, fg_color="transparent")
        botoes.pack(side="bottom", pady=20)

        def _confirmar():
            dominio = e_dominio.get().strip().lstrip("@")
            if dominio and not re.fullmatch(r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}", dominio):
                erro.configure(text="Digite um domínio válido (ex.: empresa.com.br) ou deixe em branco.")
                return
            self.email_dominio = dominio
            self._atualizar_resumo_email()
            d.destroy()
            if ao_salvar:
                ao_salvar()

        ctk.CTkButton(
            botoes, text="Cancelar", width=120, height=40, corner_radius=12,
            fg_color="transparent", border_width=1, border_color=COR_BORDA,
            hover_color=COR_FUNDO, text_color=COR_PRETO, font=(FONTE, 13, "bold"),
            command=d.destroy,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            botoes, text="Salvar", width=140, height=40, corner_radius=12,
            fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color="white",
            font=(FONTE, 13, "bold"), command=_confirmar,
        ).pack(side="left", padx=6)

    # ---- geracao da planilha ----
    def _gerar_planilha(self):
        colunas = list(self.ordem_colunas)
        if not colunas:
            messagebox.showwarning("Nenhuma coluna selecionada", "Selecione pelo menos uma coluna.")
            return

        texto = self.qtd_entry.get().strip()
        if not texto.isdigit() or int(texto) <= 0:
            messagebox.showwarning("Quantidade inválida", "Digite um número inteiro maior que zero.")
            return
        quantidade = int(texto)

        texto_dup = self.qtd_duplicatas_entry.get().strip()
        if not texto_dup.isdigit():
            messagebox.showwarning("Duplicatas inválidas", "A quantidade de duplicatas deve ser um número inteiro.")
            return
        quantidade_duplicatas = int(texto_dup) if self.duplicatas_ativo.get() else 0

        if quantidade > 50000 and not messagebox.askyesno(
            "Quantidade grande",
            f"Você pediu {quantidade} registros, isso pode demorar um pouco. Continuar?",
        ):
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar planilha de massa de teste",
            defaultextension=".xlsx",
            filetypes=[("Planilha Excel", "*.xlsx")],
            initialfile="massa_teste.xlsx",
        )
        if not caminho:
            return

        self.gerar_btn.configure(state="disabled", text="Gerando...")
        self.status_label.configure(text="")
        self.update_idletasks()

        try:
            extras = {e["nome"]: e for e in self.colunas_extras}
            estados = list(self.estados_selecionados) or None
            registros = [
                gerar_registro(
                    colunas, self.config_nascimento, extras, indice,
                    config_senha=self.config_senha,
                    cpf_sem_pontos=bool(self.cpf_sem_pontos_var.get()),
                    cnpj_sem_pontos=bool(self.cnpj_sem_pontos_var.get()),
                    estados=estados,
                    cidades=self.cidades_personalizadas or None,
                    cep_min=self.cep_min,
                    cep_max=self.cep_max,
                    sexo_fixo=self.sexo_fixo,
                    email_dominio=self.email_dominio or None,
                )
                for indice in range(quantidade)
            ]
            aplicar_duplicatas(registros, quantidade_duplicatas)
            salvar_planilha(
                pd.DataFrame(registros, columns=colunas), caminho,
                com_titulo=bool(self.com_titulo_var.get()),
            )
        except Exception as erro:
            import traceback

            traceback.print_exc()
            self.status_label.configure(text="Falha ao gerar a planilha.", text_color=COR_ERRO)
            messagebox.showerror(
                "Erro ao gerar planilha",
                f"Ocorreu um erro:\n\n{type(erro).__name__}: {erro}\n\nVeja o terminal para mais detalhes.",
            )
            return
        finally:
            self.gerar_btn.configure(state="normal", text="Gerar planilha")

        self.status_label.configure(
            text=f"✓ Planilha gerada com {quantidade} registros", text_color=COR_SUCESSO
        )
        messagebox.showinfo("Concluído", f"Planilha salva em:\n{caminho}\n\n{quantidade} registros gerados.")

    # =====================================================================
    # ABA 2: DADO UNICO
    # =====================================================================
    def _montar_aba_unico(self, aba):
        aba.grid_columnconfigure(0, weight=2, minsize=340)
        aba.grid_columnconfigure(1, weight=3)
        aba.grid_rowconfigure(0, weight=1)

        # ---- card esquerdo: escolha do dado ----
        esquerdo = self._card(aba)
        esquerdo.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)
        esquerdo.grid_columnconfigure(0, weight=1)
        esquerdo.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            esquerdo, text="O que gerar?", font=(FONTE, 18, "bold"), text_color=COR_PRETO
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(22, 12))

        ctk.CTkLabel(
            esquerdo, text="Tipo de dado", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).grid(row=1, column=0, sticky="w", padx=24)
        self.tipo_menu = self._menu(esquerdo, TIPOS_DADO_UNICO, self._ao_trocar_tipo)
        self.tipo_menu.grid(row=2, column=0, sticky="ew", padx=24, pady=(6, 0))

        # -- opcoes que variam conforme o tipo escolhido --
        self.opcoes_unico = ctk.CTkFrame(esquerdo, fg_color="transparent")
        self.opcoes_unico.grid(row=3, column=0, sticky="ew", padx=24, pady=(16, 0))

        self.bandeira_box = ctk.CTkFrame(self.opcoes_unico, fg_color="transparent")
        ctk.CTkLabel(
            self.bandeira_box, text="Bandeira", font=(FONTE, 13, "bold"), text_color=COR_PRETO
        ).pack(anchor="w")
        self.bandeira_menu = self._menu(
            self.bandeira_box, list(BANDEIRAS_CARTAO), lambda _: self._gerar_dado_unico()
        )
        self.bandeira_menu.pack(fill="x", pady=(6, 0))

        self.doc_sem_pontos_var = tk.IntVar(value=0)
        self.doc_sem_pontos_box = ctk.CTkFrame(self.opcoes_unico, fg_color="transparent")
        _checkbox_padrao(
            self.doc_sem_pontos_box, "Sem pontuação (só números)", self.doc_sem_pontos_var,
            comando=self._gerar_dado_unico,
        ).pack(anchor="w")

        self.senha_box = ctk.CTkFrame(self.opcoes_unico, fg_color="transparent")
        self.resumo_senha_unico = ctk.CTkLabel(
            self.senha_box, text="", font=(FONTE, 12), text_color=COR_TEXTO_SUAVE,
            wraplength=270, justify="left",
        )
        self.resumo_senha_unico.pack(anchor="w")
        _botao_suave(
            self.senha_box, "Alterar regras",
            lambda: self._abrir_config_senha(ao_salvar=self._ao_salvar_senha_unico),
            largura=140, altura=32,
        ).pack(anchor="w", pady=(6, 0))

        self.cep_box = ctk.CTkFrame(self.opcoes_unico, fg_color="transparent")
        self.resumo_cep_unico = ctk.CTkLabel(
            self.cep_box, text="", font=(FONTE, 12), text_color=COR_TEXTO_SUAVE,
            wraplength=270, justify="left",
        )
        self.resumo_cep_unico.pack(anchor="w")
        _botao_suave(
            self.cep_box, "Alterar faixa",
            lambda: self._abrir_config_cep_unico(),
            largura=140, altura=32,
        ).pack(anchor="w", pady=(6, 0))

        self.email_box = ctk.CTkFrame(self.opcoes_unico, fg_color="transparent")
        self.resumo_email_unico = ctk.CTkLabel(
            self.email_box, text="", font=(FONTE, 12), text_color=COR_TEXTO_SUAVE,
            wraplength=270, justify="left",
        )
        self.resumo_email_unico.pack(anchor="w")
        _botao_suave(
            self.email_box, "Alterar domínio",
            lambda: self._abrir_config_email_unico(),
            largura=140, altura=32,
        ).pack(anchor="w", pady=(6, 0))

        botao = _botao_principal(esquerdo, "Gerar novo", self._gerar_dado_unico)
        botao.grid(row=5, column=0, sticky="ew", padx=24, pady=(20, 24))

        # ---- card direito: resultado ----
        direito = self._card(aba)
        direito.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=4)

        self._titulo_card(direito, "Resultado", subtitulo=" ")
        self.resultado_sub = direito.winfo_children()[-1]

        self.resultado_area = ctk.CTkFrame(direito, fg_color="transparent")
        self.resultado_area.pack(fill="x", padx=24, pady=(4, 20))

    @staticmethod
    def _menu(parent, valores, comando):
        return ctk.CTkOptionMenu(
            parent, values=valores, command=comando, height=42, corner_radius=10,
            fg_color=COR_FUNDO, button_color=COR_LARANJA, button_hover_color=COR_LARANJA_HOVER,
            text_color=COR_PRETO, font=(FONTE, 14), dropdown_font=(FONTE, 13),
            dropdown_fg_color=COR_CARD, dropdown_text_color=COR_PRETO,
            dropdown_hover_color=COR_LARANJA_CLARO, anchor="w",
        )

    def _ao_salvar_senha_unico(self):
        self.resumo_senha_unico.configure(text=resumo_senha(self.config_senha))
        self._gerar_dado_unico()

    def _abrir_config_cep_unico(self):
        self._abrir_config_cep(ao_salvar=self._ao_salvar_cep_unico)

    def _ao_salvar_cep_unico(self):
        self.resumo_cep_unico.configure(text=resumo_cep(self.cep_min, self.cep_max))
        self._gerar_dado_unico()

    def _abrir_config_email_unico(self):
        self._abrir_config_email(ao_salvar=self._ao_salvar_email_unico)

    def _ao_salvar_email_unico(self):
        self.resumo_email_unico.configure(text=resumo_email(self.email_dominio))
        self._gerar_dado_unico()

    def _ao_trocar_tipo(self, tipo):
        for caixa in (self.bandeira_box, self.doc_sem_pontos_box, self.senha_box, self.cep_box, self.email_box):
            caixa.pack_forget()

        if tipo == "Cartão de crédito":
            self.bandeira_box.pack(fill="x")
        elif tipo in ("CPF", "CNPJ"):
            self.doc_sem_pontos_box.pack(fill="x")
        elif tipo == "Senha":
            self.resumo_senha_unico.configure(text=resumo_senha(self.config_senha))
            self.senha_box.pack(fill="x")
        elif tipo == "CEP":
            self.resumo_cep_unico.configure(text=resumo_cep(self.cep_min, self.cep_max))
            self.cep_box.pack(fill="x")
        elif tipo == "E-mail":
            self.resumo_email_unico.configure(text=resumo_email(self.email_dominio))
            self.email_box.pack(fill="x")

        self._gerar_dado_unico()

    def _gerar_dado_unico(self):
        tipo = self.tipo_menu.get()
        bandeira = self.bandeira_menu.get() if tipo == "Cartão de crédito" else None
        try:
            itens = gerar_dado_unico(
                tipo, bandeira,
                sem_pontuacao=bool(self.doc_sem_pontos_var.get()),
                config_senha=self.config_senha,
                cep_min=self.cep_min,
                cep_max=self.cep_max,
                email_dominio=self.email_dominio or None,
            )
        except Exception as erro:
            messagebox.showerror("Erro ao gerar", f"{type(erro).__name__}: {erro}")
            return

        self.resultado_sub.configure(text=f"{tipo} · {bandeira}" if bandeira else tipo)

        for filho in self.resultado_area.winfo_children():
            filho.destroy()

        for rotulo, valor in itens:
            bloco = ctk.CTkFrame(self.resultado_area, fg_color="transparent")
            bloco.pack(fill="x", pady=(0, 14))
            ctk.CTkLabel(
                bloco, text=rotulo.upper(), font=(FONTE, 11, "bold"), text_color=COR_TEXTO_SUAVE
            ).pack(anchor="w")

            linha = ctk.CTkFrame(bloco, fg_color=COR_FUNDO, corner_radius=12)
            linha.pack(fill="x", pady=(4, 0))
            ctk.CTkLabel(
                linha, text=valor, font=(FONTE_MONO, 22, "bold"), text_color=COR_PRETO
            ).pack(side="left", padx=18, pady=14)
            botao = _botao_suave(linha, "Copiar", None, largura=96, altura=34)
            botao.configure(command=lambda v=valor, b=botao: self._copiar(v, b))
            botao.pack(side="right", padx=12)

    def _copiar(self, valor, botao):
        self.clipboard_clear()
        self.clipboard_append(valor)
        botao.configure(text="Copiado ✓")

        def _restaurar():
            try:
                botao.configure(text="Copiar")
            except (tk.TclError, ValueError):
                pass

        self.after(1500, _restaurar)


def main():
    app = GeradorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
