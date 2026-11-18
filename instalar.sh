#!/usr/bin/env bash
set -e

echo "=========================================="
echo "  Instalador Oficial - Framework pyrpa"
echo "=========================================="

PY_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "[ERRO] Python 3.10+ nao encontrado."
    echo "No Ubuntu/Debian, instale com:"
    echo "  sudo apt update && sudo apt install -y python3 python3-pip python3-venv"
    exit 1
fi

if ! "$PY_CMD" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "[ERRO] Versao do Python inferior a 3.10."
    "$PY_CMD" --version
    echo "Instale Python 3.10 ou superior antes de continuar."
    exit 1
fi

if ! "$PY_CMD" -m venv --help >/dev/null 2>&1; then
    echo "[ERRO] Modulo python3-venv ausente neste sistema."
    echo "No Ubuntu/Debian, execute:"
    echo "  sudo apt update && sudo apt install -y python3-venv"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -z "${VIRTUAL_ENV:-}" ]; then
    if [ ! -d ".venv" ]; then
        echo ">> Criando ambiente virtual isolado (.venv)..."
        "$PY_CMD" -m venv .venv
    fi
    VENV_PY="$SCRIPT_DIR/.venv/bin/python"
    VENV_PYRPA="$SCRIPT_DIR/.venv/bin/pyrpa"
else
    VENV_PY="$VIRTUAL_ENV/bin/python"
    VENV_PYRPA="$VIRTUAL_ENV/bin/pyrpa"
fi

echo ">> Atualizando pip e setuptools..."
"$VENV_PY" -m pip install --upgrade pip "setuptools>=64.0" wheel

echo ">> Instalando pyrpa e todas as bibliotecas dos conectores..."
"$VENV_PY" -m pip install -e .

if [ -z "${VIRTUAL_ENV:-}" ]; then
    mkdir -p "$HOME/.local/bin"
    ln -sf "$VENV_PYRPA" "$HOME/.local/bin/pyrpa"
    echo "[OK] Atalho global criado em: $HOME/.local/bin/pyrpa"
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *)
            echo "[AVISO] Para usar 'pyrpa' direto em qualquer pasta, adicione ~/.local/bin ao PATH ou rode:"
            echo "  source \"$SCRIPT_DIR/.venv/bin/activate\""
            ;;
    esac
fi

echo ""
echo ">> Executando verificacao final (pyrpa doctor)..."
"$VENV_PYRPA" doctor

echo ""
echo "[OK] Instalacao concluida! Em caso de duvida, teste com:"
echo "  pyrpa --help"
