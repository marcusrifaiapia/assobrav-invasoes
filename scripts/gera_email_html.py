"""
Gera o corpo HTML (e a versao texto simples) do e-mail diario de invasoes,
a partir do Excel consolidado. Usa tabelas + estilo inline (compativel com
clientes de e-mail, que nao confiam em CSS moderno/flexbox).

Uso:
    python gera_email_html.py <consolidado.xlsx> <saida.html> [--link URL]
"""
import sys
from datetime import date
from html import escape
from pathlib import Path

import pandas as pd

AZUL = "#1c3d6e"
AZUL_CLARO = "#eef3fb"
TEXTO = "#1a1a1a"
TEXTO_SEC = "#5b5b5b"
MUTED = "#8a8a8a"
BORDA = "#e4e4e4"
FUNDO_PAGINA = "#f3f4f6"
ALERTA_BG = "#fff4e5"
ALERTA_TXT = "#8a5300"


def linha_ranking(pos: int, label: str, qtd: int, destaque: bool, subtexto: str | None = None) -> str:
    peso = "font-weight:700;" if destaque else ""
    cor_num = AZUL if destaque else TEXTO_SEC
    sub_html = (
        f'<div style="font-size:11px;color:{MUTED};margin-top:2px;">DN {escape(subtexto)}</div>'
        if subtexto else ""
    )
    return f"""
    <tr>
      <td style="padding:9px 12px;border-bottom:1px solid {BORDA};color:{MUTED};font-size:13px;width:28px;vertical-align:top;">{pos}</td>
      <td style="padding:9px 12px;border-bottom:1px solid {BORDA};color:{TEXTO};font-size:14px;{peso}">{escape(str(label))}{sub_html}</td>
      <td style="padding:9px 12px;border-bottom:1px solid {BORDA};color:{cor_num};font-size:14px;text-align:right;{peso}font-variant-numeric:tabular-nums;vertical-align:top;">{qtd}</td>
    </tr>"""


def tabela_ranking(titulo: str, df: pd.DataFrame, coluna_label: str, coluna_subtexto: str | None = None) -> str:
    if df.empty:
        linhas = f'<tr><td style="padding:12px;color:{MUTED};font-size:13px;">Nenhum registro.</td></tr>'
    else:
        linhas = "".join(
            linha_ranking(
                i + 1, row[coluna_label], int(row["qtd"]), i == 0,
                subtexto=(str(row[coluna_subtexto]) if coluna_subtexto and "," in str(row[coluna_subtexto]) else None),
            )
            for i, row in df.reset_index(drop=True).iterrows()
        )
    return f"""
    <tr><td style="padding:0 24px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin:0 0 24px;">
        <tr><td style="padding:0 0 10px;font-size:13px;font-weight:700;color:{AZUL};text-transform:uppercase;letter-spacing:0.04em;">{titulo}</td></tr>
        {linhas}
      </table>
    </td></tr>"""


def tabela_detalhe(df: pd.DataFrame) -> str:
    if df.empty:
        return f'<p style="color:{MUTED};font-size:13px;">Nenhuma invasao no periodo.</p>'
    cab = ["Data", "Grupo", "Modelo", "Chassi", "Municipio"]
    th = "".join(
        f'<th style="text-align:left;padding:8px 10px;font-size:11px;color:{MUTED};text-transform:uppercase;border-bottom:1px solid {BORDA};">{c}</th>'
        for c in cab
    )
    linhas = []
    for _, row in df.sort_values("Data").iterrows():
        data_fmt = pd.to_datetime(row["Data"]).strftime("%d/%m")
        linhas.append(f"""
        <tr>
          <td style="padding:7px 10px;border-bottom:1px solid {BORDA};font-size:12px;color:{TEXTO_SEC};white-space:nowrap;">{data_fmt}</td>
          <td style="padding:7px 10px;border-bottom:1px solid {BORDA};font-size:12px;color:{TEXTO};">{escape(str(row["Grupo"]))}</td>
          <td style="padding:7px 10px;border-bottom:1px solid {BORDA};font-size:12px;color:{TEXTO_SEC};">{escape(str(row["Modelo"]))}</td>
          <td style="padding:7px 10px;border-bottom:1px solid {BORDA};font-size:11px;color:{MUTED};font-family:ui-monospace,Consolas,monospace;">{escape(str(row["Chassis"]))}</td>
          <td style="padding:7px 10px;border-bottom:1px solid {BORDA};font-size:12px;color:{TEXTO_SEC};">{escape(str(row["Municipio"]))}</td>
        </tr>""")
    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
      <tr>{th}</tr>
      {"".join(linhas)}
    </table>"""


def cartao(rotulo: str, valor: str, largura: str) -> str:
    return f"""
    <td width="{largura}" style="padding:16px 14px;background:{AZUL_CLARO};border-radius:8px;">
      <div style="font-size:11px;color:{AZUL};text-transform:uppercase;letter-spacing:0.04em;font-weight:600;">{escape(rotulo)}</div>
      <div style="font-size:19px;color:{TEXTO};font-weight:700;margin-top:4px;line-height:1.25;">{escape(valor)}</div>
    </td>"""


def gera_email(rankings: dict[str, pd.DataFrame], de: str, ate: str, link_dashboard: str) -> tuple[str, str]:
    total = int(rankings["detalhe"].shape[0])
    grupo_top = rankings["ranking_grupos"].iloc[0]["Grupo"] if not rankings["ranking_grupos"].empty else "-"
    modelo_top = rankings["ranking_modelos"].iloc[0]["Modelo"] if not rankings["ranking_modelos"].empty else "-"

    nao_cadastrados = rankings["ranking_grupos"][
        rankings["ranking_grupos"]["Grupo"].astype(str).str.contains("grupo nao cadastrado", case=False)
    ]
    alerta_html = ""
    if not nao_cadastrados.empty:
        dns = ", ".join(f"DN {d}" for d in nao_cadastrados["DNs"])
        alerta_html = f"""
        <tr><td style="padding:0 24px 20px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;background:{ALERTA_BG};border-radius:8px;">
            <tr><td style="padding:12px 16px;font-size:13px;color:{ALERTA_TXT};">
              <strong>Atencao:</strong> {escape(dns)} ainda sem grupo cadastrado.
            </td></tr>
          </table>
        </td></tr>"""

    html = f"""<div style="background:{FUNDO_PAGINA};padding:24px 12px;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:10px;overflow:hidden;border:1px solid {BORDA};">

  <tr><td style="background:{AZUL};padding:22px 24px;">
    <div style="font-size:18px;color:#ffffff;font-weight:700;">Invasões VW — Grupo Ápia</div>
    <div style="font-size:12px;color:#c9d6ea;margin-top:4px;">Período {de} a {ate}</div>
  </td></tr>

  <tr><td style="padding:20px 24px 4px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate;border-spacing:8px 0;">
      <tr>
        {cartao("Total de invasões", str(total), "33%")}
        {cartao("Grupo líder", str(grupo_top), "33%")}
        {cartao("Modelo mais vendido", str(modelo_top), "33%")}
      </tr>
    </table>
  </td></tr>

  <tr><td style="height:20px;"></td></tr>

  {alerta_html}

  {tabela_ranking("Ranking de grupos invasores", rankings["ranking_grupos"], "Grupo", "DNs")}
  {tabela_ranking("Modelos mais vendidos por invasores", rankings["ranking_modelos"], "Modelo")}
  {tabela_ranking("Municípios mais invadidos", rankings["ranking_municipios"], "Municipio")}

  <tr><td style="padding:0 24px 20px;">
    <div style="font-size:13px;font-weight:700;color:{AZUL};text-transform:uppercase;letter-spacing:0.04em;margin-bottom:10px;">Detalhe das invasões</div>
    {tabela_detalhe(rankings["detalhe"])}
  </td></tr>

  <tr><td style="padding:18px 24px;background:{FUNDO_PAGINA};text-align:center;">
    <a href="{link_dashboard}" style="display:inline-block;background:{AZUL};color:#ffffff;text-decoration:none;font-size:13px;font-weight:600;padding:10px 20px;border-radius:6px;">Ver dashboard completo</a>
  </td></tr>

  <tr><td style="padding:14px 24px;text-align:center;">
    <div style="font-size:11px;color:{MUTED};">Fonte: Assobrav (Área de Cobertura &gt; Invasão, modo Grupo Econômico) · Relatório gerado automaticamente</div>
  </td></tr>

