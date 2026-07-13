"""
Processa o relatorio de Invasao ja exportado do Assobrav (Operacionais > Area de
Cobertura > Invasao, filtrado em modo "Grupo Economico") e gera o ranking de
grupos invasores, modelos e a lista de chassis invadidos.

O proprio relatorio do Assobrav ja exclui vendas entre lojas do mesmo grupo
(estoque compartilhado), entao toda linha aqui e uma invasao de verdade.

Uso:
    python processa_relatorio.py <invasao.xlsx> <saida.xlsx>
"""
import json
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
MAPA_GRUPOS_PATH = BASE / "config" / "mapa_grupos.json"


def carrega_mapa_grupos() -> dict[int, str]:
    if not MAPA_GRUPOS_PATH.exists():
        return {}
    data = json.loads(MAPA_GRUPOS_PATH.read_text(encoding="utf-8"))
    return {int(k): v for k, v in data.items() if k.lstrip("-").isdigit()}


def nome_grupo(codigo_dn, mapa: dict[int, str]) -> str:
    return mapa.get(int(codigo_dn), f"DN {int(codigo_dn)} (grupo nao cadastrado)")


def le_relatorio_invasao(caminho: Path) -> pd.DataFrame:
    bruto = pd.read_excel(caminho, header=None)
    linha_cabecalho = bruto.index[bruto[0].astype(str).str.strip() == "Data"]
    if len(linha_cabecalho) == 0:
        raise ValueError(f"Nao encontrei a linha de cabecalho 'Data' em {caminho}")
    inicio = linha_cabecalho[0] + 1

    dados = bruto.loc[inicio:, [0, 2, 6, 7, 8, 9]].copy()
    dados.columns = ["Data", "Modelo", "Chassis", "Municipio", "DN", "Tipo"]
    dados = dados[dados["Data"].astype(str).str.match(r"\d{2}/\d{2}/\d{4}")].copy()

    dados["Chassis"] = dados["Chassis"].astype(str).str.strip()
    dados["DN"] = pd.to_numeric(dados["DN"], errors="coerce").astype("Int64")
    dados["Data"] = pd.to_datetime(dados["Data"], format="%d/%m/%Y")
    return dados.reset_index(drop=True)


def gera_rankings(invasoes: pd.DataFrame, mapa_grupos: dict[int, str]) -> dict[str, pd.DataFrame]:
    invasoes = invasoes.copy()
    invasoes["Grupo"] = invasoes["DN"].apply(lambda c: nome_grupo(c, mapa_grupos))

    ranking_grupos = (
        invasoes.groupby(["DN", "Grupo"])
        .size()
        .reset_index(name="qtd")
        .sort_values("qtd", ascending=False)
        .reset_index(drop=True)
    )

    ranking_modelos = (
        invasoes.groupby("Modelo")
        .size()
        .reset_index(name="qtd")
        .sort_values("qtd", ascending=False)
        .reset_index(drop=True)
    )

    ranking_municipios = (
        invasoes.groupby("Municipio")
        .size()
        .reset_index(name="qtd")
        .sort_values("qtd", ascending=False)
        .reset_index(drop=True)
    )

    detalhe = (
        invasoes[["Data", "Grupo", "DN", "Modelo", "Chassis", "Municipio", "Tipo"]]
        .sort_values("Data")
        .reset_index(drop=True)
    )

    return {
        "ranking_grupos": ranking_grupos,
        "ranking_modelos": ranking_modelos,
        "ranking_municipios": ranking_municipios,
        "detalhe": detalhe,
    }


def salva_excel(rankings: dict[str, pd.DataFrame], saida: Path):
    with pd.ExcelWriter(saida, engine="openpyxl") as writer:
        rankings["ranking_grupos"].to_excel(writer, sheet_name="Ranking Grupos", index=False)
        rankings["ranking_modelos"].to_excel(writer, sheet_name="Ranking Modelos", index=False)
        rankings["ranking_municipios"].to_excel(writer, sheet_name="Ranking Municipios", index=False)
        rankings["detalhe"].to_excel(writer, sheet_name="Detalhe Invasoes", index=False)


def main():
    if len(sys.argv) != 3:
        print("Uso: python processa_relatorio.py <invasao.xlsx> <saida.xlsx>")
        sys.exit(1)
    entrada = Path(sys.argv[1])
    saida = Path(sys.argv[2])

    mapa_grupos = carrega_mapa_grupos()
    invasoes = le_relatorio_invasao(entrada)
    rankings = gera_rankings(invasoes, mapa_grupos)
    salva_excel(rankings, saida)

    codigos_sem_nome = sorted(set(int(c) for c in invasoes["DN"].tolist()) - set(mapa_grupos.keys()))
    print(f"Total de invasoes no periodo: {len(invasoes)}")
    if codigos_sem_nome:
        print(f"DNs sem nome cadastrado em config/mapa_grupos.json: {codigos_sem_nome}")
    print(f"Relatorio salvo em: {saida}")


if __name__ == "__main__":
    main()
