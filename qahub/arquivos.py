"""
QAhub - arquivos de teste
--------------------------
Gera um arquivo com a extensão e o tamanho (em bytes) que você pedir, para
testar upload, limite de tamanho, extensões bloqueadas e armazenamento.

O arquivo não é um documento de verdade: é só um conteúdo com o tamanho exato.
Opcionalmente começa com a "assinatura" do formato (os primeiros bytes que um
PDF, PNG, ZIP etc. têm), para passar em validações que conferem o tipo real.

Este módulo não depende de Streamlit.
"""

from __future__ import annotations

import os
import re

# 1 KB = 1024 bytes, como o Windows e a maioria dos sistemas mostram.
UNIDADES = {"B": 1, "KB": 1024, "MB": 1024 ** 2}
LIMITE_MB = 100
LIMITE_BYTES = LIMITE_MB * 1024 ** 2

EXTENSOES_COMUNS = [
    "pdf", "png", "jpg", "jpeg", "gif", "bmp", "txt", "csv", "json", "xml", "html",
    "xlsx", "xls", "docx", "doc", "pptx", "zip", "rar", "7z", "gz", "mp3", "mp4", "exe",
]

PREENCHIMENTOS = {
    "zeros": "Vazio (bytes zero)",
    "aleatorio": "Aleatório (não compacta)",
    "texto": "Texto legível",
}

# Primeiros bytes de cada formato. Só isso: o arquivo não abre no programa do formato.
ASSINATURAS: dict[str, bytes] = {
    "pdf": b"%PDF-1.4\n",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00",
    "jpeg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00",
    "gif": b"GIF89a",
    "bmp": b"BM",
    "zip": b"PK\x03\x04",
    "docx": b"PK\x03\x04",
    "xlsx": b"PK\x03\x04",
    "pptx": b"PK\x03\x04",
    "gz": b"\x1f\x8b\x08",
    "7z": b"7z\xbc\xaf\x27\x1c",
    "rar": b"Rar!\x1a\x07\x00",
    "mp3": b"ID3\x03\x00\x00\x00\x00\x00\x00",
    "mp4": b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom",
    "xls": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    "doc": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
}

_TEXTO = b"Arquivo de teste gerado pelo QAhub. Conteudo sem significado.\n"


def normalizar_extensao(extensao: str) -> str:
    """Tira o ponto do começo e confere. Mantém maiúsculas e minúsculas como digitadas."""
    ext = (extensao or "").strip().lstrip(".")
    if not ext:
        raise ValueError("Informe a extensão do arquivo.")
    if len(ext) > 20 or not re.fullmatch(r"[A-Za-z0-9]+(\.[A-Za-z0-9]+)*", ext):
        raise ValueError("Use só letras e números na extensão (ex.: pdf, tar.gz).")
    return ext


def tamanho_em_bytes(valor: int | float, unidade: str) -> int:
    """Converte o tamanho escolhido em bytes e confere o limite."""
    if unidade not in UNIDADES:
        raise ValueError("Unidade desconhecida.")
    if valor is None or valor < 0:
        raise ValueError("O tamanho não pode ser negativo.")
    total = int(round(valor * UNIDADES[unidade]))
    if total > LIMITE_BYTES:
        raise ValueError(f"O tamanho máximo é {LIMITE_MB} MB.")
    return total


def tem_assinatura(extensao: str) -> bool:
    return (extensao or "").strip().lstrip(".").lower() in ASSINATURAS


def gerar_conteudo(extensao: str, tamanho: int, preenchimento: str = "zeros", com_assinatura: bool = False) -> bytes:
    """Conteúdo com exatamente `tamanho` bytes."""
    if tamanho < 0 or tamanho > LIMITE_BYTES:
        raise ValueError(f"O tamanho deve ficar entre 0 e {LIMITE_MB} MB.")
    ext = normalizar_extensao(extensao).lower()
    cabecalho = ASSINATURAS.get(ext, b"")[:tamanho] if com_assinatura else b""
    resto = tamanho - len(cabecalho)
    if preenchimento == "aleatorio":
        corpo = os.urandom(resto)
    elif preenchimento == "texto":
        corpo = (_TEXTO * (resto // len(_TEXTO) + 1))[:resto]
    else:
        corpo = bytes(resto)
    return cabecalho + corpo


def nome_arquivo(base: str, extensao: str, valor: int | float, unidade: str) -> str:
    """Nome do arquivo: o que a pessoa digitou ou 'arquivo_teste_5MB', mais a extensão."""
    ext = normalizar_extensao(extensao)
    limpo = re.sub(r"\s+", "_", re.sub(r"[\\/:*?\"<>|]+", "-", (base or "").strip())).strip(".")[:60]
    if not limpo:
        numero = f"{valor:g}" if isinstance(valor, float) else str(valor)
        limpo = f"arquivo_teste_{numero}{unidade}"
    return f"{limpo}.{ext}"


def formatar_tamanho(total: int) -> str:
    """Ex.: '5 MB (5.242.880 bytes)'."""
    bytes_br = f"{total:,}".replace(",", ".")
    for un in ("MB", "KB"):
        if total >= UNIDADES[un]:
            v = total / UNIDADES[un]
            texto = f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")
            return f"{texto} {un} ({bytes_br} bytes)"
    return f"{bytes_br} bytes"


__all__ = [
    "UNIDADES", "LIMITE_MB", "LIMITE_BYTES", "EXTENSOES_COMUNS", "PREENCHIMENTOS", "ASSINATURAS",
    "normalizar_extensao", "tamanho_em_bytes", "tem_assinatura", "gerar_conteudo",
    "nome_arquivo", "formatar_tamanho",
]
