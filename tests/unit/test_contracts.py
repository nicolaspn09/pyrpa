import pytest
from pyrpa.domain.contracts import (
    BaseUseCase,
    ChaveContextoNaoEncontradaException,
    ContextoExecucao,
    ResultadoPasso,
)


def test_contexto_execucao_deve_armazenar_e_recuperar_valores():
    ctx = ContextoExecucao()
    ctx.definir("total_faturas", 42)
    ctx.definir("nome_cliente", "Empresa Exemplo")

    assert ctx.obter("total_faturas") == 42
    assert ctx.obter("nome_cliente") == "Empresa Exemplo"
    assert ctx.obter("inexistente", padrao=100) == 100
    assert ctx.contem("total_faturas") is True
    assert ctx.contem("inexistente") is False


def test_contexto_obter_obrigatorio_deve_lancar_excecao_quando_chave_nao_existir():
    ctx = ContextoExecucao()
    with pytest.raises(ChaveContextoNaoEncontradaException):
        ctx.obter_obrigatorio("chave_ausente")


def test_contexto_deve_registrar_e_limpar_historico():
    ctx = ContextoExecucao()
    resultado = ResultadoPasso(sucesso=True, mensagem="Etapa OK", duracao_segundos=1.5)
    ctx.registrar_resultado_passo("etapa_1", resultado)

    assert "etapa_1" in ctx.historico_passos
    assert ctx.historico_passos["etapa_1"].sucesso is True

    ctx.limpar()
    assert len(ctx.obter_todos()) == 0
    assert len(ctx.historico_passos) == 0


def test_base_use_case_deve_exigir_implementacao_do_metodo_executar():
    class UseCaseInvalido(BaseUseCase):
        pass

    with pytest.raises(TypeError):
        UseCaseInvalido()  # type: ignore

    class UseCaseValido(BaseUseCase):
        def executar(self, contexto: ContextoExecucao) -> ResultadoPasso:
            return ResultadoPasso(sucesso=True, mensagem="Executado com sucesso")

    instancia = UseCaseValido()
    res = instancia.executar(ContextoExecucao())
    assert res.sucesso is True
