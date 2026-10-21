from pathlib import Path
from pyrpa.core.doctor import executar_diagnostico_doctor, verificar_navegador_instalado


def test_verificar_navegador_retorna_booleano():
    resultado_chrome = verificar_navegador_instalado("chrome")
    assert isinstance(resultado_chrome, bool)

    resultado_fantasma = verificar_navegador_instalado("navegador_inexistente_xyz_123")
    assert resultado_fantasma is False


def test_diagnostico_doctor_sistema_base():
    diagnosticos = executar_diagnostico_doctor()
    assert len(diagnosticos) > 0

    itens_por_nome = {item.item: item for item in diagnosticos}

    assert "Versão do Python" in itens_por_nome
    assert itens_por_nome["Versão do Python"].status == "OK"

    assert "Sistema Operacional" in itens_por_nome
    assert itens_por_nome["Sistema Operacional"].status == "OK"

    # Pacotes obrigatórios
    assert any("Typer" in item.item for item in diagnosticos)
    assert any("Pydantic" in item.item for item in diagnosticos)


def test_diagnostico_doctor_em_projeto_rpa(tmp_path: Path):
    from pyrpa.core.generator import gerar_projeto_rpa

    projeto_dir = tmp_path / "meu_robo"
    gerar_projeto_rpa("meu_robo", destino=projeto_dir)

    diagnosticos = executar_diagnostico_doctor(diretorio_atual=projeto_dir)
    itens_locais = [d for d in diagnosticos if d.categoria == "Projeto Local"]

    assert len(itens_locais) >= 2
    nomes_itens = [d.item for d in itens_locais]
    assert "Robô 'meu_robo'" in nomes_itens
    assert any(d.status == "OK" for d in itens_locais if d.item == "Robô 'meu_robo'")
