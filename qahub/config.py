"""
QAhub - configuração, modelos prontos e colunas personalizadas
---------------------------------------------------------------
Estado inicial do app, modelos prontos de seleção de colunas e a
persistência das colunas personalizadas em arquivo.

Este módulo não depende de Streamlit.
"""

from __future__ import annotations

import json
import os

from .geradores import (
    COLUNAS_DISPONIVEIS, NASCIMENTO_PADRAO, SENHA_PADRAO, TIPOS_PIX,
)

# ---------------------------------------------------------------------------
# Sujeira na planilha
# ---------------------------------------------------------------------------

SUJEIRA_PADRAO = {
    "duplicadas": 0,
    "cpf_repetido": 0,
    "email_variacao": 0,
    "espacos": 0,
    "vazios": 0,
    "linha_branca": 0,
}

# Como cada tipo de sujeira aparece na tela.
SUJEIRA_CAMPOS = [
    ("duplicadas", "Linhas duplicadas", "cópias exatas de outra linha"),
    ("cpf_repetido", "Mesmo CPF em nomes diferentes", "mesmo CPF com nomes diferentes"),
    ("email_variacao", "E-mail com caixa ou espaços", "e-mail com caixa, espaços ou @ solto"),
    ("espacos", "Espaços sobrando", "espaços no começo e no fim do campo"),
    ("vazios", "Campo vazio", "campo vazio"),
    ("linha_branca", "Linha em branco", "linha em branco"),
]

# ---------------------------------------------------------------------------
# Estado inicial
# ---------------------------------------------------------------------------


def config_inicial() -> dict:
    """O app abre sem nenhuma coluna marcada, sem filtro e sem sujeira."""
    return {
        "colunas": [],
        "extras": [],
        "nascimento": dict(NASCIMENTO_PADRAO),
        "senha": dict(SENHA_PADRAO),
        "estados": [],
        "cidades": [],
        "cep_min": None,
        "cep_max": None,
        "sexo": None,
        "dominio": "",
        "cpf_sem_pontos": False,
        "cnpj_sem_pontos": False,
        "rg_sem_pontos": False,
        "telefone_sem_pontos": False,
        "celular_sem_pontos": False,
        "quantidade": 100,
        "com_titulo": True,
        "nome_arquivo": "",
        "sujeira": dict(SUJEIRA_PADRAO),
        "escolaridade": None,
        "pix_tipo": None,
        "renda_min": None,
        "renda_max": None,
        "valor_fixo": None,
        "valor_min": None,
        "valor_max": None,
    }


def montar_opcoes(cfg: dict) -> dict:
    """Transforma a configuração da tela nas opções usadas ao gerar linhas."""
    extras = {}
    for ex in cfg.get("extras", []):
        if ex.get("nome") and ex.get("valores"):
            extras[ex["nome"]] = {
                "valores": ex["valores"],
                "sequencial": bool(ex.get("sequencial")),
            }
    dominio = (cfg.get("dominio") or "").strip() or None
    return {
        "nascimento": cfg.get("nascimento") or dict(NASCIMENTO_PADRAO),
        "senha": cfg.get("senha") or dict(SENHA_PADRAO),
        "extras": extras,
        "cpf_sem_pontos": bool(cfg.get("cpf_sem_pontos")),
        "cnpj_sem_pontos": bool(cfg.get("cnpj_sem_pontos")),
        "rg_sem_pontos": bool(cfg.get("rg_sem_pontos")),
        "telefone_sem_pontos": bool(cfg.get("telefone_sem_pontos")),
        "celular_sem_pontos": bool(cfg.get("celular_sem_pontos")),
        "estados": cfg.get("estados") or None,
        "cidades": cfg.get("cidades") or None,
        "cep_min": cfg.get("cep_min"),
        "cep_max": cfg.get("cep_max"),
        "sexo_fixo": cfg.get("sexo"),
        "email_dominio": dominio,
        "escolaridade": cfg.get("escolaridade"),
        "renda_min": cfg.get("renda_min"),
        "renda_max": cfg.get("renda_max"),
        "valor_fixo": cfg.get("valor_fixo"),
        "valor_min": cfg.get("valor_min"),
        "valor_max": cfg.get("valor_max"),
        "pix_tipo": cfg.get("pix_tipo"),
    }


