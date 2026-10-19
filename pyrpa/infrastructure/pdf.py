from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union


class PdfExtracaoException(Exception):
    """Exceção lançada em falhas de abertura ou leitura de arquivos PDF."""
    pass


class PdfAdapter:
    """
    Adaptador de processamento e extração de documentos PDF para automações RPA (IDP).
    Utiliza pypdf para extração de texto página a página e regex para reconhecimento
    automático de dados corporativos (CNPJs, CPFs, valores monetários, datas e boletos).
    """

    def __init__(self) -> None:
        pass

    def extrair_texto(self, caminho_pdf: Union[str, Path]) -> str:
        """Extrai todo o conteúdo textual contínuo de um arquivo PDF."""
        paginas = self.extrair_paginas(caminho_pdf)
        return "\n--- PÁGINA ---\n".join(paginas)

    def extrair_paginas(self, caminho_pdf: Union[str, Path]) -> List[str]:
        """Extrai o texto de cada página separadamente, preservando a numeração."""
        path = Path(caminho_pdf).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {path}")

        try:
            import pypdf
            leitor = pypdf.PdfReader(str(path))
            paginas = []
            for num, pagina in enumerate(leitor.pages):
                texto = pagina.extract_text() or ""
                paginas.append(texto.strip())
            return paginas
        except Exception as exc:
            raise PdfExtracaoException(f"Erro ao extrair texto do PDF '{path.name}': {exc}") from exc

    def extrair_campos_padrao(self, caminho_pdf: Union[str, Path]) -> Dict[str, Any]:
        """
        Analisa o texto do PDF com expressões regulares para identificar
        campos corporativos brasileiros frequentes em faturas, recibos e DANFEs.
        """
        texto_completo = self.extrair_texto(caminho_pdf)

        # Expressões regulares corporativas
        padrao_cnpj = r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"
        padrao_cpf = r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"
        padrao_data = r"\b\d{2}/\d{2}/\d{4}\b"
        padrao_valor = r"R\$\s?(\d{1,3}(?:\.\d{3})*,\d{2})"
        padrao_linha_digitavel = r"\b\d{5}\.\d{5}\s\d{5}\.\d{6}\s\d{5}\.\d{6}\s\d\s\d{14}\b"

        cnpjs = list(set(re.findall(padrao_cnpj, texto_completo)))
        cpfs = list(set(re.findall(padrao_cpf, texto_completo)))
        datas = list(set(re.findall(padrao_data, texto_completo)))
        valores = list(set(re.findall(padrao_valor, texto_completo)))
        linhas_digitaveis = list(set(re.findall(padrao_linha_digitavel, texto_completo)))

        return {
            "arquivo": Path(caminho_pdf).name,
            "cnpjs_encontrados": cnpjs,
            "cpfs_encontrados": cpfs,
            "datas_encontradas": datas,
            "valores_encontrados": valores,
            "linhas_digitaveis_boletos": linhas_digitaveis,
            "total_caracteres": len(texto_completo),
        }
