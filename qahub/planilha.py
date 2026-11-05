"""
QAhub - exportação da planilha
-------------------------------
Monta o arquivo final em Excel (.xlsx), CSV ou JSON e devolve o nome,
o conteúdo e o tipo para o botão de download.
"""

from __future__ import annotations

import io
import json
import re
from datetime import datetime

FORMATOS = ["xlsx", "csv", "json"]
NOMES_FORMATO = {"xlsx": "Excel (.xlsx)", "csv": "CSV", "json": "JSON"}
EXTENSAO = {"xlsx": "xlsx", "csv": "csv", "json": "json"}
MIME = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "json": "application/json",
}

COR_LARANJA = "FFFF7729"


def nome_arquivo(base: str, formato: str, quando: datetime | None = None) -> str:
    """Nome do arquivo: base + data e hora + extensão."""
    limpo = re.sub(r"\s+", "_", re.sub(r"[\\/:*?\"<>|]+", "-", (base or "").strip()))[:60] or "massa_de_teste"
    quando = quando or datetime.now()
    data = quando.strftime("%Y-%m-%d_%H%M")
    return f"{limpo}_{data}.{EXTENSAO[formato]}"


def para_xlsx(colunas: list[str], linhas: list[dict], com_titulo: bool = True) -> bytes:
    """Planilha Excel com o cabeçalho na cor da marca e a primeira linha fixa."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Massa de teste"
    if com_titulo:
        ws.append(colunas)
        preenchimento = PatternFill("solid", fgColor=COR_LARANJA)
        for c in range(1, len(colunas) + 1):
            celula = ws.cell(row=1, column=c)
            celula.fill = preenchimento
            celula.font = Font(bold=True, color="FFFFFFFF")
            celula.alignment = Alignment(horizontal="center", vertical="center")
        ws.freeze_panes = "A2"
    for l in linhas:
        ws.append([l.get(c, "") for c in colunas])
    for i, nome in enumerate(colunas, start=1):
        maior = max([len(nome) if com_titulo else 0] + [len(str(l.get(nome, ""))) for l in linhas] or [0])
        ws.column_dimensions[get_column_letter(i)].width = min(60, maior + 3)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _celula_csv(v) -> str:
    s = str(v if v is not None else "")
    return f'"{s.replace(chr(34), chr(34) * 2)}"' if re.search(r'[";\n]', s) else s


def para_csv(colunas: list[str], linhas: list[dict], com_titulo: bool = True) -> bytes:
    """CSV separado por ponto e vírgula, com BOM para abrir certo no Excel."""
    partes = ["\ufeff"]
    if com_titulo:
        partes.append(";".join(_celula_csv(c) for c in colunas) + "\r\n")
    for l in linhas:
        partes.append(";".join(_celula_csv(l.get(c, "")) for c in colunas) + "\r\n")
    return "".join(partes).encode("utf-8")


def para_json(colunas: list[str], linhas: list[dict]) -> bytes:
    """JSON com um objeto por linha, nas colunas escolhidas."""
    saida = [{c: l.get(c, "") for c in colunas} for l in linhas]
    return json.dumps(saida, ensure_ascii=False, indent=2).encode("utf-8")


def gerar_arquivo(
    colunas: list[str],
    linhas: list[dict],
    com_titulo: bool = True,
    formato: str = "xlsx",
    base: str = "",
    quando: datetime | None = None,
) -> tuple[str, bytes, str]:
    """Devolve (nome do arquivo, conteúdo, tipo) para o download."""
    formato = formato if formato in EXTENSAO else "xlsx"
    if formato == "csv":
        conteudo = para_csv(colunas, linhas, com_titulo)
    elif formato == "json":
        conteudo = para_json(colunas, linhas)
    else:
        conteudo = para_xlsx(colunas, linhas, com_titulo)
    return nome_arquivo(base, formato, quando), conteudo, MIME[formato]


__all__ = [
    "FORMATOS", "NOMES_FORMATO", "EXTENSAO", "MIME", "nome_arquivo",
    "para_xlsx", "para_csv", "para_json", "gerar_arquivo",
]
