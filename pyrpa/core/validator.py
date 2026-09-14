from pathlib import Path
from typing import Union
import yaml
from pydantic import ValidationError

from pyrpa.models.schema import FluxoSchema


class FluxoInvalidoException(Exception):
    """Exceção de domínio lançada quando o arquivo de metadados do robô é inválido."""
    pass


def validar_arquivo_fluxo(caminho_arquivo: Union[str, Path]) -> FluxoSchema:
    """
    Lê um arquivo YAML de fluxo, valida sua sintaxe e aplica as regras do FluxoSchema.

    :param caminho_arquivo: Caminho físico para o arquivo fluxo.yaml
    :return: Instância validada do FluxoSchema
    :raises FileNotFoundError: Se o arquivo não existir no disco
    :raises FluxoInvalidoException: Se houver erro de sintaxe YAML ou violação de regras de negócio
    """
    path = Path(caminho_arquivo)

    if not path.is_file():
        raise FileNotFoundError(f"Arquivo de fluxo não encontrado no caminho: {path.resolve()}")

    try:
        conteudo_raw = path.read_text(encoding="utf-8")
        dados_dict = yaml.safe_load(conteudo_raw)
    except yaml.YAMLError as exc:
        raise FluxoInvalidoException(f"Erro de sintaxe no arquivo YAML: {exc}") from exc

    if not isinstance(dados_dict, dict):
        raise FluxoInvalidoException(
            "O arquivo YAML deve conter um mapeamento chave-valor na raiz (ex: 'fluxo:')."
        )

    try:
        return FluxoSchema.model_validate(dados_dict)
    except ValidationError as exc:
        raise FluxoInvalidoException(f"Erro de validação do contrato do fluxo:\n{exc}") from exc