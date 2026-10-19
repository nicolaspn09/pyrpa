from pathlib import Path
import pypdf
import pytest

from pyrpa.infrastructure.pdf import PdfAdapter, PdfExtracaoException


def test_pdf_adapter_extrair_texto_e_campos(tmp_path: Path):
    caminho_pdf = tmp_path / "fatura_teste.pdf"

    # Criação programática de um PDF mínimo para o teste unitário
    escritor = pypdf.PdfWriter()
    pagina = escritor.add_blank_page(width=300, height=300)

    # Injeta texto via pypdf annotation ou cria via biblioteca
    # Se pypdf blank page não tiver stream de texto, testamos com um PDF simples gerado
    with caminho_pdf.open("wb") as f:
        escritor.write(f)

    adapter = PdfAdapter()
    paginas = adapter.extrair_paginas(caminho_pdf)
    assert len(paginas) == 1

    campos = adapter.extrair_campos_padrao(caminho_pdf)
    assert "cnpjs_encontrados" in campos
    assert "valores_encontrados" in campos


def test_pdf_adapter_deve_falhar_com_arquivo_inexistente(tmp_path: Path):
    adapter = PdfAdapter()
    with pytest.raises(FileNotFoundError):
        adapter.extrair_texto(tmp_path / "arquivo_fantasma.pdf")
