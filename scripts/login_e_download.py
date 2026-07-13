"""
Loga no portal Assobrav e baixa o relatorio pronto de Invasao
(Operacionais > Area de Cobertura > Invasao), ja filtrado por Grupo Economico
-- ou seja, o proprio portal exclui as vendas entre lojas do mesmo grupo
(estoque compartilhado entre Rio Claro/Araras/Araraquara/Matao/Pirassununga)
e mantem so as vendas feitas por outros grupos dentro das nossas ADVEs.

Uso:
    python login_e_download.py

Le credenciais de config/.env (nunca hardcoded, nunca no chat).
"""
import asyncio
import os
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import Page, async_playwright

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / "config" / ".env")

LOGIN_URL = os.environ["ASSOBRAV_URL"]
USER = os.environ["ASSOBRAV_USER"]
PASSWORD = os.environ["ASSOBRAV_PASSWORD"]
DOWNLOAD_DIR = Path(os.environ.get("DOWNLOAD_DIR", str(BASE / "downloads")))

INVASAO_URL = (
    "https://portal.assobrav.com.br/Consulta/AreaCobertura/lstInvasao.aspx"
    "?id_opcao=OTAw&id_menu=Mjc="
)

# Qualquer DN da conta serve aqui -- em modo "Grupo Economico" o portal ignora
# qual DN especifico foi selecionado e traz as invasoes do grupo inteiro.
DN_QUALQUER = "1187"
MODO_GRUPO_ECONOMICO = "1"


def periodo_atual() -> tuple[str, str]:
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)
    ontem = hoje - timedelta(days=1)
    return primeiro_dia.strftime("%Y-%m-%d"), ontem.strftime("%Y-%m-%d")


async def login(page: Page):
    await page.goto(LOGIN_URL)
    await page.get_by_placeholder("LOGIN").fill(USER)
    await page.get_by_placeholder("SENHA").fill(PASSWORD)
    await page.get_by_role("button", name="Acessar").click()
    await page.wait_for_load_state("networkidle")


# IDs reais dos controles ASP.NET nesta tela (levantados via inspecao do DOM,
# estaveis entre execucoes pois vem da arvore de controles do Web Forms).
ID_DATA_INICIO = "#ContentPlaceHolder1_txtDataInicio"
ID_DATA_FINAL = "#ContentPlaceHolder1_txtDataFinal"
ID_DDL_DN = "#ContentPlaceHolder1_ddlDN"
ID_DDL_AREA_DEMARCADA = "#ContentPlaceHolder1_ddlAreaDemarcada"
ID_BOTAO_FILTRAR = "#ContentPlaceHolder1_btFiltrar"
ID_BOTAO_EXPORTAR = "#ctl00_ContentPlaceHolder1_ReportViewer1_ctl09_ctl04_ctl00_ButtonLink"


async def baixa_relatorio_invasao(page: Page, saida_dir: Path) -> Path:
    de, ate = periodo_atual()
    await page.goto(INVASAO_URL)
    await page.wait_for_load_state("networkidle")

    await page.locator(ID_DATA_INICIO).fill(de)
    await page.locator(ID_DATA_FINAL).fill(ate)
    await page.locator(ID_DDL_DN).select_option(DN_QUALQUER)
    await page.locator(ID_DDL_AREA_DEMARCADA).select_option(MODO_GRUPO_ECONOMICO)

    await page.locator(ID_BOTAO_FILTRAR).click()
    await page.wait_for_load_state("networkidle")
    # O relatorio SSRS renderiza via postback/AJAX e pode demorar mais que o
    # "networkidle" da rede -- damos um tempo extra antes de procurar o menu.
    await page.wait_for_timeout(4000)

    saida_dir.mkdir(parents=True, exist_ok=True)
    exportar = page.locator(ID_BOTAO_EXPORTAR)
    try:
        await exportar.wait_for(state="visible", timeout=20000)
    except Exception:
        debug_path = saida_dir / "erro_export_nao_encontrado.png"
        await page.screenshot(path=str(debug_path), full_page=True)
        print(f"Nao encontrei o menu Exportar. Screenshot salvo em {debug_path}")
        raise

    destino = saida_dir / "invasao.xlsx"
    async with page.expect_download() as download_info:
        await exportar.click()
        await page.get_by_role("link", name="Excel").click()
    download = await download_info.value
    await download.save_as(destino)
    print(f"Relatorio de invasao salvo em {destino}")
    return destino


async def main():
    saida_dir = Path(DOWNLOAD_DIR) / date.today().isoformat()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(accept_downloads=True)
        await login(page)
        await baixa_relatorio_invasao(page, saida_dir)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
