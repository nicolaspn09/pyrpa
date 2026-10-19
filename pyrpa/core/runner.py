from dataclasses import dataclass, field
import importlib
from pathlib import Path
import sys
import time
from typing import Any, Dict, Optional, Union

from pyrpa.core.validator import validar_arquivo_fluxo
from pyrpa.domain.contracts import BaseUseCase, ContextoExecucao, ResultadoPasso
from pyrpa.infrastructure.logger import RPAAuditLogger


class ExecucaoFluxoException(Exception):
    """Exceção lançada em falhas críticas de orquestração do runner."""
    pass


@dataclass
class ResultadoFluxo:
    """Consolidado final da execução de um fluxo pelo runner."""
    nome_fluxo: str
    versao: str
    sucesso: bool
    passos_executados: int
    total_passos: int
    resultados_passos: Dict[str, ResultadoPasso] = field(default_factory=dict)
    duracao_total_segundos: float = 0.0
    erro: Optional[str] = None


class FluxoRunner:
    """
    Motor de execução sequencial opinativo do pyrpa.
    Lê o fluxo declarativo YAML, valida contratos, carrega dinamicamente
    as classes UseCase via importlib e coordena a passagem de dados via ContextoExecucao.
    """

    def __init__(self, logger: Optional[RPAAuditLogger] = None) -> None:
        self.logger = logger or RPAAuditLogger(nome_robo="pyrpa_runner")

    def executar(
        self,
        caminho_fluxo: Union[str, Path],
        diretorio_projeto: Optional[Path] = None,
        contexto_inicial: Optional[ContextoExecucao] = None,
    ) -> ResultadoFluxo:
        inicio_total = time.perf_counter()
        caminho = Path(caminho_fluxo).resolve()

        if not caminho.is_file():
            raise FileNotFoundError(f"Arquivo de fluxo não encontrado: {caminho}")

        # Determina a raiz do projeto para resolução dinâmica de módulos
        raiz = diretorio_projeto.resolve() if diretorio_projeto else caminho.parent.parent
        str_raiz = str(raiz)
        if str_raiz not in sys.path:
            sys.path.insert(0, str_raiz)

        # Evita conflitos de cache do sys.modules quando múltiplos projetos ou testes rodam no mesmo processo
        for mod_chave in list(sys.modules.keys()):
            if mod_chave == "application" or mod_chave.startswith("application."):
                mod = sys.modules.get(mod_chave)
                mod_file = getattr(mod, "__file__", None)
                if mod_file:
                    try:
                        if not Path(mod_file).resolve().is_relative_to(raiz):
                            sys.modules.pop(mod_chave, None)
                    except (ValueError, TypeError):
                        sys.modules.pop(mod_chave, None)

        # Validação do fluxo pelo validador oficial
        esquema = validar_arquivo_fluxo(caminho)
        fluxo = esquema.fluxo
        contexto = contexto_inicial or ContextoExecucao()

        self.logger.info(f"Iniciando execução do robô: {fluxo.nome} (v{fluxo.versao})", etapa="inicializacao")
        resultados_passos: Dict[str, ResultadoPasso] = {}

        for passo in fluxo.passos:
            self.logger.definir_etapa(passo.id)
            self.logger.info(f">> Executando etapa [{passo.id}]: {passo.nome} (Provider: {passo.provider.value})")

            inicio_passo = time.perf_counter()
            resultado: ResultadoPasso

            try:
                # Resolução dinâmica da classe do UseCase
                modulo_nome, classe_nome = passo.target.rsplit(".", 1)
                if modulo_nome in sys.modules:
                    try:
                        modulo = importlib.reload(sys.modules[modulo_nome])
                    except Exception:
                        modulo = importlib.import_module(modulo_nome)
                else:
                    modulo = importlib.import_module(modulo_nome)

                classe_use_case = getattr(modulo, classe_nome)

                if not isinstance(classe_use_case, type):
                    raise ExecucaoFluxoException(f"O target '{passo.target}' não é uma classe válida.")

                instancia_use_case = classe_use_case()

                if not hasattr(instancia_use_case, "executar") or not callable(instancia_use_case.executar):
                    raise ExecucaoFluxoException(
                        f"A classe '{classe_nome}' deve implementar o método 'executar(contexto)'."
                    )

                resultado = instancia_use_case.executar(contexto)

                if not isinstance(resultado, ResultadoPasso):
                    resultado = ResultadoPasso(
                        sucesso=True,
                        mensagem="Etapa concluída sem retorno padronizado.",
                        dados={"retorno_bruto": resultado},
                    )

            except Exception as exc:
                duracao = round(time.perf_counter() - inicio_passo, 3)
                mensagem_erro = f"Falha na execução do passo '{passo.id}': {exc}"
                self.logger.error(mensagem_erro, exc_info=True)
                resultado_falha = ResultadoPasso(
                    sucesso=False,
                    mensagem=mensagem_erro,
                    duracao_segundos=duracao,
                )
                resultados_passos[passo.id] = resultado_falha
                contexto.registrar_resultado_passo(passo.id, resultado_falha)

                duracao_total = round(time.perf_counter() - inicio_total, 3)
                return ResultadoFluxo(
                    nome_fluxo=fluxo.nome,
                    versao=fluxo.versao,
                    sucesso=False,
                    passos_executados=len(resultados_passos),
                    total_passos=len(fluxo.passos),
                    resultados_passos=resultados_passos,
                    duracao_total_segundos=duracao_total,
                    erro=mensagem_erro,
                )

            duracao = round(time.perf_counter() - inicio_passo, 3)
            resultado.duracao_segundos = duracao
            resultados_passos[passo.id] = resultado
            contexto.registrar_resultado_passo(passo.id, resultado)

            if not resultado.sucesso:
                self.logger.error(f"[FALHA] Etapa [{passo.id}] falhou: {resultado.mensagem}")
                duracao_total = round(time.perf_counter() - inicio_total, 3)
                return ResultadoFluxo(
                    nome_fluxo=fluxo.nome,
                    versao=fluxo.versao,
                    sucesso=False,
                    passos_executados=len(resultados_passos),
                    total_passos=len(fluxo.passos),
                    resultados_passos=resultados_passos,
                    duracao_total_segundos=duracao_total,
                    erro=resultado.mensagem,
                )

            self.logger.info(f"[OK] Etapa [{passo.id}] concluída com sucesso em {duracao}s")

        duracao_total = round(time.perf_counter() - inicio_total, 3)
        self.logger.info(f"Fluxo '{fluxo.nome}' finalizado com sucesso em {duracao_total}s", etapa="finalizacao")

        return ResultadoFluxo(
            nome_fluxo=fluxo.nome,
            versao=fluxo.versao,
            sucesso=True,
            passos_executados=len(resultados_passos),
            total_passos=len(fluxo.passos),
            resultados_passos=resultados_passos,
            duracao_total_segundos=duracao_total,
        )


def executar_fluxo(
    caminho_fluxo: Union[str, Path],
    diretorio_projeto: Optional[Path] = None,
    contexto_inicial: Optional[ContextoExecucao] = None,
) -> ResultadoFluxo:
    """Função utilitária para acionamento direto do motor de execução."""
    runner = FluxoRunner()
    return runner.executar(caminho_fluxo, diretorio_projeto, contexto_inicial)
