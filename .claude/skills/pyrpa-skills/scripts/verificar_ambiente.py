#!/usr/bin/env python3
"""Checklist de ambiente da skill pyrpa-skills.

SOMENTE LEITURA: diagnostica e imprime o comando que resolve cada item.
Nunca instala nada e nunca imprime o valor de segredos do .env (só informa se a chave está preenchida).

Uso:
    python verificar_ambiente.py --modulos web,excel,email [--projeto PASTA] [--engine playwright|selenium|undetected_chromedriver] [--json]

Saída: uma linha por item com [OK], [FALTA], [AVISO] ou [INFO]. Código de saída 0 se não houver
[FALTA]; 1 caso contrário. Rode com o Python do ambiente virtual do projeto para o resultado valer
para aquele ambiente.
"""
from __future__ import annotations

import argparse
import importlib.metadata as md
import importlib.util
import json
import os
import platform
import shutil
import sys
from pathlib import Path

MODULOS_VALIDOS = {"web", "banco", "excel", "pdf", "ia", "email"}
ENGINES_VALIDOS = {"playwright", "selenium", "undetected_chromedriver"}
REPO_PYRPA_GIT = "git+https://github.com/nicolaspn09/pyrpa.git"
PIP = "python -m pip"

itens: list[dict] = []


def add(grupo: str, item: str, status: str, detalhe: str = "", correcao: str = "") -> None:
    itens.append({"grupo": grupo, "item": item, "status": status, "detalhe": detalhe, "correcao": correcao})


def tem_modulo(nome: str) -> bool:
    try:
        return importlib.util.find_spec(nome) is not None
    except (ImportError, ValueError):
        return False


def versao_pacote(nome: str) -> str | None:
    try:
        return md.version(nome)
    except md.PackageNotFoundError:
        return None


def navegador_instalado(nome: str) -> bool:
    if platform.system() == "Windows":
        pastas = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        rel = {
            "chrome": Path("Google") / "Chrome" / "Application" / "chrome.exe",
            "edge": Path("Microsoft") / "Edge" / "Application" / "msedge.exe",
            "firefox": Path("Mozilla Firefox") / "firefox.exe",
        }[nome]
        if any(p and (Path(p) / rel).is_file() for p in pastas):
            return True
        return shutil.which({"chrome": "chrome", "edge": "msedge", "firefox": "firefox"}[nome]) is not None
    candidatos = {"chrome": ["google-chrome", "chrome", "chromium"], "edge": ["microsoft-edge", "msedge"], "firefox": ["firefox"]}[nome]
    return any(shutil.which(c) for c in candidatos)


