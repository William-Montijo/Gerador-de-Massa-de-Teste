"""
Gerador de Massa de Teste (QAhub)
---------------------------------
Interface Streamlit, cópia da tela do site. Gera planilhas Excel/CSV/JSON
com dados falsos em português do Brasil, um dado único avulso e confere
valores digitados.

Para rodar:
    pip install -r requirements.txt
    streamlit run app.py
"""

from __future__ import annotations

import base64
import html
from datetime import datetime
from pathlib import Path

import streamlit as st

from qahub import brasil, config as cfg_mod, geradores, historico, planilha

st.set_page_config(
    page_title="Gerador de Massa de Teste · QAhub",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Visual (mesmas cores, letras e cartões do site)
# ---------------------------------------------------------------------------

st.html(
    """
<style>
@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&family=Manrope:wght@400;500;600;700&family=Sora:wght@600;700&display=swap");
:root{--bg:#F3F4F6;--card:#FFFFFF;--fg:#181818;--primary:#FD7933;--secondary:#FFEEE2;--muted:#EDEEF0;
      --mutedfg:#6C727E;--accent:#FFE1CC;--accfg:#BD4600;--destr:#DF2225;--border:#E3E4E8;}
#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stToolbar"], [data-testid="stDecoration"] {display:none !important;}
html, body, .stApp, p, span, label, input, textarea, button, li, div {font-family:'Manrope',sans-serif;}
[data-testid="stIconMaterial"], .material-symbols-rounded{font-family:"Material Symbols Rounded" !important;}
[data-testid="stMainBlockContainer"]{padding-top:0 !important;}
.stApp{background:var(--bg); color:var(--fg);}
.block-container{max-width:1152px !important; padding:0 20px 64px !important;}
.mono, code{font-family:'JetBrains Mono',monospace !important;}
[data-testid="stVerticalBlock"]{gap:.5rem;}
p{margin-bottom:0;}
/* Parágrafo/caption logo acima de um botão: dá o respiro que a linha de texto não tem sozinha */
[data-testid="stMarkdownContainer"] > p:last-child{margin-bottom:10px !important;}
[data-testid="stCaptionContainer"]{margin-bottom:10px !important;}
.subtit{font-size:14px; font-weight:600; margin:0 0 10px !important;}

/* Topo branco de ponta a ponta */
.st-key-topo{background:var(--card); box-shadow:0 0 0 100vmax var(--card); clip-path:inset(0 -100vmax);
  border-bottom:1px solid var(--border); padding:16px 0; margin-bottom:24px;}
.st-key-topo [data-testid="stHorizontalBlock"]{align-items:center;}
.marca{display:flex; align-items:center; gap:16px;}
.marca img{height:40px;}
.marca .nome{border-left:1px solid var(--border); padding-left:16px;}
.marca .nome b{font-family:'Sora',sans-serif; font-size:14px; display:block;}
.marca .nome span{font-size:12px; color:var(--mutedfg);}
.marca .nome .aut{display:block; font-size:11px; font-weight:600; color:var(--fg); margin-top:2px;}
.st-key-abas{display:flex; justify-content:flex-end;}
.st-key-abas [data-testid="stButtonGroup"]{background:var(--muted); border-radius:12px; padding:4px; width:fit-content; margin-left:auto;}
.st-key-abas [data-testid="stButtonGroup"] button{border:none !important; background:transparent !important; color:var(--mutedfg) !important;
  border-radius:8px !important; font-weight:600; padding:8px 16px; min-height:0;}
.st-key-abas [data-testid="stButtonGroup"] button p{font-weight:600; font-size:14px;}
.st-key-abas [data-testid="stButtonGroup"] button:hover{color:var(--fg) !important;}
.st-key-abas [data-testid="stButtonGroup"] button[aria-checked="true"],
.st-key-abas [data-testid="stButtonGroup"] button[kind$="Active"]{background:var(--primary) !important; color:#fff !important; box-shadow:0 1px 3px rgba(0,0,0,.15);}

/* Cartões */
[class*="st-key-card_"]{background:var(--card); border:1px solid var(--border); border-radius:18px; padding:20px;
  box-shadow:0 1px 2px rgba(0,0,0,.04);}
.ctit{font-family:'Sora',sans-serif; font-size:16px; font-weight:700; margin:0;}
.csub{font-size:14px; color:var(--mutedfg); margin:2px 0 8px;}
.vazio{background:var(--muted); border-radius:10px; padding:16px; text-align:center; font-size:14px; color:var(--mutedfg);}

/* Botões */
.stButton button, .stDownloadButton button{border-radius:10px; font-weight:600; border:1px solid var(--border); background:var(--card); color:var(--fg); min-height:36px;}
.stButton button:hover, .stDownloadButton button:hover{background:var(--secondary); border-color:var(--primary); color:var(--fg);}
.stButton button[kind="primary"], .stDownloadButton button[kind="primary"]{background:var(--primary); border-color:var(--primary); color:#fff;}
.stButton button[kind="primary"]:hover, .stDownloadButton button[kind="primary"]:hover{background:#F06A22; color:#fff;}
.stButton button p{font-size:14px;}
[class*="st-key-modelo_"] button{border-color:rgba(253,121,51,.4); font-size:13px; min-height:32px; padding:4px 10px;}
[class*="st-key-modelo_"] button p{font-size:13px; font-weight:500;}
 .st-key-limpar_selecao button{min-height:32px; padding:4px 12px;}
.st-key-limpar_selecao button p{font-size:13px; font-weight:500;}
/* Separa os modelos criados dos botões de ação. */
.seprot{border-top:1px solid var(--border); margin:16px 0 10px; padding-top:12px; font-size:12px; font-weight:700;
  letter-spacing:.05em; text-transform:uppercase; color:var(--mutedfg);}
[class*="st-key-modelox_"] button{border:none; background:transparent; min-height:32px; padding:4px 2px; margin-left:-8px; color:#6C727E;}
[class*="st-key-modelox_"] button:hover{color:#D93D3D;}
.st-key-criar_modelo button{min-height:32px; padding:4px 12px;}
.st-key-criar_modelo button p{font-size:13px; font-weight:500;}
.st-key-todas button, .st-key-limpar_colunas button{background:var(--muted); border-color:var(--muted);}
.st-key-nova_extra button{border-style:dashed; border-color:rgba(253,121,51,.5); color:var(--accfg);}
.st-key-gerar_xlsx button{min-height:48px;}
.st-key-gerar_xlsx button p{font-size:16px; font-weight:700;}

/* Linhas de coluna (laranja claro quando marcadas) */
[class*="st-key-linha_"]{border:1px solid transparent; border-radius:10px; padding:6px 10px; min-height:44px; justify-content:center;}
[class*="st-key-linha_"]:hover{background:var(--muted);}
[class*="st-key-linha_"]:has(input[type="checkbox"]:checked){background:var(--secondary); border-color:rgba(253,121,51,.4);}
[class*="st-key-linha_"] [data-testid="stHorizontalBlock"]{align-items:center; gap:4px; flex-wrap:nowrap;}
[class*="st-key-linha_"] [data-testid="stCheckbox"] p{font-size:14px; font-weight:500;}
[class*="st-key-linha_"] .stButton button, [class*="st-key-ord_"] .stButton button{border:none; background:transparent; min-height:28px; padding:2px 6px; color:var(--mutedfg);}
[class*="st-key-linha_"] .stButton button:hover, [class*="st-key-ord_"] .stButton button:hover{background:var(--accent); color:var(--accfg);}
.resumo{font-size:12px !important; color:var(--mutedfg); margin:-12px 0 0 28px !important; line-height:1.2 !important;}
[class*="st-key-semp_"] p{white-space:nowrap; font-size:12px !important; color:var(--mutedfg); font-weight:400 !important;}
/* Título e "sem pontos" grudados: cada um ocupa só o seu espaço, a engrenagem fica no fim da linha. */
[class*="st-key-par_"]{gap:10px !important;}
[class*="st-key-par_"] > [data-testid="stElementContainer"]{flex:0 1 auto; min-width:0;}
/* Nome longo de coluna personalizada: quebra a linha em vez de passar por cima da engrenagem. */
[class*="st-key-par_"] [data-testid="stCheckbox"] label{max-width:100%; min-width:0;}
[class*="st-key-par_"] [data-testid="stCheckbox"] p{min-width:0; white-space:normal; overflow-wrap:anywhere;}
[data-testid="stCheckbox"] [data-baseweb="checkbox"] > span:first-child, [data-testid="stCheckbox"] label > span:first-child{border-radius:50%;}
.st-key-colunas_grade [data-testid="stHorizontalBlock"]{gap:6px;}

/* Ordem na planilha */
[class*="st-key-ord_"]{background:var(--muted); border-radius:10px; padding:2px 8px;}
[class*="st-key-ord_"] [data-testid="stHorizontalBlock"]{align-items:center; gap:2px; flex-wrap:nowrap;}
.onum{line-height:1.2; font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--mutedfg); text-align:right; display:block;}
.onome{line-height:1.2; font-size:14px; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; display:block;}

/* Prévia */
.previa{overflow-x:auto; border:1px solid var(--border); border-radius:10px;}
.previa table{width:100%; border-collapse:collapse; font-size:12px; text-align:left;}
.previa th{background:var(--secondary); color:var(--accfg); font-weight:600; white-space:nowrap; padding:8px 12px;}
.previa td{font-family:'JetBrains Mono',monospace; white-space:nowrap; padding:6px 12px; border-top:1px solid var(--border);}

/* Histórico */
[class*="st-key-hist_"]{border:1px solid var(--border); border-radius:10px; padding:6px 12px;}
[class*="st-key-hist_"] [data-testid="stHorizontalBlock"]{align-items:center;}
.hnome{font-size:14px; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.hinfo{font-size:12px; color:var(--mutedfg);}

/* Sujeira */
[class*="st-key-suj_"] [data-testid="stHorizontalBlock"]{align-items:center;}
.sdica{font-size:12px !important; color:var(--mutedfg); margin:-14px 0 6px 28px !important; line-height:1.2 !important;}

/* Dado único e validador */
[class*="st-key-res_"]{background:var(--secondary); border:1px solid rgba(253,121,51,.3); border-radius:14px; padding:10px 16px;}
[class*="st-key-res_"] [data-testid="stHorizontalBlock"]{align-items:center;}
.rrot{font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.04em; color:var(--accfg);}
.rval{font-family:'JetBrains Mono',monospace; font-size:20px; font-weight:500; word-break:break-all;}
.val{display:flex; gap:12px; align-items:flex-start; border-radius:14px; border:1px solid; padding:12px 16px; margin-top:8px;}
.val.ok{border-color:rgba(253,121,51,.4); background:var(--secondary);}
.val.no{border-color:rgba(223,34,37,.4); background:rgba(223,34,37,.05);}
.val .ic{width:20px; height:20px; border-radius:50%; color:#fff; font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:2px;}
.val.ok .ic{background:var(--primary);} .val.no .ic{background:var(--destr);}
.val .v{font-family:'JetBrains Mono',monospace; font-size:14px; font-weight:500; word-break:break-all;}
.val .m{font-size:12px; color:var(--mutedfg);}
.rodape{margin-top:32px; text-align:center; font-size:12px; color:var(--mutedfg);}

/* Campos */
[data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"], .stTextArea [data-baseweb="base-input"], .stSelectbox [data-baseweb="select"] > div{border:1px solid var(--border) !important; border-radius:8px !important; background:var(--card) !important;}
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div{border:1px solid var(--border) !important; background:var(--card) !important; border-radius:8px !important;}
[data-baseweb="input"] > div, [data-baseweb="input"] input{background:var(--card) !important;}
[class*="st-key-ord_"] [data-testid="stMarkdown"], [class*="st-key-ord_"] [data-testid="stMarkdownContainer"]{display:flex; align-items:center; min-height:28px; margin:0 !important;}
[class*="st-key-ord_"] .stElementContainer{margin:0 !important;}
.stTextInput input, .stNumberInput input, .stTextArea textarea{border-radius:8px;}
[data-testid="stWidgetLabel"] p{font-size:14px; font-weight:500;}
</style>
""",
    )

# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

st.session_state.setdefault("cfg", cfg_mod.config_inicial())
st.session_state.setdefault("extras", cfg_mod.carregar_extras())
st.session_state.setdefault("modelos", cfg_mod.carregar_modelos())
st.session_state.setdefault("historico", [])
st.session_state.setdefault("banco_linhas", {})
st.session_state.setdefault("aba", "Gerar planilha")
CFG: dict = st.session_state["cfg"]
EXTRAS: list = st.session_state["extras"]
CFG["extras"] = EXTRAS
ORDEM: list = CFG["colunas"]
NOMES_EXTRAS = [e["nome"] for e in EXTRAS]
TODAS = list(geradores.COLUNAS_DISPONIVEIS) + NOMES_EXTRAS
NOMES_FORMATO = {"xlsx": "Excel", "csv": "CSV", "json": "JSON"}
SUJEIRA_EXIGE = {"cpf_repetido": "CPF", "email_variacao": "E-mail"}
SUJEIRA_TEXTO = {
    "duplicadas": ("Linhas duplicadas", "Cópia exata de outra linha"),
    "cpf_repetido": ("Mesmo CPF, nome diferente", "Repete o CPF de outra linha"),
    "email_variacao": ("E-mail com caixa diferente", "MAIÚSCULO, com espaços ou @ solto"),
    "espacos": ("Espaços sobrando", "Espaços no começo e no fim de um campo"),
    "vazios": ("Campo vazio", "Deixa um campo em branco na linha"),
    "linha_branca": ("Linha em branco", "Insere uma linha sem nada"),
}


def _numero(texto) -> float | None:
    """Lê um número escrito em português: 1.500,00, 1500, 1500.00."""
    if texto is None:
        return None
    t = str(texto).strip().replace("R$", "").replace(" ", "")
    if not t:
        return None
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _real(x: float) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _milhar(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".") if float(x).is_integer() else _real(x)


def _cep_fmt(x) -> str:
    s = str(int(x)).zfill(8)
    return f"{s[:5]}-{s[5:]}"


def _ck(c: str) -> str:
    return f"chk_{TODAS.index(c) if c in TODAS else abs(hash(c))}"


# Checkbox de cada coluna sempre reflete a ordem atual (modelos, Todas, Limpar, ✕).
for _c in TODAS:
    st.session_state[_ck(_c)] = _c in ORDEM


# ---------------------------------------------------------------------------
# Ações
# ---------------------------------------------------------------------------

def _set_ordem(nova: list[str]) -> None:
    CFG["colunas"] = list(nova)


def _alternar(c: str) -> None:
    marcado = st.session_state.get(_ck(c), False)
    ordem = list(CFG["colunas"])
    tinha_nasc = any(x in ("Data de nascimento", "Idade") for x in ordem)
    if marcado and c not in ordem:
        ordem.append(c)
        if c in ("Data de nascimento", "Idade") and not tinha_nasc:
            st.session_state["abrir"] = "nasc"
    elif not marcado:
        ordem = [x for x in ordem if x != c]
    _set_ordem(ordem)


def _aplicar_modelo(nome: str) -> None:
    m = next((x for x in st.session_state["modelos"] if x["nome"] == nome), None)
    extras = {e["nome"] for e in EXTRAS}
    cols = [c for c in (m["colunas"] if m else []) if c in geradores.COLUNAS_DISPONIVEIS or c in extras]
    _set_ordem(cols)
    if "Data de nascimento" in cols or "Idade" in cols:
        st.session_state["abrir"] = "nasc"


def _excluir_modelo(nome: str) -> None:
    st.session_state["modelos"] = [m for m in st.session_state["modelos"] if m["nome"] != nome]
    cfg_mod.salvar_modelos(st.session_state["modelos"])


def _mover(i: int, d: int) -> None:
    n = list(CFG["colunas"])
    if 0 <= i + d < len(n):
        n[i], n[i + d] = n[i + d], n[i]
        _set_ordem(n)


def _remover(c: str) -> None:
    _set_ordem([x for x in CFG["colunas"] if x != c])


def _abrir(qual: str, editar: str | None = None) -> None:
    st.session_state["abrir"] = qual
    st.session_state["editando"] = editar


def _excluir_hist(token: int) -> None:
    st.session_state["historico"] = [h for h in st.session_state["historico"] if h["token"] != token]


def _ir_aba() -> None:
    if not st.session_state.get("abas_nav"):
        st.session_state["abas_nav"] = st.session_state["aba"]
    st.session_state["aba"] = st.session_state["abas_nav"]


# ---------------------------------------------------------------------------
# Janelas (as engrenagens do site)
# ---------------------------------------------------------------------------

def _botoes_janela(salvar) -> None:
    _, a, b = st.columns([2, 1, 1.2])
    if a.button("Cancelar", key="dlg_cancelar", width="stretch"):
        st.rerun()
    if b.button("Confirmar", key="dlg_ok", type="primary", width="stretch"):
        if salvar() is not False:
            st.rerun()


@st.dialog("Limite da data de nascimento")
def dlg_nasc():
    st.caption("Vale para as colunas Data de nascimento e Idade.")
    n = CFG["nascimento"]
    modo = st.segmented_control("Modo", ["Por idade", "Por ano de nascimento"], key="dn_modo",
                                default="Por idade" if n.get("modo", "idade") == "idade" else "Por ano de nascimento",
                                label_visibility="collapsed", width="stretch") or "Por idade"
    a, b = st.columns(2)
    if modo == "Por idade":
        mn = a.number_input("De (anos)", 0, 120, int(n.get("idade_min", 18)))
        mx = b.number_input("até (anos)", 0, 120, int(n.get("idade_max", 80)))
    else:
        mn = a.number_input("De (ano)", 1900, 2100, int(n.get("ano_min", 1950)))
        mx = b.number_input("até (ano)", 1900, 2100, int(n.get("ano_max", 2008)))

    def salvar():
        if mn > mx:
            st.error("O início não pode ser maior que o fim.")
            return False
        if modo == "Por idade":
            CFG["nascimento"] = {**n, "modo": "idade", "idade_min": int(mn), "idade_max": int(mx)}
        else:
            CFG["nascimento"] = {**n, "modo": "ano", "ano_min": int(mn), "ano_max": int(mx)}
    _botoes_janela(salvar)


@st.dialog("Regras da senha")
def dlg_senha():
    s = CFG["senha"]
    tam = st.number_input("Tamanho", 1, 64, int(s["tamanho"]))
    a, b, c, d = st.columns(4)
    ai = a.checkbox("A-Z", value=bool(s["maiusculas"]))
    az = b.checkbox("a-z", value=bool(s["minusculas"]))
    nu = c.checkbox("0-9", value=bool(s["numeros"]))
    es = d.checkbox("!@#", value=bool(s["especiais"]))

    def salvar():
        if not (ai or az or nu or es):
            st.error("Marque pelo menos um tipo de caractere.")
            return False
        CFG["senha"] = {"tamanho": int(tam), "maiusculas": ai, "minusculas": az, "numeros": nu, "especiais": es}
    _botoes_janela(salvar)


@st.dialog("Estados (UF)", width="medium")
def dlg_estados():
    st.caption("Desmarque os estados que não devem aparecer.")
    atuais = CFG["estados"] or list(brasil.SIGLAS_BR)
    sel = st.pills("Estados", brasil.SIGLAS_BR, selection_mode="multi", default=atuais, label_visibility="collapsed")

    def salvar():
        if not sel:
            st.error("Escolha pelo menos um estado.")
            return False
        CFG["estados"] = [] if len(sel) == len(brasil.SIGLAS_BR) else list(sel)
    _botoes_janela(salvar)


@st.dialog("Cidades", width="medium")
def dlg_cidades():
    st.caption("Vazio = todas. O estado, o CEP e o DDD acompanham a cidade escolhida.")
    sel = st.multiselect("Cidades", sorted(brasil.UF_DA_CIDADE), default=CFG["cidades"], placeholder="Todas as cidades")

    def salvar():
        CFG["cidades"] = list(sel)
    _botoes_janela(salvar)


@st.dialog("Faixa de CEP")
def dlg_cep():
    st.caption("Deixe vazio para usar o CEP da região sorteada.")
    a, b = st.columns(2)
    mn = a.text_input("CEP mínimo", value=_cep_fmt(CFG["cep_min"]) if CFG["cep_min"] is not None else "", placeholder="01000-000")
    mx = b.text_input("CEP máximo", value=_cep_fmt(CFG["cep_max"]) if CFG["cep_max"] is not None else "", placeholder="01999-999")

    def salvar():
        x, y = _numero(mn.replace("-", "")), _numero(mx.replace("-", ""))
        if (x is None) != (y is None) or (x is not None and x > y):
            st.error("Preencha os dois CEPs, com o mínimo menor que o máximo.")
            return False
        CFG["cep_min"], CFG["cep_max"] = x, y
    _botoes_janela(salvar)


@st.dialog("Sexo")
def dlg_sexo():
    st.caption("Vale para Nome completo e Sexo.")
    op = ["Sortear", "Feminino", "Masculino"]
    v = st.radio("Sexo", op, index=op.index(CFG["sexo"]) if CFG["sexo"] in op else 0, label_visibility="collapsed")

    def salvar():
        CFG["sexo"] = None if v == "Sortear" else v
    _botoes_janela(salvar)


@st.dialog("Domínio do e-mail")
def dlg_email():
    v = st.text_input("Domínio fixo", value=CFG["dominio"], placeholder="empresa.com (vazio = sorteia)")

    def salvar():
        CFG["dominio"] = v.strip().lstrip("@")
    _botoes_janela(salvar)


@st.dialog("Criar modelo")
def dlg_modelo():
    st.caption(f"O modelo guarda as {len(CFG['colunas'])} coluna(s) selecionada(s), na ordem atual.")
    nome = st.text_input("Nome do modelo", max_chars=40, placeholder="Cadastro de cliente", key="dlg_modelo_nome")

    def salvar():
        novos, erro = cfg_mod.salvar_modelo(st.session_state["modelos"], nome, list(CFG["colunas"]))
        if erro:
            st.error(erro)
            return False
        st.session_state["modelos"] = novos
        cfg_mod.salvar_modelos(novos)
        st.toast(f'Modelo "{nome.strip()}" salvo.')
    _botoes_janela(salvar)


@st.dialog("Tipo de chave PIX")
def dlg_pix():
    st.caption("A chave usa os dados da própria linha: CPF → o CPF da pessoa, Celular → o celular dela.")
    op = ["Todos (sorteado)"] + [brasil.NOME_TIPO_PIX[t] for t in brasil.TIPOS_PIX]
    idx = 0 if not CFG["pix_tipo"] else brasil.TIPOS_PIX.index(CFG["pix_tipo"]) + 1
    v = st.radio("Tipo", op, index=idx, label_visibility="collapsed")

    def salvar():
        CFG["pix_tipo"] = None if v == op[0] else brasil.TIPOS_PIX[op.index(v) - 1]
    _botoes_janela(salvar)


@st.dialog("Escolaridade")
def dlg_escolar():
    op = ["Todas (sorteado)"] + list(brasil.ESCOLARIDADES)
    idx = 0 if not CFG["escolaridade"] else op.index(CFG["escolaridade"])
    v = st.radio("Escolaridade", op, index=idx, label_visibility="collapsed")

    def salvar():
        CFG["escolaridade"] = None if v == op[0] else v
    _botoes_janela(salvar)


@st.dialog("Faixa de renda mensal")
def dlg_renda():
    st.caption("Em reais. Deixe vazio para sortear entre R$ 1.412 e R$ 30.000.")
    a, b = st.columns(2)
    mn = a.text_input("De (R$)", value=_milhar(CFG["renda_min"]) if CFG["renda_min"] is not None else "", placeholder="1.412")
    mx = b.text_input("Até (R$)", value=_milhar(CFG["renda_max"]) if CFG["renda_max"] is not None else "", placeholder="30.000")

    def salvar():
        x, y = _numero(mn), _numero(mx)
        if (x is None) != (y is None) or (x is not None and x > y):
            st.error("Preencha os dois valores, com o início menor que o fim.")
            return False
        CFG["renda_min"], CFG["renda_max"] = x, y
    _botoes_janela(salvar)


@st.dialog("Valor")
def dlg_valor():
    fixo = CFG["valor_fixo"] is not None
    modo = st.segmented_control("Modo", ["Faixa", "Valor fixo"], default="Valor fixo" if fixo else "Faixa",
                                key="dv_modo", label_visibility="collapsed", width="stretch") or "Faixa"
    if modo == "Valor fixo":
        f = st.text_input("Valor fixo (R$)", value=_real(CFG["valor_fixo"]) if fixo else "", placeholder="89,90")
        mn = mx = ""
    else:
        a, b = st.columns(2)
        mn = a.text_input("De (R$)", value=_real(CFG["valor_min"]) if CFG["valor_min"] is not None else "", placeholder="10,00")
        mx = b.text_input("Até (R$)", value=_real(CFG["valor_max"]) if CFG["valor_max"] is not None else "", placeholder="250.000,00")
        f = ""

    def salvar():
        if modo == "Valor fixo":
            v = _numero(f)
            if v is None:
                st.error("Digite o valor.")
                return False
            CFG["valor_fixo"], CFG["valor_min"], CFG["valor_max"] = v, None, None
        else:
            x, y = _numero(mn), _numero(mx)
            if (x is None) != (y is None) or (x is not None and x > y):
                st.error("Preencha os dois valores, com o início menor que o fim.")
                return False
            CFG["valor_fixo"], CFG["valor_min"], CFG["valor_max"] = None, x, y
    _botoes_janela(salvar)


@st.dialog("Coluna personalizada")
def dlg_extra():
    nome_ed = st.session_state.get("editando")
    ex = next((e for e in EXTRAS if e["nome"] == nome_ed), None)
    nome = st.text_input("Nome da coluna", value=ex["nome"] if ex else "", placeholder="Status do pedido")
    valores = st.text_area("Valores possíveis (um por linha)", value="\n".join(ex["valores"]) if ex else "",
                           placeholder="Pendente\nPago\nEntregue", height=130)
    seq = st.checkbox("Em sequência (na ordem da lista)", value=bool(ex and ex["sequencial"]))

    def salvar():
        usados = [c for c in TODAS if c != (ex["nome"] if ex else None)]
        r = geradores.validar_coluna_extra(nome, valores, usados)
        if r.get("erro"):
            st.error(r["erro"])
            return False
        novo = {"nome": nome.strip(), "valores": r["valores"], "sequencial": bool(seq)}
        if ex:
            EXTRAS[EXTRAS.index(ex)] = novo
            _set_ordem([novo["nome"] if x == ex["nome"] else x for x in CFG["colunas"]])
        else:
            EXTRAS.append(novo)
        cfg_mod.salvar_extras(EXTRAS)

    if ex:
        a, _, b, c = st.columns([1.2, 0.8, 1, 1.2])
        if a.button("Excluir", key="dlg_excluir", width="stretch"):
            EXTRAS.remove(ex)
            cfg_mod.salvar_extras(EXTRAS)
            _set_ordem([x for x in CFG["colunas"] if x != ex["nome"]])
            st.rerun()
        if b.button("Cancelar", key="dlg_cancelar", width="stretch"):
            st.rerun()
        if c.button("Salvar", key="dlg_ok", type="primary", width="stretch"):
            if salvar() is not False:
                st.rerun()
    else:
        _botoes_janela(salvar)


JANELAS = {"nasc": dlg_nasc, "senha": dlg_senha, "estados": dlg_estados, "cidades": dlg_cidades, "cep": dlg_cep,
           "sexo": dlg_sexo, "email": dlg_email, "pix": dlg_pix, "escolar": dlg_escolar, "renda": dlg_renda,
           "valor": dlg_valor, "extra": dlg_extra, "modelo": dlg_modelo}
ENGRENAGEM = {"Data de nascimento": "nasc", "Idade": "nasc", "Senha": "senha", "Estado (UF)": "estados",
              "CPF": "estados", "Telefone": "estados", "Celular": "estados",
              "Cidade": "cidades", "CEP": "cep", "Nome completo": "sexo", "Sexo": "sexo", "E-mail": "email",
              "Escolaridade": "escolar", "Renda mensal": "renda", "Valor": "valor", "PIX": "pix"}

# Colunas que podem sair sem a pontuação de costume, com a etiqueta mostrada na tela.
SEMP_CAMPOS = {
    "CPF": ("cpf_sem_pontos", "sem pontos"),
    "CNPJ": ("cnpj_sem_pontos", "sem pontos"),
    "RG": ("rg_sem_pontos", "sem pontos"),
    "Telefone": ("telefone_sem_pontos", "só números"),
    "Celular": ("celular_sem_pontos", "só números"),
}

# Dados que nascem de uma região: o DDD (e o CEP) vêm do estado escolhido.
REGIAO_TIPOS = ("CPF", "Telefone", "Celular", "CEP", "PIX")


def _resumos() -> dict:
    n = CFG["nascimento"]
    nasc = (f"{n.get('idade_min', 18)} a {n.get('idade_max', 80)} anos" if n.get("modo", "idade") == "idade"
            else f"nascidos de {n.get('ano_min')} a {n.get('ano_max')}")
    s = CFG["senha"]
    tipos = " ".join(t for t, on in (("A-Z", s["maiusculas"]), ("a-z", s["minusculas"]),
                                      ("0-9", s["numeros"]), ("!@#", s["especiais"])) if on)
    sx = f"somente {CFG['sexo'].lower()}" if CFG["sexo"] else None
    est = CFG["estados"]
    cid = CFG["cidades"]
    r = {
        "Data de nascimento": nasc, "Idade": nasc, "Nome completo": sx, "Sexo": sx,
        "Senha": f"{s['tamanho']} caracteres · {tipos}",
        "CPF": None if not est or len(est) == len(brasil.SIGLAS_BR) else "CPF de " + (", ".join(est) if len(est) <= 4 else f"{len(est)} estados"),
        "Estado (UF)": None if not est or len(est) == len(brasil.SIGLAS_BR) else (", ".join(est) if len(est) <= 4 else f"{len(est)} estados"),
        "Telefone": None if not est or len(est) == len(brasil.SIGLAS_BR) else "DDD de " + (", ".join(est) if len(est) <= 4 else f"{len(est)} estados"),
        "Celular": None if not est or len(est) == len(brasil.SIGLAS_BR) else "DDD de " + (", ".join(est) if len(est) <= 4 else f"{len(est)} estados"),
        "Cidade": (", ".join(cid) if len(cid) <= 2 else f"{len(cid)} cidades") if cid else None,
        "CEP": f"{_cep_fmt(CFG['cep_min'])} a {_cep_fmt(CFG['cep_max'])}" if CFG["cep_min"] is not None and CFG["cep_max"] is not None else None,
        "E-mail": f"@{CFG['dominio']}" if CFG["dominio"] else None,
        "PIX": f"somente chave {brasil.NOME_TIPO_PIX[CFG['pix_tipo']].lower()}" if CFG["pix_tipo"] else "tipo sorteado por linha",
        "UUID": "código único aleatório, sem significado",
        "Escolaridade": f"somente {CFG['escolaridade'].lower()}" if CFG["escolaridade"] else None,
        "Renda mensal": f"R$ {_milhar(CFG['renda_min'])} a R$ {_milhar(CFG['renda_max'])}" if CFG["renda_min"] is not None and CFG["renda_max"] is not None else None,
        "Valor": (f"R$ {_real(CFG['valor_fixo'])} em todas as linhas" if CFG["valor_fixo"] is not None
                  else f"R$ {_real(CFG['valor_min'])} a R$ {_real(CFG['valor_max'])}" if CFG["valor_min"] is not None and CFG["valor_max"] is not None else None),
    }
    for e in EXTRAS:
        r[e["nome"]] = f"{len(e['valores'])} valores" + (" · em sequência" if e["sequencial"] else "")
    return r


def _botao_copiar(texto: str, chave: str) -> None:
    """Botão "Copiar" que grava o valor na área de transferência do navegador."""
    payload = base64.b64encode(str(texto).encode("utf-8")).decode("ascii")
    st.components.v1.html(
        """
        <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@600&display=swap" rel="stylesheet">
        <button id="b" style="font-family:Manrope,sans-serif;border:1px solid #E3E4E8;background:#fff;color:#181818;
          border-radius:8px;padding:6px 12px;font-size:13px;font-weight:600;cursor:pointer;width:100%;display:flex;gap:6px;align-items:center;justify-content:center">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          <span>Copiar</span>
        </button>
        <script>
          var V = decodeURIComponent(escape(atob("__VALOR__"))); var b = document.getElementById("b"); var s = b.querySelector("span");
          b.addEventListener("click", function () {
            function ok(){ s.textContent = "Copiado!"; setTimeout(function(){ s.textContent = "Copiar"; }, 1500); }
            function reserva(){ var t=document.createElement("textarea"); t.value=V; document.body.appendChild(t); t.select();
              try{document.execCommand("copy");}catch(e){} document.body.removeChild(t); ok(); }
            if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(V).then(ok, reserva); else reserva();
          });
        </script>
        """.replace("__VALOR__", payload),
        height=40,
    )


def _card(chave: str, titulo: str, sub: str | None = None):
    c = st.container(key=f"card_{chave}")
    c.markdown(f'<p class="ctit">{titulo}</p>' + (f'<p class="csub">{sub}</p>' if sub else '<div style="height:8px"></div>'),
               unsafe_allow_html=True)
    return c


# ---------------------------------------------------------------------------
# Topo
# ---------------------------------------------------------------------------

try:
    _logo = f'<img src="data:image/png;base64,{base64.b64encode(Path("assets/logo-qahub.png").read_bytes()).decode()}" alt="QAhub">'
except Exception:
    _logo = "<b>QAhub</b>"

with st.container(key="topo"):
    t1, t2 = st.columns([1, 1])
    t1.markdown(f'<div class="marca">{_logo}<div class="nome"><b>Gerador de Massa de Teste</b>'
                '<span>Dados fictícios no formato brasileiro</span><span class="aut">Desenvolvido por William Montijo</span></div></div>', unsafe_allow_html=True)
    with t2:
        with st.container(key="abas"):
            st.segmented_control("Aba", ["Gerar planilha", "Gerar dado único"],
                                 default=st.session_state["aba"], key="abas_nav", on_change=_ir_aba,
                                 label_visibility="collapsed")

ABA = st.session_state["aba"]

# ===========================================================================
# GERAR PLANILHA
# ===========================================================================

if ABA == "Gerar planilha":
    esq, dir_ = st.columns([2.15, 1], gap="medium")
    resumo = _resumos()

    with esq:
        with _card("modelos", "Meus modelos", "Selecione as colunas, clique em Criar modelo e dê um nome. Ele aparece aqui para usar com um clique."):
            if st.session_state["modelos"]:
                with st.container(horizontal=True, gap="small"):
                    for i, m in enumerate(st.session_state["modelos"]):
                        st.button(m["nome"], key=f"modelo_{i}", help=f"{len(m['colunas'])} coluna(s)",
                                  on_click=_aplicar_modelo, args=(m["nome"],))
                        st.button("", key=f"modelox_{i}", icon=":material/close:", help=f"Excluir o modelo {m['nome']}",
                                  on_click=_excluir_modelo, args=(m["nome"],))
            else:
                st.markdown('<p class="vazio">Nenhum modelo ainda. Marque colunas e clique em <b>Criar modelo</b> aqui embaixo.</p>',
                            unsafe_allow_html=True)
            st.markdown('<p class="seprot">Seleção atual</p>', unsafe_allow_html=True)
            with st.container(horizontal=True, gap="small", key="acoes_modelo"):
                st.button("Limpar seleção", key="limpar_selecao", icon=":material/close:",
                           type="primary", help="Deixa a planilha sem nenhuma coluna",
                          on_click=_set_ordem, args=([],))
                if st.button("Criar modelo", key="criar_modelo", icon=":material/add:", disabled=not ORDEM,
                             type="primary",
                             help="Salva as colunas selecionadas como modelo"):
                    st.session_state["abrir"] = "modelo"

        with _card("colunas", "Colunas", f"{len(ORDEM)} selecionada(s). Elas entram na planilha na ordem em que você seleciona."):
            b1, b2, b3 = st.columns([6, 0.9, 0.9], vertical_alignment="center")
            busca = b1.text_input("Procurar coluna", placeholder="Procurar coluna...", key="busca",
                                  label_visibility="collapsed", icon=":material/search:")
            b2.button("Todas", key="todas", width="stretch", on_click=_set_ordem, args=(TODAS,))
            b3.button("Limpar", key="limpar_colunas", width="stretch", on_click=_set_ordem, args=([],))

            def linha(c: str, extra: bool = False) -> None:
                with st.container(key=f"linha_{TODAS.index(c)}"):
                    tem_semp = c in SEMP_CAMPOS
                    tem_eng = c in ENGRENAGEM or extra
                    # Título e "sem pontos" na mesma linha, grudados; a engrenagem fica no fim, sempre no mesmo prumo.
                    cols = st.columns([8.6, 1], vertical_alignment="center")
                    with cols[0].container(horizontal=True, gap="small", key=f"par_{TODAS.index(c)}"):
                        st.checkbox(c, key=_ck(c), on_change=_alternar, args=(c,))
                        if tem_semp:
                            campo, rotulo = SEMP_CAMPOS[c]
                            with st.container(key=f"semp_{campo}"):
                                v = st.checkbox(rotulo, value=bool(CFG[campo]), key=f"w_{campo}")
                            CFG[campo] = v
                    if tem_eng:
                        if extra:
                            cols[1].button("", icon=":material/edit:", key=f"eng_{TODAS.index(c)}", help=f"Editar {c}",
                                           on_click=_abrir, args=("extra", c))
                        else:
                            cols[1].button("", icon=":material/settings:", key=f"eng_{TODAS.index(c)}", help=f"Configurar {c}",
                                           on_click=_abrir, args=(ENGRENAGEM[c],))
                    if resumo.get(c):
                        st.markdown(f'<div class="resumo">{html.escape(resumo[c])}</div>', unsafe_allow_html=True)

            filtradas = [c for c in geradores.COLUNAS_DISPONIVEIS if busca.strip().lower() in c.lower()]
            with st.container(key="colunas_grade"):
                for i in range(0, len(filtradas), 2):
                    g1, g2 = st.columns(2)
                    with g1:
                        linha(filtradas[i])
                    if i + 1 < len(filtradas):
                        with g2:
                            linha(filtradas[i + 1])
            if busca and not filtradas:
                st.markdown(f'<div class="vazio">Nenhuma coluna com "{html.escape(busca)}".</div>', unsafe_allow_html=True)

            st.divider()
            st.markdown('<p class="subtit">Colunas personalizadas</p>', unsafe_allow_html=True)
            for i in range(0, len(NOMES_EXTRAS), 2):
                g1, g2 = st.columns(2)
                with g1:
                    linha(NOMES_EXTRAS[i], extra=True)
                if i + 1 < len(NOMES_EXTRAS):
                    with g2:
                        linha(NOMES_EXTRAS[i + 1], extra=True)
            st.button("Nova coluna personalizada", key="nova_extra", icon=":material/add:", on_click=_abrir, args=("extra", None))

        with _card("previa", "Prévia", "8 linhas com as configurações de agora, para conferir antes de baixar."):
            if not ORDEM:
                st.markdown('<div class="vazio">Marque uma coluna para ver a prévia.</div>', unsafe_allow_html=True)
            else:
                opc = cfg_mod.montar_opcoes(CFG)
                # Gera sempre com pontuação e só formata na hora de mostrar: marcar "só números" não troca o número.
                bruto = {**opc, "rg_sem_pontos": False, "telefone_sem_pontos": False, "celular_sem_pontos": False}
                chave = repr((list(ORDEM), sorted((k, repr(v)) for k, v in bruto.items())))
                if st.session_state.get("previa_chave") != chave:
                    st.session_state.previa_chave = chave
                    st.session_state.previa_linhas = [geradores.gerar_registro(list(ORDEM), bruto, i) for i in range(8)]
                fmt = {"RG": opc.get("rg_sem_pontos"), "Telefone": opc.get("telefone_sem_pontos"), "Celular": opc.get("celular_sem_pontos")}
                previa = [{c: geradores.sem_pontuacao(str(v), bool(fmt.get(c))) for c, v in l.items()} for l in st.session_state.previa_linhas]
                cab = "".join(f"<th>{html.escape(c)}</th>" for c in ORDEM)
                corpo = "".join("<tr>" + "".join(f"<td>{html.escape(str(l.get(c, '')))}</td>" for c in ORDEM) + "</tr>" for l in previa)
                st.markdown(f'<div class="previa"><table><thead><tr>{cab}</tr></thead><tbody>{corpo}</tbody></table></div>',
                            unsafe_allow_html=True)

        with _card("historico", "Histórico", "As últimas planilhas geradas nesta sessão."):
            itens = st.session_state["historico"]
            if not itens:
                st.markdown('<div class="vazio">Nada gerado ainda.</div>', unsafe_allow_html=True)
            for h in itens:
                with st.container(key=f"hist_{h['token']}"):
                    a, b, c = st.columns([5, 1.9, 0.5], vertical_alignment="center")
                    a.markdown(f'<div class="hnome">🕘 {html.escape(h["nome"])}</div><div class="hinfo">{h["quando"]} · '
                               f'{_milhar(h["quantidade"])} registros · {len(h["colunas"])} colunas · {NOMES_FORMATO[h["formato"]]}</div>',
                               unsafe_allow_html=True)
                    linhas_h = st.session_state["banco_linhas"].get(h["token"]) or []
                    b.download_button("Baixar de novo", icon=":material/download:", key=f"dlh_{h['token']}", width="stretch",
                                      file_name=h["nome"], mime=planilha.MIME[h["formato"]], on_click="ignore",
                                      data=(lambda h=h, l=linhas_h: planilha.gerar_arquivo(
                                          h["colunas"], l, h["formato"] != "json" and h["com_titulo"], h["formato"], h["nome_base"])[1]))
                    c.button("", icon=":material/delete:", key=f"delh_{h['token']}", help=f"Excluir {h['nome']}",
                             on_click=_excluir_hist, args=(h["token"],))

    with dir_:
        with _card("ordem", "Ordem na planilha", "Use as setas para reorganizar."):
            if not ORDEM:
                st.markdown('<div class="vazio">Nenhuma coluna selecionada.</div>', unsafe_allow_html=True)
            else:
                with st.container(height=min(320, 44 * len(ORDEM) + 8), border=False):
                    for i, c in enumerate(ORDEM):
                        with st.container(key=f"ord_{i}"):
                            n, nm, u, d, x = st.columns([0.5, 4, 0.7, 0.7, 0.7], vertical_alignment="center", gap=None)
                            n.markdown(f'<span class="onum">{i + 1}</span>', unsafe_allow_html=True)
                            nm.markdown(f'<span class="onome">{html.escape(c)}</span>', unsafe_allow_html=True)
                            u.button("", icon=":material/arrow_upward:", key=f"sobe_{i}", disabled=i == 0, help="Subir",
                                     on_click=_mover, args=(i, -1))
                            d.button("", icon=":material/arrow_downward:", key=f"desce_{i}", disabled=i == len(ORDEM) - 1,
                                     help="Descer", on_click=_mover, args=(i, 1))
                            x.button("", icon=":material/close:", key=f"tira_{i}", help="Remover", on_click=_remover, args=(c,))

        with _card("config", "Configuração"):
            CFG["quantidade"] = int(st.number_input("Quantidade de registros", 1, 100000, int(CFG["quantidade"]), step=1, key="w_qtd"))
            CFG["nome_arquivo"] = st.text_input("Nome do arquivo (opcional)", value=CFG["nome_arquivo"],
                                                placeholder="massa_cadastro_loja", key="w_nome")
            st.caption("A data é acrescentada automaticamente.")
            CFG["com_titulo"] = st.checkbox("Incluir título na planilha", value=bool(CFG["com_titulo"]), key="w_titulo")

        with _card("sujeira", "Sujeira na planilha", "Os problemas que costumam quebrar sistema no teste."):
            qtd = CFG["quantidade"]
            for chave, _, _ in cfg_mod.SUJEIRA_CAMPOS:
                titulo, dica = SUJEIRA_TEXTO[chave]
                falta = SUJEIRA_EXIGE.get(chave)
                falta = falta if falta and falta not in ORDEM else None
                atual = int(CFG["sujeira"].get(chave, 0))
                limite = qtd if chave == "linha_branca" else max(qtd - 1, 0)
                with st.container(key=f"suj_{chave}"):
                    a, b = st.columns([3, 1.1], vertical_alignment="center")
                    on = a.checkbox(titulo, value=atual > 0 and not falta, disabled=bool(falta) or limite < 1, key=f"w_suj_{chave}")
                    if on:
                        v = b.number_input("Qtd", 1, max(limite, 1), min(max(atual, 1), max(limite, 1)),
                                           key=f"w_sujn_{chave}", label_visibility="collapsed")
                        CFG["sujeira"][chave] = int(v)
                    else:
                        CFG["sujeira"][chave] = 0
                    st.markdown(f'<div class="sdica">{f"marque a coluna {falta}" if falta else dica}</div>', unsafe_allow_html=True)

        with _card("baixar", "Baixar"):
            HIST = st.session_state["historico"]
            BANCO = st.session_state["banco_linhas"]
            snap = {**CFG, "colunas": list(ORDEM), "sujeira": dict(CFG["sujeira"]), "extras": list(EXTRAS)}

            def gerar(fmt: str, snap=snap):
                """Roda no clique: gera as linhas, monta o arquivo e guarda no histórico."""
                cols = snap["colunas"]
                opc = cfg_mod.montar_opcoes(snap)
                linhas = [geradores.gerar_registro(cols, opc, i) for i in range(int(snap["quantidade"]))]
                geradores.aplicar_sujeira(linhas, cols, snap["sujeira"])
                nome, conteudo, _ = planilha.gerar_arquivo(cols, linhas, fmt != "json" and snap["com_titulo"], fmt, snap["nome_arquivo"])
                token = (max(BANCO) if BANCO else 0) + 1
                BANCO[token] = linhas
                novo = historico.registrar(list(HIST), {
                    "token": token, "nome": nome, "formato": fmt, "colunas": cols, "quantidade": len(linhas),
                    "nome_base": snap["nome_arquivo"], "com_titulo": snap["com_titulo"],
                    "quando": datetime.now().strftime("%d/%m, %H:%M"),
                })
                HIST[:] = novo
                return conteudo

            antes = len(BANCO)

            def esperar(antes=antes):
                """Espera o arquivo ficar pronto para o histórico já aparecer atualizado."""
                import time
                for _ in range(100):
                    if len(BANCO) > antes:
                        break
                    time.sleep(0.1)

            sem = not ORDEM
            if sem:
                st.caption("Selecione pelo menos uma coluna.")
            st.download_button("Gerar Excel (.xlsx)", icon=":material/download:", data=lambda: gerar("xlsx"),
                               file_name=planilha.nome_arquivo(CFG["nome_arquivo"], "xlsx"), mime=planilha.MIME["xlsx"],
                               type="primary", width="stretch", disabled=sem, key="gerar_xlsx", on_click=esperar)
            c1, c2 = st.columns(2)
            c1.download_button("CSV", data=lambda: gerar("csv"), file_name=planilha.nome_arquivo(CFG["nome_arquivo"], "csv"),
                               mime=planilha.MIME["csv"], width="stretch", disabled=sem, key="gerar_csv", on_click=esperar)
            c2.download_button("JSON", data=lambda: gerar("json"), file_name=planilha.nome_arquivo(CFG["nome_arquivo"], "json"),
                               mime=planilha.MIME["json"], width="stretch", disabled=sem, key="gerar_json", on_click=esperar)

# ===========================================================================
# GERAR DADO ÚNICO
# ===========================================================================

elif ABA == "Gerar dado único":
    _, meio, _ = st.columns([1, 2.4, 1])
    with meio, _card("unico", "Gerar dado único", "Gere um valor avulso e copie para onde precisar."):
        a, b, c = st.columns([1.3, 1.3, 1], vertical_alignment="bottom")
        tipo = a.selectbox("Tipo de dado", geradores.TIPOS_DADO_UNICO, key="u_tipo")
        bandeira = "Visa"
        sem_p = False
        if tipo == "Cartão de crédito":
            bandeira = b.selectbox("Bandeira", geradores.BANDEIRAS, key="u_band")
        if tipo in ("CPF", "CNPJ", "RG", "Telefone", "Celular"):
            sem_p = b.checkbox("Sem pontuação", key="u_semp")
        botoes = {"Senha": ("Alterar regras", "senha"), "CEP": ("Faixa de CEP", "cep"),
                  "E-mail": ("Domínio", "email"), "Valor": ("Valor fixo ou faixa", "valor")}
        if tipo in botoes:
            b.button(botoes[tipo][0], key="u_opc", on_click=_abrir, args=(botoes[tipo][1],), width="stretch")
        # Tipos que saem de uma região: o DDD e o CEP vêm do estado escolhido.
        if tipo in REGIAO_TIPOS:
            with c:
                st.button("Estado e DDD", key="u_est", icon=":material/location_on:", width="stretch",
                          help="Escolhe os estados que o DDD pode sair. Vale também para a planilha.",
                          on_click=_abrir, args=("estados",))
            est = CFG["estados"] or list(brasil.SIGLAS_BR)
            ddds = sorted({d for uf in est for d in brasil.DDDS_POR_UF.get(uf, [])})
            mostra = ", ".join(str(d) for d in ddds[:14]) + ("…" if len(ddds) > 14 else "")
            st.caption(f"DDD de {', '.join(est) if len(est) < 8 else 'todos os estados'}: {mostra}")
        if tipo == "UUID":
            st.caption("Código único aleatório, sem significado.")

        opc = {"bandeira": bandeira, "sem_pontuacao": sem_p, "senha": CFG["senha"], "cep_min": CFG["cep_min"],
               "cep_max": CFG["cep_max"], "email_dominio": CFG["dominio"] or None, "pix_tipo": CFG["pix_tipo"],
               "valor_fixo": CFG["valor_fixo"], "valor_min": CFG["valor_min"], "valor_max": CFG["valor_max"],
               "estados": CFG["estados"] or None}
        assinatura = repr((tipo, sorted(opc.items(), key=lambda kv: kv[0])))
        if st.session_state.get("u_assin") != assinatura or st.session_state.pop("u_novo", False):
            st.session_state["u_assin"] = assinatura
            st.session_state["u_res"] = geradores.gerar_dado_unico(tipo, opc)

        for i, (rot, val) in enumerate(st.session_state["u_res"]):
            with st.container(key=f"res_{i}"):
                x, y = st.columns([5, 1.1], vertical_alignment="center")
                x.markdown(f'<div class="rrot">{html.escape(str(rot))}</div><div class="rval">{html.escape(str(val))}</div>',
                           unsafe_allow_html=True)
                with y:
                    _botao_copiar(str(val), f"cp_{i}")
        if st.button("Gerar novo", key="u_gerar", type="primary", icon=":material/refresh:", width="stretch"):
            st.session_state["u_novo"] = True
            st.rerun()

st.markdown('<p class="rodape">Dados fictícios, apenas para testes de software. CPF, CNPJ, CNH, PIS e título têm dígitos '
            'verificadores válidos, mas não pertencem a pessoas reais.</p>',
            unsafe_allow_html=True)

# Abre a janela pedida (engrenagem, modelo com data de nascimento etc.)
_qual = st.session_state.pop("abrir", None)
if _qual in JANELAS:
    JANELAS[_qual]()
