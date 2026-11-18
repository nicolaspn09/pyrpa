from pathlib import Path
from unittest.mock import MagicMock, patch

from pyrpa.core.installer import (
    garantir_dependencias_modulos,
    gerar_conteudo_requirements,
    listar_pacotes_pip_modulos,
    registrar_dependencias_requirements,
)


def test_listar_pacotes_completo_sem_duplicidade():
    pacotes = listar_pacotes_pip_modulos({"web", "banco", "excel", "pdf", "ia", "email"})
    assert len(pacotes) == len(set(pacotes))
    for esperado in ("python-dotenv", "pandas", "openpyxl", "sqlalchemy", "playwright", "selenium", "pypdf", "openai"):
        assert any(p.startswith(esperado) for p in pacotes)


def test_gerar_requirements_descomentado_e_sem_colisao_pypi():
    conteudo = gerar_conteudo_requirements({"web", "banco", "excel", "pdf", "ia", "email"})
    assert "pyrpa>=0.1.0" not in conteudo
    assert "pyrpa @ git+https://github.com/nicolaspn09/pyrpa.git" in conteudo
    assert "\nplaywright>=" in conteudo
    assert "\nselenium>=" in conteudo
    assert "\nsqlalchemy>=" in conteudo
    assert "\nopenai>=" in conteudo
    assert "# playwright" not in conteudo


def test_registrar_dependencias_requirements_sem_duplicar(tmp_path: Path):
    req = tmp_path / "requirements.txt"
    req.write_text(gerar_conteudo_requirements({"banco"}), encoding="utf-8")

    registrar_dependencias_requirements(req, {"pdf", "banco"})
    conteudo = req.read_text(encoding="utf-8")

    assert conteudo.count("sqlalchemy>=") == 1
    assert "pypdf>=5.0.0" in conteudo


def test_garantir_dependencias_ja_instaladas():
    with patch("pyrpa.core.installer.importlib.util.find_spec", return_value=object()):
        res = garantir_dependencias_modulos({"web", "pdf"}, instalar_automaticamente=True)
    assert res.falhas == []
    assert res.instalados_agora == []
    assert len(res.ja_instalados) > 0


def test_garantir_dependencias_instala_faltante_via_pip():
    def fake_find_spec(nome: str):
        return None if nome == "pypdf" else object()

    mock_proc = MagicMock(returncode=0, stdout="Successfully installed pypdf", stderr="")
    with patch("pyrpa.core.installer.importlib.util.find_spec", side_effect=fake_find_spec), \
         patch("pyrpa.core.installer.subprocess.run", return_value=mock_proc) as mock_run:
        res = garantir_dependencias_modulos({"pdf"}, instalar_automaticamente=True, incluir_base=False)

    mock_run.assert_called_once()
    args_cmd = mock_run.call_args[0][0]
    assert "-m" in args_cmd and "pip" in args_cmd and "pypdf>=5.0.0" in args_cmd
    assert res.instalados_agora == ["pypdf>=5.0.0"]
    assert res.falhas == []


def test_garantir_dependencias_trata_pep668_linux():
    mock_proc = MagicMock(returncode=1, stdout="", stderr="error: externally-managed-environment")
    with patch("pyrpa.core.installer.importlib.util.find_spec", return_value=None), \
         patch("pyrpa.core.installer.subprocess.run", return_value=mock_proc):
        res = garantir_dependencias_modulos({"pdf"}, instalar_automaticamente=True, incluir_base=False)

    assert res.falhas == ["pypdf>=5.0.0"]
    assert "PEP 668" in res.erro_detalhe
