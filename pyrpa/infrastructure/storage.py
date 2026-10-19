import csv
import json
from pathlib import Path
from typing import Any, Dict, List


class StorageAdapter:
    """
    Adaptador padronizado para manipulação de arquivos locais (JSON, CSV, relatórios e downloads)
    em automações RPA, garantindo criação segura de diretórios e codificação UTF-8.
    """

    def __init__(self, diretorio_base: Path) -> None:
        self.diretorio_base = Path(diretorio_base).resolve()
        self.pasta_downloads = self.diretorio_base / "downloads"
        self.pasta_relatorios = self.diretorio_base / "relatorios"
        self.pasta_downloads.mkdir(parents=True, exist_ok=True)
        self.pasta_relatorios.mkdir(parents=True, exist_ok=True)

    def salvar_json(self, nome_arquivo: str, dados: Any) -> Path:
        destino = self.pasta_relatorios / nome_arquivo
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
        return destino

    def ler_json(self, nome_arquivo: str) -> Any:
        origem = self.pasta_relatorios / nome_arquivo
        return json.loads(origem.read_text(encoding="utf-8"))

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