</table>
</div>"""

    linhas_txt = [f"Invasoes VW - Grupo Apia | Periodo {de} a {ate}", "", f"Total de invasoes: {total}", f"Grupo lider: {grupo_top}", f"Modelo mais vendido: {modelo_top}", ""]
    linhas_txt.append("=== Ranking por Grupo ===")
    for i, row in rankings["ranking_grupos"].reset_index(drop=True).iterrows():
        linhas_txt.append(f"{i + 1}. {row['Grupo']} (DN {row['DNs']}) - {row['qtd']}")
    linhas_txt.append("")
    linhas_txt.append("=== Ranking por Modelo ===")
    for i, row in rankings["ranking_modelos"].reset_index(drop=True).iterrows():
        linhas_txt.append(f"{i + 1}. {row['Modelo']} - {row['qtd']}")
    linhas_txt.append("")
    linhas_txt.append("=== Ranking por Municipio ===")
    for i, row in rankings["ranking_municipios"].reset_index(drop=True).iterrows():
        linhas_txt.append(f"{i + 1}. {row['Municipio']} - {row['qtd']}")
    linhas_txt.append("")
    linhas_txt.append(f"Dashboard: {link_dashboard}")
    texto = "\n".join(linhas_txt)

    return html, texto


def main():
    if len(sys.argv) < 3:
        print("Uso: python gera_email_html.py <consolidado.xlsx> <saida.html> [--link URL]")
        sys.exit(1)
    entrada = Path(sys.argv[1])
    saida = Path(sys.argv[2])
    link = "https://marcusrifaiapia.github.io/assobrav-invasoes/"
    if "--link" in sys.argv:
        link = sys.argv[sys.argv.index("--link") + 1]

    rankings = {
        "ranking_grupos": pd.read_excel(entrada, sheet_name="Ranking Grupos"),
        "ranking_modelos": pd.read_excel(entrada, sheet_name="Ranking Modelos"),
        "ranking_municipios": pd.read_excel(entrada, sheet_name="Ranking Municipios"),
        "detalhe": pd.read_excel(entrada, sheet_name="Detalhe Invasoes"),
    }
    # O periodo e sempre "dia 01 do mes ate a data do arquivo" (o filtro
    # usado na consulta) -- nao derivar de min/max de "Detalhe Invasoes",
    # que so reflete os dias com invasao de verdade.
    data_relatorio = date.fromisoformat(entrada.stem)
    de = data_relatorio.replace(day=1).strftime("%d/%m/%Y")
    ate = data_relatorio.strftime("%d/%m/%Y")

    html, texto = gera_email(rankings, de, ate, link)
    saida.write_text(html, encoding="utf-8")
    saida.with_suffix(".txt").write_text(texto, encoding="utf-8")
    print(f"Email HTML salvo em {saida}")
    print(f"Email texto salvo em {saida.with_suffix('.txt')}")


if __name__ == "__main__":
    main()