def playwright_browsers_baixados() -> bool:
    bases = []
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH") and os.environ["PLAYWRIGHT_BROWSERS_PATH"] != "0":
        bases.append(Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"]))
    if platform.system() == "Windows":
        bases.append(Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright")
    elif platform.system() == "Darwin":
        bases.append(Path.home() / "Library" / "Caches" / "ms-playwright")
    else:
        bases.append(Path.home() / ".cache" / "ms-playwright")
    return any(b.is_dir() and any(p.name.startswith("chromium") for p in b.iterdir()) for b in bases)


def ler_env(arquivo: Path) -> dict[str, str]:
    """Lê o .env sem expor valores: devolve chave -> valor, mas o valor só é usado internamente."""
    dados: dict[str, str] = {}
    try:
        for linha in arquivo.read_text(encoding="utf-8", errors="replace").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, _, valor = linha.partition("=")
            dados[chave.strip()] = valor.strip().strip('"').strip("'")
    except OSError:
        pass
    return dados


def verificar_base() -> None:
    v = sys.version_info
    versao = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 11):
        add("A. Base", "Python 3.11 ou superior", "OK", f"Python {versao} em {sys.executable}")
    else:
        add("A. Base", "Python 3.11 ou superior", "FALTA", f"Python {versao}",
            "Instalar Python 3.11+ (python.org ou procedimento da empresa). A skill não instala o Python.")

    em_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if em_venv:
        add("A. Base", "Ambiente virtual ativo (.venv)", "OK", f"venv em {sys.prefix}")
    else:
        add("A. Base", "Ambiente virtual ativo (.venv)", "FALTA",
            "Este Python é o global do computador; instalar pacotes aqui não é permitido pela skill.",
            "python -m venv .venv   (depois rode este script com .venv\\Scripts\\python no Windows ou .venv/bin/python no Linux/macOS)")

    if tem_modulo("pip"):
        add("A. Base", "pip disponível", "OK", f"pip {versao_pacote('pip') or ''}".strip())
    else:
        add("A. Base", "pip disponível", "FALTA", "", "python -m ensurepip --upgrade")


def verificar_framework() -> None:
    v = versao_pacote("pyrpa")
    caminho_cli = shutil.which("pyrpa")
    if v and tem_modulo("pyrpa"):
        add("B. Framework", "pyrpa instalado", "OK", f"versão {v}" + (f", comando em {caminho_cli}" if caminho_cli else ""))
        if v != "0.1.0":
            add("B. Framework", "Versão do pyrpa conhecida pela skill", "AVISO",
                f"A skill foi escrita para a 0.1.0 e aqui está a {v}. Comandos e contratos podem ter mudado.",
                "Avisar o usuário antes de seguir.")
        else:
            add("B. Framework", "Versão do pyrpa conhecida pela skill", "OK", "0.1.0")
        if not caminho_cli:
            add("B. Framework", "Comando `pyrpa` no PATH", "AVISO",
                "O pacote está instalado, mas o comando não está no PATH deste ambiente.",
                "Use `python -m pyrpa.cli ...` ou ative o ambiente virtual.")
    else:
        add("B. Framework", "pyrpa instalado", "FALTA", "Pacote pyrpa não encontrado neste ambiente.",
            f"{PIP} install -e <pasta-do-repositorio-pyrpa>   OU   {PIP} install {REPO_PYRPA_GIT}   "
            "(o pyrpa não está no PyPI; o repositório exige login feito pelo usuário na janela do Git)")

    if v and tem_modulo("pyrpa"):
        # A versão (0.1.0) é a mesma em cópias antigas e novas do framework: confira os recursos.
        recursos = {
            "motor de execução (pyrpa run)": "pyrpa.core.runner",
            "contratos BaseUseCase/ContextoExecucao": "pyrpa.domain.contracts",
            "adicionar módulos (pyrpa add)": "pyrpa.core.modifier",
            "compilador do Airflow (pyrpa compile)": "pyrpa.core.compiler",
        }
        ausentes = []
        for nome, mod in recursos.items():
            try:
                ok = importlib.util.find_spec(mod) is not None
            except (ImportError, ValueError):
                ok = False
            if not ok:
                ausentes.append(nome)
        if ausentes:
            add("B. Framework", "pyrpa com os recursos esperados pela skill", "FALTA",
                "O pyrpa instalado é uma cópia antiga: faltam " + "; ".join(ausentes) + ".",
                "Atualizar o repositório do pyrpa (git fetch/pull da branch main) e reinstalar: "
                f"{PIP} install -e <pasta-do-repositorio-pyrpa>")
        else:
            add("B. Framework", "pyrpa com os recursos esperados pela skill", "OK", "run, add, compile e contratos presentes")

    nucleo = [("typer", "typer", None), ("rich", "rich", None), ("pydantic", "pydantic", 2),
              ("yaml", "pyyaml", None), ("jinja2", "jinja2", None), ("dotenv", "python-dotenv", None)]
    faltam = []
    for mod, pacote, major_min in nucleo:
        if not tem_modulo(mod):
            faltam.append(pacote)
            continue
        if major_min:
            ver = versao_pacote(pacote) or "0"
            try:
                if int(ver.split(".")[0]) < major_min:
                    faltam.append(f"{pacote}>={major_min}")
            except ValueError:
                pass
    if faltam:
        add("B. Framework", "Núcleo (typer, rich, pydantic>=2, pyyaml, jinja2, python-dotenv)", "FALTA",
            "Faltando: " + ", ".join(faltam),
            f"{PIP} install " + " ".join(f'"{p}"' if ">" in p else p for p in faltam))
    else:
        add("B. Framework", "Núcleo (typer, rich, pydantic>=2, pyyaml, jinja2, python-dotenv)", "OK", "todos presentes")


def verificar_modulos(modulos: set[str], engine: str) -> None:
    g = "C. Pacotes por módulo"
    if "excel" in modulos:
        falta = [p for m, p in (("pandas", "pandas"), ("openpyxl", "openpyxl")) if not tem_modulo(m)]
        if falta:
            add(g, "excel: pandas + openpyxl", "FALTA", "Faltando: " + ", ".join(falta), f"{PIP} install " + " ".join(falta))
        else:
            add(g, "excel: pandas + openpyxl", "OK", "instalados")
    if "pdf" in modulos:
        if tem_modulo("pypdf"):
            add(g, "pdf: pypdf", "OK", "instalado")
        else:
            add(g, "pdf: pypdf", "FALTA", "", f"{PIP} install pypdf")
    if "web" in modulos:
        if engine == "playwright":
            if not tem_modulo("playwright"):
                add(g, "web: playwright", "FALTA", "", f"{PIP} install playwright   e depois   python -m playwright install chromium (download grande: avisar o usuário)")
            else:
                add(g, "web: playwright (pacote)", "OK", f"versão {versao_pacote('playwright') or '?'}")
                if playwright_browsers_baixados():
                    add(g, "web: navegador do Playwright (chromium)", "OK", "baixado")
                else:
                    add(g, "web: navegador do Playwright (chromium)", "FALTA",
                        "Pacote instalado, mas o navegador do Playwright ainda não foi baixado.",
                        "python -m playwright install chromium   (download de centenas de MB: avisar o usuário)")
        elif engine == "selenium":
            if tem_modulo("selenium"):
                add(g, "web: selenium", "OK", f"versão {versao_pacote('selenium') or '?'}")
            else:
                add(g, "web: selenium", "FALTA", "", f"{PIP} install selenium")
            if any(navegador_instalado(n) for n in ("chrome", "edge", "firefox")):
                add(g, "web: navegador instalado no computador", "OK", "Chrome, Edge ou Firefox encontrado")
            else:
                add(g, "web: navegador instalado no computador", "FALTA", "Nenhum navegador encontrado nos caminhos padrão.",
                    "Instalar Chrome, Edge ou Firefox (procedimento da empresa).")
        else:  # undetected_chromedriver
            falta = [p for m, p in (("undetected_chromedriver", "undetected-chromedriver"), ("selenium", "selenium")) if not tem_modulo(m)]
            if falta:
                add(g, "web: undetected-chromedriver + selenium", "FALTA", "Faltando: " + ", ".join(falta), f"{PIP} install " + " ".join(falta))
            else:
                add(g, "web: undetected-chromedriver + selenium", "OK", "instalados")
            if navegador_instalado("chrome"):
                add(g, "web: Google Chrome instalado", "OK", "encontrado")
            else:
                add(g, "web: Google Chrome instalado", "FALTA", "", "Instalar o Google Chrome (procedimento da empresa).")
    if "banco" in modulos:
        if tem_modulo("sqlalchemy"):
            add(g, "banco: sqlalchemy", "OK", f"versão {versao_pacote('sqlalchemy') or '?'} (confirme também o driver do banco)")
        else:
            add(g, "banco: sqlalchemy", "AVISO",
                "Sem SQLAlchemy só o SQLite local funciona. Para PostgreSQL/SQL Server/MySQL é preciso instalar.",
                f"{PIP} install sqlalchemy   + driver do banco (ex.: psycopg2-binary, pyodbc). Perguntar ao usuário qual banco.")
    if "ia" in modulos:
        add(g, "ia: pacotes", "OK", "usa só a biblioteca padrão; nenhum pacote extra")
    if "email" in modulos:
        add(g, "email: pacotes", "OK", "usa só a biblioteca padrão; nenhum pacote extra")


def verificar_projeto(pasta: Path, modulos: set[str]) -> None:
    g = "D. Projeto e configuração"
    if not pasta.is_dir():
        add(g, "Pasta do projeto", "FALTA", f"{pasta} não existe.", "Criar o projeto com `pyrpa init <nome> --destino <pasta> --modulos <lista>`.")
        return
    fluxo = pasta / "metadados" / "fluxo.yaml"
    if fluxo.is_file():
        add(g, "metadados/fluxo.yaml", "OK", "encontrado (confirme com `pyrpa validate`)")
    else:
        add(g, "metadados/fluxo.yaml", "FALTA", "Não é um projeto pyrpa (sem metadados/fluxo.yaml).",
            "`pyrpa init <nome> --destino <pasta> --modulos <lista>`. Se a pasta já tem projeto, indique a pasta raiz certa.")
    env = pasta / ".env"
    if not env.is_file():
        add(g, ".env", "FALTA", "Arquivo .env não encontrado na raiz do robô.",
            "O `pyrpa init` já o cria. Não coloque segredos no chat: o usuário preenche o arquivo.")
        return
    add(g, ".env", "OK", "encontrado (valores nunca são exibidos)")
    cfg = ler_env(env)

    def preenchido(chave: str) -> bool:
        return bool(cfg.get(chave, "").strip())

    if "web" in modulos:
        motor = cfg.get("BROWSER_ENGINE", "").lower()
        if motor in ("", "simulacao"):
            add(g, "BROWSER_ENGINE (modo de simulação)", "AVISO",
                "O navegador está em modo simulação: não abre de verdade.",
                "Para rodar de verdade, o usuário define BROWSER_ENGINE como playwright, selenium ou undetected_chromedriver no .env. Perguntar antes.")
        else:
            add(g, "BROWSER_ENGINE", "OK", f"motor: {motor}")
    if "email" in modulos:
        faltam = [k for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD") if not preenchido(k)]
        if faltam:
            add(g, "e-mail: SMTP no .env", "FALTA", "Chaves vazias ou ausentes: " + ", ".join(faltam),
                "O USUÁRIO preenche essas chaves no .env (nunca no chat). Sem elas, enviar_email devolve False.")
        else:
            add(g, "e-mail: SMTP no .env", "OK", "chaves preenchidas (valores não exibidos)")
    if "ia" in modulos:
        if preenchido("AI_API_KEY") or preenchido("OPENAI_API_KEY"):
            add(g, "ia: chave no .env", "OK", "chave preenchida (valor não exibido)")
        elif cfg.get("AI_SIMULACAO", "").lower() in ("true", "1", "yes"):
            add(g, "ia: chave no .env", "AVISO", "AI_SIMULACAO ativo: as respostas da IA serão simuladas.", "")
        else:
            add(g, "ia: chave no .env", "AVISO",
                "Sem AI_API_KEY, o adaptador cai em resposta simulada.",
                "O USUÁRIO preenche AI_API_KEY no .env, ou aceita testar em simulação.")
    if "banco" in modulos:
        if preenchido("DB_URL"):
            add(g, "banco: DB_URL no .env", "OK", "preenchido (valor não exibido)")
        else:
            add(g, "banco: DB_URL no .env", "AVISO", "DB_URL ausente: o padrão é um SQLite local (dados_rpa.db).", "")
    gi = pasta / ".gitignore"
    if gi.is_file() and ".env" in gi.read_text(encoding="utf-8", errors="replace").splitlines():
        add(g, ".env fora do Git", "OK", ".gitignore ignora o .env")
    else:
        add(g, ".env fora do Git", "AVISO", "O .gitignore não lista o .env.", "Acrescentar `.env` ao .gitignore antes de versionar.")


def imprimir(resultado: list[dict]) -> None:
    grupo_atual = None
    for it in resultado:
        if it["grupo"] != grupo_atual:
            grupo_atual = it["grupo"]
            print(f"\n== {grupo_atual} ==")
        print(f"[{it['status']}] {it['item']}" + (f": {it['detalhe']}" if it["detalhe"] else ""))
        if it["correcao"] and it["status"] in ("FALTA", "AVISO"):
            print(f"        -> {it['correcao']}")
    falta = sum(1 for i in resultado if i["status"] == "FALTA")
    aviso = sum(1 for i in resultado if i["status"] == "AVISO")
    print("\n-- Resumo --")
    print(f"FALTA: {falta} | AVISO: {aviso} | OK: {sum(1 for i in resultado if i['status'] == 'OK')}")
    print("Pronto para seguir." if falta == 0 else "Ainda há itens [FALTA]: resolva (com o ok do usuário) e rode de novo.")
    print("Próximo passo depois de tudo OK: rodar `pyrpa doctor` (dentro da pasta do robô).")


def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Checklist de ambiente (somente leitura) da skill pyrpa-skills.")
    ap.add_argument("--modulos", default="", help="módulos do pedido, separados por vírgula: " + ", ".join(sorted(MODULOS_VALIDOS)))
    ap.add_argument("--projeto", default=None, help="pasta do robô (opcional)")
    ap.add_argument("--engine", default="playwright", choices=sorted(ENGINES_VALIDOS), help="motor web (padrão: playwright)")
    ap.add_argument("--json", action="store_true", help="saída em JSON")
    args = ap.parse_args()

    modulos = {m.strip().lower() for m in args.modulos.split(",") if m.strip()}
    if "completo" in modulos:
        modulos = set(MODULOS_VALIDOS)
    invalidos = modulos - MODULOS_VALIDOS
    if invalidos:
        print(f"Módulos desconhecidos: {', '.join(sorted(invalidos))}. Válidos: {', '.join(sorted(MODULOS_VALIDOS))}.", file=sys.stderr)
        return 2

    verificar_base()
    verificar_framework()
    verificar_modulos(modulos, args.engine)
    if args.projeto:
        verificar_projeto(Path(args.projeto).expanduser().resolve(), modulos)

    if args.json:
        print(json.dumps({"python": platform.python_version(), "pyrpa": versao_pacote("pyrpa"), "itens": itens}, ensure_ascii=False, indent=2))
    else:
        print(f"Python {platform.python_version()} | pyrpa {versao_pacote('pyrpa') or 'não instalado'} | {platform.system()} {platform.release()}")
        imprimir(itens)
    return 1 if any(i["status"] == "FALTA" for i in itens) else 0


if __name__ == "__main__":
    sys.exit(main())
