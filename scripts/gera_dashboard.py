"""
Gera um dashboard HTML autonomo (sem CDN externo) a partir do Excel consolidado
produzido por processa_relatorio.py.

Uso:
    python gera_dashboard.py <consolidado.xlsx> <saida.html> [--de DD/MM/AAAA --ate DD/MM/AAAA]
"""
import sys
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd

SEQ_BLUE = {"light": "#2a78d6", "dark": "#3987e5"}
SEQ_AQUA = {"light": "#1baf7a", "dark": "#199e70"}
SEQ_YELLOW = {"light": "#eda100", "dark": "#c98500"}


def barra_horizontal(df: pd.DataFrame, coluna_label: str, cor: dict, id_prefix: str) -> str:
    if df.empty:
        return '<p class="vazio">Nenhum registro no período.</p>'
    maximo = int(df["qtd"].max())
    linhas = []
    for i, row in df.iterrows():
        label = escape(str(row[coluna_label]))
        qtd = int(row["qtd"])
        largura_pct = round(100 * qtd / maximo, 1) if maximo else 0
        linhas.append(f"""
        <div class="linha-barra">
          <div class="rotulo" title="{label}">{label}</div>
          <div class="trilha">
            <div class="preenchimento" style="width:{largura_pct}%"></div>
            <span class="valor">{qtd}</span>
          </div>
        </div>""")
    return "\n".join(linhas)


def tabela_detalhe(df: pd.DataFrame) -> str:
    if df.empty:
        return '<p class="vazio">Nenhuma invasão no período.</p>'
    linhas_html = []
    for _, row in df.iterrows():
        data_fmt = pd.to_datetime(row["Data"]).strftime("%d/%m/%Y")
        linhas_html.append(f"""
        <tr>
          <td>{data_fmt}</td>
          <td>{escape(str(row["Grupo"]))}</td>
          <td>{escape(str(row["Modelo"]))}</td>
          <td class="mono">{escape(str(row["Chassis"]))}</td>
          <td>{escape(str(row["Municipio"]))}</td>
          <td>{escape(str(row["Tipo"]))}</td>
        </tr>""")
    return f"""
    <table class="detalhe">
      <thead>
        <tr><th>Data</th><th>Grupo</th><th>Modelo</th><th>Chassi</th><th>Município</th><th>Tipo</th></tr>
      </thead>
      <tbody>
        {"".join(linhas_html)}
      </tbody>
    </table>"""


def gera_html(rankings: dict[str, pd.DataFrame], de: str, ate: str) -> str:
    total = int(rankings["detalhe"].shape[0])
    n_grupos = rankings["ranking_grupos"].shape[0]
    grupo_top = rankings["ranking_grupos"].iloc[0]["Grupo"] if n_grupos else "-"
    modelo_top = rankings["ranking_modelos"].iloc[0]["Modelo"] if not rankings["ranking_modelos"].empty else "-"
    gerado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Invasões VW — Ápia</title>
