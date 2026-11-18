from dataclasses import dataclass
import importlib
import os
from pathlib import Path
import platform
import shutil
import sys
from typing import List, Optional


@dataclass
class ItemDiagnostico:
    categoria: str
    item: str
    status: str  # "OK", "AVISO", "FALHA"
    detalhes: str


_EXECUTAVEIS_WINDOWS = {
    "chrome": ("Google", "Chrome", "Application", "chrome.exe"),
    "edge": ("Microsoft", "Edge", "Application", "msedge.exe"),
    "firefox": ("Mozilla Firefox", "firefox.exe"),
}

_CANDIDATOS_UNIX = {
    "chrome": ["chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"],
    "edge": ["msedge", "microsoft-edge", "microsoft-edge-stable"],
    "firefox": ["firefox"],
}


def verificar_navegador_instalado(nome_navegador: str) -> bool:
    """Verifica se o binário do navegador existe no sistema (Windows, Linux ou macOS)."""
    sistema = platform.system()
    if sistema == "Windows" and nome_navegador in _EXECUTAVEIS_WINDOWS:
        pastas_prog = [
            os.environ.get("PROGRAMFILES", "C:\\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        rel_path = Path(*_EXECUTAVEIS_WINDOWS[nome_navegador])
        if any(pasta and (Path(pasta) / rel_path).is_file() for pasta in pastas_prog):
            return True

    for binario in _CANDIDATOS_UNIX.get(nome_navegador, [nome_navegador]):
        if shutil.which(binario) is not None:
            return True

    return False


def executar_diagnostico_doctor(diretorio_atual: Optional[Path] = None) -> List[ItemDiagnostico]:
    """
    Executa uma varredura completa da máquina e do ambiente Python para certificar
    que o sistema está pronto para executar automações corporativas com o pyrpa.
    """
    diagnosticos: List[ItemDiagnostico] = []

    # 1. Ambiente Python e Sistema Operacional
    v_python = sys.version_info
    versao_str = f"{v_python.major}.{v_python.minor}.{v_python.micro}"
    if v_python >= (3, 10):
        diagnosticos.append(ItemDiagnostico(
            categoria="Sistema Base",
            item="Versão do Python",
            status="OK",
            detalhes=f"Python {versao_str} (Atende ao requisito >= 3.10)"
        ))
    else:
        diagnosticos.append(ItemDiagnostico(
            categoria="Sistema Base",
            item="Versão do Python",
            status="FALHA",
            detalhes=f"Python {versao_str} (Requer Python >= 3.10)"
        ))

    sistema_nome = platform.system()
    versao_so = platform.release()
    if sistema_nome == "Windows" and versao_so == "10":
        try:
            if sys.getwindowsversion().build >= 22000:
                versao_so = "11"
        except Exception:
            pass

    diagnosticos.append(ItemDiagnostico(
        categoria="Sistema Base",
        item="Sistema Operacional",
        status="OK",
        detalhes=f"{sistema_nome} {versao_so} ({platform.architecture()[0]})"
    ))

    # 2. Navegadores Instalados no Host
    chrome_ok = verificar_navegador_instalado("chrome")
    diagnosticos.append(ItemDiagnostico(
        categoria="Navegadores",
        item="Google Chrome",
        status="OK" if chrome_ok else "AVISO",
        detalhes="Detectado no sistema operacional" if chrome_ok else "Não detectado nos caminhos padrão"
    ))

    edge_ok = verificar_navegador_instalado("edge")
    diagnosticos.append(ItemDiagnostico(
        categoria="Navegadores",
        item="Microsoft Edge",
        status="OK" if edge_ok else "AVISO",
        detalhes="Detectado no sistema operacional" if edge_ok else "Não detectado nos caminhos padrão"
    ))

    firefox_ok = verificar_navegador_instalado("firefox")
    diagnosticos.append(ItemDiagnostico(
        categoria="Navegadores",
        item="Mozilla Firefox",
        status="OK" if firefox_ok else "AVISO",
        detalhes="Detectado no sistema operacional" if firefox_ok else "Não detectado (opcional)"
    ))

    # 3. Pacotes Python do Ecossistema RPA
    pacotes_obrigatorios = [
        ("typer", "Typer (CLI)"),
        ("rich", "Rich (Terminal Visual)"),
        ("pydantic", "Pydantic v2 (Validação de Contratos)"),
        ("yaml", "PyYAML (Orquestração Declarativa)"),
        ("dotenv", "Python-Dotenv (Variáveis .env)"),
    ]
    for mod_nome, descricao in pacotes_obrigatorios:
        try:
            importlib.import_module(mod_nome)
            diagnosticos.append(ItemDiagnostico(
                categoria="Pacotes Núcleo",
                item=descricao,
                status="OK",
                detalhes="Instalado e operacional"
            ))
        except ImportError:
            diagnosticos.append(ItemDiagnostico(
                categoria="Pacotes Núcleo",
                item=descricao,
                status="FALHA",
                detalhes="Não encontrado no ambiente Python atual"
            ))

    pacotes_opcionais = [
        ("pandas", "Pandas & OpenPyXL (Planilhas Excel)", ["pandas", "openpyxl"]),
        ("pypdf", "PyPDF (Leitura e Extração de Documentos)", ["pypdf"]),
        ("playwright", "Playwright (Automação Web Moderna)", ["playwright"]),
        ("selenium", "Selenium (Automação Web Clássica)", ["selenium"]),
        ("sqlalchemy", "SQLAlchemy (Bancos Corporativos)", ["sqlalchemy"]),
        ("openai", "OpenAI / LLMs (IA Cognitiva)", ["openai"]),
    ]

    for chave, descricao, modulos in pacotes_opcionais:
        instalados = []
        faltantes = []
        for m in modulos:
            try:
                importlib.import_module(m)
                instalados.append(m)
            except ImportError:
                faltantes.append(m)

        if not faltantes:
            diagnosticos.append(ItemDiagnostico(
                categoria="Conectores de Automação",
                item=descricao,
                status="OK",
                detalhes="Instalado e pronto para uso"
            ))
        elif instalados:
            diagnosticos.append(ItemDiagnostico(
                categoria="Conectores de Automação",
                item=descricao,
                status="AVISO",
                detalhes=f"Parcial: {', '.join(instalados)} instalado(s); falta {', '.join(faltantes)}"
            ))
        else:
            diagnosticos.append(ItemDiagnostico(
                categoria="Conectores de Automação",
                item=descricao,
                status="AVISO",
                detalhes="Não instalado (opcional - instale via pip se for utilizar)"
            ))

    # 4. Checagem do Projeto Local (se estiver em uma pasta de robô)
    pasta = diretorio_atual or Path.cwd()
    arquivo_fluxo = pasta / "metadados" / "fluxo.yaml"
    if arquivo_fluxo.is_file():
        from pyrpa.core.validator import validar_arquivo_fluxo
        try:
            esquema = validar_arquivo_fluxo(arquivo_fluxo)
            diagnosticos.append(ItemDiagnostico(
                categoria="Projeto Local",
                item=f"Robô '{esquema.fluxo.nome}'",
                status="OK",
                detalhes=f"Contrato válido com {len(esquema.fluxo.passos)} etapa(s) registrada(s)"
            ))
        except Exception as exc:
            diagnosticos.append(ItemDiagnostico(
                categoria="Projeto Local",
                item="Validação de Fluxo",
                status="FALHA",
                detalhes=f"Erro no fluxo.yaml: {exc}"
            ))

        arquivo_env = pasta / ".env"
        if arquivo_env.is_file():
            diagnosticos.append(ItemDiagnostico(
                categoria="Projeto Local",
                item="Configuração de Ambiente",
                status="OK",
                detalhes="Arquivo .env encontrado no projeto"
            ))
        else:
            diagnosticos.append(ItemDiagnostico(
                categoria="Projeto Local",
                item="Configuração de Ambiente",
                status="AVISO",
                detalhes="Arquivo .env não encontrado na raiz do projeto"
            ))

    return diagnosticos
