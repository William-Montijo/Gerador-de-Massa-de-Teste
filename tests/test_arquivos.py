"""Testes do gerador de arquivos de teste (extensão e tamanho exatos)."""

import pytest

from qahub import arquivos as a


@pytest.mark.parametrize("tamanho", [0, 1, 5, 1023, 1024, 1025, 1024 * 1024])
@pytest.mark.parametrize("preench", ["zeros", "aleatorio", "texto"])
def test_tamanho_exato(tamanho, preench):
    assert len(a.gerar_conteudo("pdf", tamanho, preench)) == tamanho


@pytest.mark.parametrize("ext", ["pdf", "png", "jpg", "zip", "mp4", "docx", "txt"])
@pytest.mark.parametrize("tamanho", [0, 3, 10, 2048])
def test_tamanho_exato_com_cabecalho(ext, tamanho):
    assert len(a.gerar_conteudo(ext, tamanho, "zeros", True)) == tamanho


def test_unidades_e_limite():
    assert a.tamanho_em_bytes(1, "KB") == 1024
    assert a.tamanho_em_bytes(2, "MB") == 2 * 1024 * 1024
    assert a.tamanho_em_bytes(0, "B") == 0
    assert a.tamanho_em_bytes(a.LIMITE_MB, "MB") == a.LIMITE_BYTES
    with pytest.raises(ValueError):
        a.tamanho_em_bytes(a.LIMITE_MB + 1, "MB")
    with pytest.raises(ValueError):
        a.tamanho_em_bytes(-1, "KB")
    with pytest.raises(ValueError):
        a.tamanho_em_bytes(1, "GB")
    with pytest.raises(ValueError):
        a.gerar_conteudo("pdf", a.LIMITE_BYTES + 1)


def test_conteudos():
    assert set(a.gerar_conteudo("bin", 100, "zeros")) == {0}
    assert len(set(a.gerar_conteudo("bin", 4096, "aleatorio"))) > 100
    texto = a.gerar_conteudo("txt", 500, "texto")
    assert texto.startswith(b"Arquivo de teste") and texto.isascii()


def test_assinaturas():
    assert a.gerar_conteudo("pdf", 100, "zeros", True).startswith(b"%PDF-")
    assert a.gerar_conteudo("PNG", 100, "zeros", True).startswith(b"\x89PNG\r\n\x1a\n")
    assert a.gerar_conteudo(".zip", 100, "zeros", True).startswith(b"PK\x03\x04")
    assert a.gerar_conteudo("xlsx", 100, "zeros", True).startswith(b"PK\x03\x04")
    assert a.gerar_conteudo("pdf", 100, "zeros", False)[:5] == bytes(5)
    assert a.gerar_conteudo("txt", 100, "zeros", True) == bytes(100)  # sem assinatura para txt
    assert a.gerar_conteudo("pdf", 4, "zeros", True) == b"%PDF"  # cabeçalho cortado
    assert a.tem_assinatura("PDF") and a.tem_assinatura(".png") and not a.tem_assinatura("csv")
    assert all(a.tem_assinatura(e) or e in {"txt", "csv", "json", "xml", "html", "exe"} for e in a.EXTENSOES_COMUNS)


def test_extensao():
    assert a.normalizar_extensao(" .pdf ") == "pdf"
    assert a.normalizar_extensao("PDF") == "PDF"  # mantém a caixa (teste de extensão maiúscula)
    assert a.normalizar_extensao("tar.gz") == "tar.gz"
    for ruim in ["", "  ", ".", "p df", "a/b", "x" * 21, "pdf."]:
        with pytest.raises(ValueError):
            a.normalizar_extensao(ruim)


def test_nome_arquivo():
    assert a.nome_arquivo("", "pdf", 5, "MB") == "arquivo_teste_5MB.pdf"
    assert a.nome_arquivo("  meu relatório ", ".PDF", 1, "KB") == "meu_relatório.PDF"
    assert a.nome_arquivo("a/b:c", "txt", 1, "B") == "a-b-c.txt"
    assert a.nome_arquivo("", "zip", 1.5, "MB") == "arquivo_teste_1.5MB.zip"


def test_formatar_tamanho():
    assert a.formatar_tamanho(0) == "0 bytes"
    assert a.formatar_tamanho(1023) == "1.023 bytes"
    assert a.formatar_tamanho(1024) == "1 KB (1.024 bytes)"
    assert a.formatar_tamanho(5 * 1024 * 1024) == "5 MB (5.242.880 bytes)"
    assert a.formatar_tamanho(1536) == "1,5 KB (1.536 bytes)"