<style>
  .viz-root {{
    --surface-1: #fcfcfb; --page: #f9f9f7;
    --text-primary: #0b0b0b; --text-secondary: #52514e; --text-muted: #898781;
    --grid: #e1e0d9; --border: rgba(11,11,11,0.10);
    --blue: {SEQ_BLUE["light"]}; --aqua: {SEQ_AQUA["light"]}; --yellow: {SEQ_YELLOW["light"]};
  }}
  @media (prefers-color-scheme: dark) {{
    .viz-root {{
      --surface-1: #1a1a19; --page: #0d0d0d;
      --text-primary: #ffffff; --text-secondary: #c3c2b7; --text-muted: #898781;
      --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
      --blue: {SEQ_BLUE["dark"]}; --aqua: {SEQ_AQUA["dark"]}; --yellow: {SEQ_YELLOW["dark"]};
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 24px; background: var(--page); color: var(--text-primary);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  .viz-root {{ max-width: 980px; margin: 0 auto; }}
  header {{ margin-bottom: 24px; }}
  h1 {{ font-size: 1.4rem; margin: 0 0 4px; }}
  .subtitulo {{ color: var(--text-secondary); font-size: 0.9rem; }}
  .cartoes {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }}
  .cartao {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px;
  }}
  .cartao .rotulo-cartao {{ color: var(--text-muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }}
  .cartao .valor-cartao {{ font-size: 1.9rem; font-weight: 600; margin-top: 4px; font-variant-numeric: proportional-nums; }}
  .cartao .valor-cartao.pequeno {{ font-size: 1.15rem; }}
  section {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 18px 20px; margin-bottom: 16px;
  }}
  section h2 {{ font-size: 0.95rem; margin: 0 0 14px; color: var(--text-primary); }}
  .linha-barra {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
  .rotulo {{
    width: 190px; flex-shrink: 0; font-size: 0.82rem; color: var(--text-secondary);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  .trilha {{ flex: 1; background: var(--grid); border-radius: 4px; height: 20px; position: relative; }}
  .preenchimento {{ background: var(--barra-cor, var(--blue)); height: 100%; border-radius: 4px; }}
  #grupos .preenchimento {{ background: var(--blue); }}
  #modelos .preenchimento {{ background: var(--aqua); }}
  #municipios .preenchimento {{ background: var(--yellow); }}
  .valor {{
    position: absolute; right: -28px; top: 50%; transform: translateY(-50%);
    font-size: 0.78rem; color: var(--text-secondary); font-variant-numeric: tabular-nums;
  }}
  table.detalhe {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
  table.detalhe th {{
    text-align: left; padding: 8px 10px; color: var(--text-muted); font-weight: 500;
    border-bottom: 1px solid var(--grid); white-space: nowrap;
  }}
  table.detalhe td {{ padding: 8px 10px; border-bottom: 1px solid var(--grid); color: var(--text-secondary); }}
  table.detalhe td.mono {{ font-family: ui-monospace, monospace; font-size: 0.76rem; }}
  .vazio {{ color: var(--text-muted); font-size: 0.85rem; }}
  footer {{ color: var(--text-muted); font-size: 0.75rem; margin-top: 20px; }}
</style>
</head>
<body>
<div class="viz-root">
  <header>
    <h1>Invasões VW — Grupo Ápia</h1>
    <div class="subtitulo">Período {de} a {ate} · ADVEs Araraquara, Rio Claro, Araras, Pirassununga</div>
  </header>

  <div class="cartoes">
    <div class="cartao">
      <div class="rotulo-cartao">Total de invasões</div>
      <div class="valor-cartao">{total}</div>
    </div>
    <div class="cartao">
      <div class="rotulo-cartao">Grupo que mais invadiu</div>
      <div class="valor-cartao pequeno">{escape(str(grupo_top))}</div>
    </div>
    <div class="cartao">
      <div class="rotulo-cartao">Modelo mais vendido por invasores</div>
      <div class="valor-cartao pequeno">{escape(str(modelo_top))}</div>
    </div>
  </div>

  <section id="grupos">
    <h2>Ranking de grupos invasores</h2>
    {barra_horizontal(rankings["ranking_grupos"], "Grupo", SEQ_BLUE, "grupos")}
  </section>

  <section id="modelos">
    <h2>Modelos VW mais vendidos por invasores</h2>
    {barra_horizontal(rankings["ranking_modelos"], "Modelo", SEQ_AQUA, "modelos")}
  </section>

  <section id="municipios">
    <h2>Municípios mais invadidos</h2>
    {barra_horizontal(rankings["ranking_municipios"], "Municipio", SEQ_YELLOW, "municipios")}
  </section>

  <section>
    <h2>Detalhe das invasões</h2>
    {tabela_detalhe(rankings["detalhe"])}
  </section>

  <footer>Gerado em {gerado_em} · Fonte: Assobrav (Área de Cobertura &gt; Invasão, modo Grupo Econômico)</footer>
</div>
</body>
</html>"""


def main():
    if len(sys.argv) < 3:
        print("Uso: python gera_dashboard.py <consolidado.xlsx> <saida.html>")
        sys.exit(1)
    entrada = Path(sys.argv[1])
    saida = Path(sys.argv[2])

    rankings = {
        "ranking_grupos": pd.read_excel(entrada, sheet_name="Ranking Grupos"),
        "ranking_modelos": pd.read_excel(entrada, sheet_name="Ranking Modelos"),
        "ranking_municipios": pd.read_excel(entrada, sheet_name="Ranking Municipios"),
        "detalhe": pd.read_excel(entrada, sheet_name="Detalhe Invasoes"),
    }

    de = rankings["detalhe"]["Data"].min()
    ate = rankings["detalhe"]["Data"].max()
    de_str = pd.to_datetime(de).strftime("%d/%m/%Y") if pd.notna(de) else "-"
    ate_str = pd.to_datetime(ate).strftime("%d/%m/%Y") if pd.notna(ate) else "-"

    html = gera_html(rankings, de_str, ate_str)
    saida.write_text(html, encoding="utf-8")
    print(f"Dashboard salvo em {saida}")


if __name__ == "__main__":
    main()
