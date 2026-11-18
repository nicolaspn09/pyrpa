@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Instalador Oficial - Framework pyrpa
echo ==========================================

set "PY_CMD="
where python >nul 2>nul && (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY_CMD=python"
)
if not defined PY_CMD (
    where py >nul 2>nul && (
        py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY_CMD=py -3"
    )
)

if not defined PY_CMD (
    echo [ERRO] Python 3.10 ou superior nao encontrado neste Windows.
    echo Baixe em https://www.python.org/downloads/ marcando "Add python.exe to PATH".
    pause
    exit /b 1
)

echo ^>^> Atualizando pip e setuptools...
%PY_CMD% -m pip install --upgrade pip "setuptools>=64.0" wheel

echo ^>^> Instalando pyrpa e todas as bibliotecas dos conectores...
%PY_CMD% -m pip install -e .
if errorlevel 1 (
    echo [ERRO] Falha durante a instalacao das bibliotecas via pip.
    pause
    exit /b 1
)

where pyrpa >nul 2>nul
if errorlevel 1 (
    echo.
    echo [AVISO] A pasta Scripts do Python nao esta no PATH deste terminal.
    echo ^>^> Tentando adicionar automaticamente ao PATH do usuario...
    for /f "delims=" %%i in ('%PY_CMD% -c "import sysconfig; print(sysconfig.get_path('scripts'))"') do set "SYS_SCRIPTS=%%i"
    for /f "delims=" %%i in ('%PY_CMD% -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"') do set "USR_SCRIPTS=%%i"
    powershell -NoProfile -Command "$p = [Environment]::GetEnvironmentVariable('Path', 'User'); $add = @('%SYS_SCRIPTS%', '%USR_SCRIPTS%') | Where-Object { $_ -and (Test-Path $_) -and ($p -notlike ('*' + $_ + '*')) }; if ($add) { [Environment]::SetEnvironmentVariable('Path', ($p.TrimEnd(';') + ';' + ($add -join ';')), 'User'); Write-Host '[OK] PATH atualizado! Reabra o terminal depois para usar pyrpa direto.' }"
)

echo.
echo ^>^> Executando verificacao final (pyrpa doctor)...
%PY_CMD% -m pyrpa doctor

echo.
echo [OK] Instalacao concluida!
echo Caso 'pyrpa' nao abra imediatamente nesta janela, feche e abra um novo PowerShell.
endlocal
