import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import zipfile


class StorageAdapter:
    """
    Adaptador padronizado para manipulação de arquivos (Excel, CSV, JSON, ZIP e downloads)
    em automações RPA, garantindo criação segura de diretórios e codificação UTF-8.
    """

    def __init__(self, diretorio_base: Union[str, Path]) -> None:
        self.diretorio_base = Path(diretorio_base).resolve()
        self.pasta_downloads = self.diretorio_base / "downloads"
        self.pasta_relatorios = self.diretorio_base / "relatorios"
        self.pasta_downloads.mkdir(parents=True, exist_ok=True)
        self.pasta_relatorios.mkdir(parents=True, exist_ok=True)

    # --- JSON ---
    def salvar_json(self, nome_arquivo: str, dados: Any) -> Path:
        destino = self.pasta_relatorios / nome_arquivo
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
        return destino

    def ler_json(self, nome_arquivo: str) -> Any:
        origem = self.pasta_relatorios / nome_arquivo
        return json.loads(origem.read_text(encoding="utf-8"))

    # --- CSV ---
    def salvar_csv(self, nome_arquivo: str, registros: List[Dict[str, Any]]) -> Path:
        destino = self.pasta_relatorios / nome_arquivo
        destino.parent.mkdir(parents=True, exist_ok=True)
        if not registros:
            destino.write_text("", encoding="utf-8")
            return destino
        colunas = list(registros[0].keys())
        with destino.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=colunas)
            writer.writeheader()
            writer.writerows(registros)
        return destino

    def ler_csv(self, nome_arquivo: str) -> List[Dict[str, Any]]:
        origem = self.pasta_relatorios / nome_arquivo
        with origem.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    # --- EXCEL (Pandas / OpenpyXL) ---
    def exportar_excel(
        self,
        nome_arquivo: str,
        dados: Union[List[Dict[str, Any]], Any],
        nome_aba: str = "Dados",
    ) -> Path:
        """
        Exporta registros para uma planilha Excel (.xlsx) formatada via Pandas.
        """
        import pandas as pd

        destino = self.pasta_relatorios / nome_arquivo
        destino.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(dados, pd.DataFrame):
            df = dados
        else:
            df = pd.DataFrame(dados)

        df.to_excel(destino, sheet_name=nome_aba, index=False, engine="openpyxl")
        return destino

    def ler_excel(
        self,
        nome_arquivo: str,
        nome_aba: Union[str, int] = 0,
    ) -> List[Dict[str, Any]]:
        """
        Lê uma planilha Excel (.xlsx ou .xls) e retorna as linhas como lista de dicionários.
        """
        import pandas as pd

        origem = self.pasta_relatorios / nome_arquivo
        df = pd.read_excel(origem, sheet_name=nome_aba, engine="openpyxl")
        # Converte valores nulos para None e serializa em dicionários
        return df.where(pd.notnull(df), None).to_dict(orient="records")

    # --- LEITOR UNIVERSAL DE DADOS ---
    def ler_dados(self, nome_arquivo: str) -> List[Dict[str, Any]]:
        """
        Identifica automaticamente a extensão do arquivo (.xlsx, .csv, .json)
        e executa a leitura convertendo em lista de dicionários.
        """
        extensao = Path(nome_arquivo).suffix.lower()
        if extensao in {".xlsx", ".xls"}:
            return self.ler_excel(nome_arquivo)
        elif extensao == ".csv":
            return self.ler_csv(nome_arquivo)
        elif extensao == ".json":
            conteudo = self.ler_json(nome_arquivo)
            return conteudo if isinstance(conteudo, list) else [conteudo]
        else:
            raise ValueError(f"Extensão de arquivo não suportada para leitura universal: '{extensao}'.")

    # --- ARQUIVOS COMPACTADOS (ZIP) ---
    def descompactar_zip(self, arquivo_zip: Union[str, Path], pasta_destino: Optional[Path] = None) -> Path:
        """
        Descompacta arquivos ZIP baixados pelo robô (muito comum em portais fiscais e governamentais).
        """
        origem = Path(arquivo_zip)
        destino = pasta_destino or self.pasta_downloads / origem.stem
        destino.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(origem, "r") as z:
            z.extractall(destino)

        return destino

    def compactar_pasta(self, pasta_origem: Union[str, Path], nome_arquivo_zip: str) -> Path:
        """
        Compacta uma pasta inteira em um arquivo .zip para envio ou arquivamento.
        """
        origem = Path(pasta_origem)
        destino_zip = self.pasta_relatorios / nome_arquivo_zip
        destino_zip.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(destino_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for item in origem.rglob("*"):
                if item.is_file():
                    z.write(item, item.relative_to(origem))

        return destino_zip
