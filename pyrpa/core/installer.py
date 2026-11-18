from dataclasses import dataclass, field
import importlib.util
import subprocess
import sys
from typing import Dict, List, Set, Tuple


# Mapeamento único: (nome_importacao_python, especificacao_pip)
DEPENDENCIAS_BASE: List[Tuple[str, str]] = [
    ("dotenv", "python-dotenv>=1.0.0"),
    ("pandas", "pandas>=2.0.0"),
    ("openpyxl", "openpyxl>=3.1.0"),
    ("sqlalchemy", "sqlalchemy>=2.0.0"),
]

DEPENDENCIAS_POR_MODULO: Dict[str, List[Tuple[str, str]]] = {
    "web": [
        ("playwright", "playwright>=1.40.0"),
        ("selenium", "selenium>=4.15.0"),
    ],
    "banco": [
        ("sqlalchemy", "sqlalchemy>=2.0.0"),
    ],
    "excel": [
        ("pandas", "pandas>=2.0.0"),
        ("openpyxl", "openpyxl>=3.1.0"),
    ],
    "pdf": [
        ("pypdf", "pypdf>=5.0.0"),
    ],
    "ia": [
        ("openai", "openai>=1.0.0"),
    ],
    "email": [],
}


@dataclass
class ResultadoInstalacaoDeps:
    """Resumo da verificação e instalação automática de bibliotecas de um robô."""
    ja_instalados: List[str] = field(default_factory=list)
    instalados_agora: List[str] = field(default_factory=list)
    falhas: List[str] = field(default_factory=list)
    erro_detalhe: str = ""


def coletar_especificacoes_modulos(modulos: Set[str], incluir_base: bool = True) -> List[Tuple[str, str]]:
    """Coleta e remove duplicidades das dependências exigidas pelos módulos escolhidos."""
    vistos: Set[str] = set()
    resultado: List[Tuple[str, str]] = []

    pares: List[Tuple[str, str]] = []
    if incluir_base:
        pares.extend(DEPENDENCIAS_BASE)

    for mod in sorted(modulos):
        pares.extend(DEPENDENCIAS_POR_MODULO.get(mod.strip().lower(), []))

    for mod_import, pip_spec in pares:
        if mod_import not in vistos:
            vistos.add(mod_import)
            resultado.append((mod_import, pip_spec))

    return resultado


def listar_pacotes_pip_modulos(modulos: Set[str], incluir_base: bool = True) -> List[str]:
    """Retorna somente as especificações pip para preenchimento do requirements.txt."""
    return [pip_spec for _, pip_spec in coletar_especificacoes_modulos(modulos, incluir_base=incluir_base)]


def gerar_conteudo_requirements(modulos: Set[str]) -> str:
    """Gera um requirements.txt limpo e descomentado para os módulos escolhidos."""
    pacotes = listar_pacotes_pip_modulos(modulos, incluir_base=True)
    linhas = [
        "# Framework pyrpa (instalar via repositório oficial, não pelo PyPI)",
        "pyrpa @ git+https://github.com/nicolaspn09/pyrpa.git",
        "",
        "# Dependências ativas do robô (instaladas automaticamente pelo pyrpa init/add)",
        *pacotes,
    ]
    return "\n".join(linhas) + "\n"


def registrar_dependencias_requirements(caminho_requirements: "Path", modulos: Set[str]) -> None:
    """Acrescenta dependências de novos módulos no requirements.txt sem duplicar entradas."""
    from pathlib import Path

    req_path = Path(caminho_requirements)
    if not req_path.is_file():
        req_path.write_text(gerar_conteudo_requirements(modulos), encoding="utf-8")
        return

    conteudo_atual = req_path.read_text(encoding="utf-8")
    nomes_existentes = {
        linha.strip().split(">=")[0].split("==")[0].split("@")[0].strip().lower()
        for linha in conteudo_atual.splitlines()
        if linha.strip() and not linha.strip().startswith("#")
    }

    novas_linhas = []
    for spec in listar_pacotes_pip_modulos(modulos, incluir_base=False):
        pkg_nome = spec.split(">=")[0].split("==")[0].strip().lower()
        if pkg_nome not in nomes_existentes:
            novas_linhas.append(spec)
            nomes_existentes.add(pkg_nome)

    if novas_linhas:
        separador = "" if conteudo_atual.endswith("\n") else "\n"
        req_path.write_text(conteudo_atual + separador + "\n".join(novas_linhas) + "\n", encoding="utf-8")


def garantir_dependencias_modulos(
    modulos: Set[str],
    instalar_automaticamente: bool = True,
    incluir_base: bool = True,
) -> ResultadoInstalacaoDeps:
    """
    Verifica quais bibliotecas exigidas pelos módulos estão disponíveis no ambiente Python
    atual e, caso alguma falte, executa a instalação automática via pip.
    """
    specs = coletar_especificacoes_modulos(modulos, incluir_base=incluir_base)
    ja_instalados: List[str] = []
    faltantes: List[Tuple[str, str]] = []

    for mod_import, pip_spec in specs:
        if importlib.util.find_spec(mod_import) is not None:
            ja_instalados.append(pip_spec)
        else:
            faltantes.append((mod_import, pip_spec))

    if not faltantes:
        return ResultadoInstalacaoDeps(ja_instalados=ja_instalados)

    if not instalar_automaticamente:
        return ResultadoInstalacaoDeps(
            ja_instalados=ja_instalados,
            falhas=[pip_spec for _, pip_spec in faltantes],
        )

    pip_specs_faltantes = [pip_spec for _, pip_spec in faltantes]
    comando = [sys.executable, "-m", "pip", "install", *pip_specs_faltantes]

    try:
        proc = subprocess.run(comando, capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            return ResultadoInstalacaoDeps(
                ja_instalados=ja_instalados,
                instalados_agora=pip_specs_faltantes,
            )

        detalhe = (proc.stderr or proc.stdout or "Erro desconhecido do pip.").strip()
        if "externally-managed-environment" in detalhe:
            detalhe = (
                "Ambiente Linux protegido pelo PEP 668 (externally-managed-environment). "
                "Execute o pyrpa dentro de uma virtualenv (.venv) ou use o script instalar.sh."
            )
        return ResultadoInstalacaoDeps(
            ja_instalados=ja_instalados,
            falhas=pip_specs_faltantes,
            erro_detalhe=detalhe,
        )
    except Exception as exc:
        return ResultadoInstalacaoDeps(
            ja_instalados=ja_instalados,
            falhas=pip_specs_faltantes,
            erro_detalhe=str(exc),
        )