def colunas_da_config(cfg: dict) -> list[str]:
    """Colunas marcadas, incluindo as personalizadas criadas pelo usuário."""
    return list(cfg.get("colunas", []))


# ---------------------------------------------------------------------------
# Modelos prontos
# ---------------------------------------------------------------------------

MODELOS = [
    {
        "nome": "Cadastro PF",
        "resumo": "Pessoa física com tudo do endereço",
        "colunas": [
            "Nome completo", "CPF", "Data de nascimento", "Idade", "Sexo", "E-mail",
            "Telefone", "Celular", "Endereço", "Complemento", "Bairro", "Cidade",
            "Estado (UF)", "CEP", "Senha",
        ],
    },
    {
        "nome": "Cadastro PJ",
        "resumo": "Empresa com CNPJ e contato",
        "colunas": [
            "Nome da empresa", "CNPJ", "E-mail", "Telefone", "Celular", "Endereço",
            "Bairro", "Cidade", "Estado (UF)", "CEP", "Senha", "PIX",
        ],
    },
    {
        "nome": "Pedido com cartão",
        "resumo": "Cliente + cartão válido + valor",
        "colunas": [
            "Nome completo", "CPF", "E-mail", "Telefone", "Cidade", "Estado (UF)", "CEP",
            "Cartão de crédito", "Bandeira do cartão", "Validade do cartão",
            "CVV do cartão", "Valor",
        ],
    },
    {
        "nome": "Mailing",
        "resumo": "Só contato, leve e rápido",
        "colunas": ["Nome completo", "E-mail", "Telefone", "Celular", "Cidade", "Estado (UF)"],
    },
    {
        "nome": "Cobrança / boleto",
        "resumo": "Devedor com código de barras e valor",
        "colunas": [
            "Nome completo", "CPF", "E-mail", "Telefone", "Endereço", "Cidade",
            "Estado (UF)", "CEP", "Código de barras", "Valor", "Data de cadastro",
        ],
    },
]


def modelo_por_nome(nome: str) -> list[str] | None:
    """As colunas de um modelo pronto, ou None se o nome não existir."""
    for m in MODELOS:
        if m["nome"] == nome:
            return list(m["colunas"])
    return None


# ---------------------------------------------------------------------------
# Colunas personalizadas em arquivo
# ---------------------------------------------------------------------------

ARQUIVO_EXTRAS = "colunas_personalizadas.json"


def carregar_extras(caminho: str = ARQUIVO_EXTRAS) -> list[dict]:
    """Lê as colunas personalizadas salvas. Se der errado, começa vazio."""
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        return []
    if not isinstance(dados, list):
        return []
    extras = []
    for item in dados:
        if not isinstance(item, dict):
            continue
        nome = str(item.get("nome") or "").strip()
        valores = [str(v) for v in (item.get("valores") or []) if str(v).strip()]
        if nome and valores:
            extras.append({"nome": nome, "valores": valores, "sequencial": bool(item.get("sequencial"))})
    return extras


def salvar_extras(extras: list[dict], caminho: str = ARQUIVO_EXTRAS) -> bool:
    """Grava as colunas personalizadas. Falha silenciosa se o disco não deixar."""
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(extras, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


__all__ = [
    "SUJEIRA_PADRAO", "SUJEIRA_CAMPOS", "config_inicial", "montar_opcoes",
    "colunas_da_config", "MODELOS", "modelo_por_nome", "ARQUIVO_EXTRAS",
    "carregar_extras", "salvar_extras", "COLUNAS_DISPONIVEIS", "TIPOS_PIX",
]
