from contextlib import contextmanager
from dataclasses import dataclass
import os
from typing import Any, Generator, List, Optional


class BrowserAdapterException(Exception):
    """Exceção lançada em falhas de inicialização, navegação ou fechamento do navegador."""
    pass


@dataclass
class BrowserConfig:
    """
    Configuração padronizada para drivers de navegador em automações RPA.
    Suporta motores: playwright, selenium, undetected_chromedriver e simulacao.
    Suporta navegadores: chrome, firefox, edge.
    """
    engine: str = "playwright"
    browser_type: str = "chrome"
    headless: bool = True
    timeout_ms: int = 15000
    modo_simulacao: bool = False

    @classmethod
    def from_env(cls) -> "BrowserConfig":
        return cls(
            engine=os.getenv("BROWSER_ENGINE", "playwright").lower(),
            browser_type=os.getenv("BROWSER_TYPE", "chrome").lower(),
            headless=os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes"),
            timeout_ms=int(os.getenv("BROWSER_TIMEOUT_MS", "15000")),
            modo_simulacao=os.getenv("BROWSER_SIMULACAO", "false").lower() in ("true", "1", "yes"),
        )


class BrowserSession:
    """
    Sessão encapsulada de navegador que abstrai as diferenças entre Playwright, Selenium
    e Undetected-Chromedriver, garantindo fechamento seguro para evitar processos zumbis.
    """

    def __init__(self, config: BrowserConfig) -> None:
        self.config = config
        self._driver: Any = None
        self._playwright_ctx: Any = None
        self._browser_instance: Any = None
        self._fechado: bool = False
        self.historico_urls: List[str] = []

    def iniciar(self) -> "BrowserSession":
        engines_validos = {"playwright", "selenium", "undetected_chromedriver", "simulacao"}
        browsers_validos = {"chrome", "firefox", "edge"}

        if self.config.engine not in engines_validos:
            raise BrowserAdapterException(
                f"Motor de navegador inválido: '{self.config.engine}'. "
                f"Opções suportadas: {', '.join(sorted(engines_validos))}."
            )
        if self.config.browser_type not in browsers_validos:
            raise BrowserAdapterException(
                f"Tipo de navegador inválido: '{self.config.browser_type}'. "
                f"Opções suportadas: {', '.join(sorted(browsers_validos))}."
            )

        if self.config.modo_simulacao or self.config.engine == "simulacao":
            self._driver = {"simulacao": True, "browser": self.config.browser_type}
            return self

        if self.config.engine == "playwright":
            self._iniciar_playwright()
        elif self.config.engine == "selenium":
            self._iniciar_selenium()
        elif self.config.engine == "undetected_chromedriver":
            self._iniciar_undetected()

        return self

    def _iniciar_playwright(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
            self._playwright_ctx = sync_playwright().start()
            b_type = self.config.browser_type
            if b_type == "firefox":
                self._browser_instance = self._playwright_ctx.firefox.launch(headless=self.config.headless)
            elif b_type == "edge":
                self._browser_instance = self._playwright_ctx.chromium.launch(
                    channel="msedge", headless=self.config.headless
                )
            else:
                self._browser_instance = self._playwright_ctx.chromium.launch(headless=self.config.headless)

            page = self._browser_instance.new_page()
            page.set_default_timeout(self.config.timeout_ms)
            self._driver = page
        except Exception as exc:
            self.fechar()
            raise BrowserAdapterException(f"Falha ao inicializar Playwright: {exc}") from exc

    def _iniciar_selenium(self) -> None:
        try:
            from selenium import webdriver
            b_type = self.config.browser_type
            if b_type == "firefox":
                opts = webdriver.FirefoxOptions()
                if self.config.headless:
                    opts.add_argument("--headless")
                self._driver = webdriver.Firefox(options=opts)
            elif b_type == "edge":
                opts = webdriver.EdgeOptions()
                if self.config.headless:
                    opts.add_argument("--headless=new")
                self._driver = webdriver.Edge(options=opts)
            else:
                opts = webdriver.ChromeOptions()
                if self.config.headless:
                    opts.add_argument("--headless=new")
                self._driver = webdriver.Chrome(options=opts)
            self._driver.set_page_load_timeout(self.config.timeout_ms / 1000.0)
        except Exception as exc:
            self.fechar()
            raise BrowserAdapterException(f"Falha ao inicializar Selenium: {exc}") from exc

    def _iniciar_undetected(self) -> None:
        try:
            import undetected_chromedriver as uc
            opts = uc.ChromeOptions()
            if self.config.headless:
                opts.add_argument("--headless=new")
            self._driver = uc.Chrome(options=opts)
            self._driver.set_page_load_timeout(self.config.timeout_ms / 1000.0)
        except Exception as exc:
            self.fechar()
            raise BrowserAdapterException(f"Falha ao inicializar Undetected-Chromedriver: {exc}") from exc

    def navegar(self, url: str) -> None:
        """Navega para uma URL registrando no histórico de auditoria."""
        if self._fechado or self._driver is None:
            raise BrowserAdapterException("Não é possível navegar: a sessão do navegador não está ativa.")
        self.historico_urls.append(url)
        if self.config.modo_simulacao or self.config.engine == "simulacao":
            return
        if self.config.engine == "playwright":
            self._driver.goto(url)
        else:
            self._driver.get(url)

    @property
    def driver(self) -> Any:
        return self._driver

    @property
    def esta_fechado(self) -> bool:
        return self._fechado

    def fechar(self) -> None:
        """Encerra determinísticamente o navegador e libera os processos filhos do sistema operacional."""
        if self._fechado:
            return
        try:
            if self._browser_instance is not None:
                self._browser_instance.close()
            if self._playwright_ctx is not None:
                self._playwright_ctx.stop()
            if self._driver is not None and hasattr(self._driver, "quit"):
                self._driver.quit()
        finally:
            self._driver = None
            self._browser_instance = None
            self._playwright_ctx = None
            self._fechado = True


@contextmanager
def get_browser(
    config: Optional[BrowserConfig] = None,
) -> Generator[BrowserSession, None, None]:
    """
    Context Manager defensivo para automação web (with get_browser() as browser:).
    Garante o encerramento obrigatório do navegador no bloco finally mesmo diante de falhas.
    """
    cfg = config or BrowserConfig.from_env()
    sessao = BrowserSession(cfg)
    try:
        sessao.iniciar()
        yield sessao
    finally:
        sessao.fechar()
