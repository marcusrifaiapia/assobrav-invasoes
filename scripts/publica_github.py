"""
Publica o dashboard do dia no GitHub Pages: copia o HTML gerado para docs/,
atualiza docs/index.html (sempre = ultimo relatorio) e faz commit + push.

Uso:
    python publica_github.py <dashboard.html> <data AAAA-MM-DD>

O link fixo apos a primeira publicacao fica em:
    https://<GITHUB_USER>.github.io/<GITHUB_REPO>/
"""
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / "config" / ".env")

GITHUB_USER = os.environ["GITHUB_USER"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

NOME_DATADO = re.compile(r"^\d{4}-\d{2}-\d{2}\.html$")


def roda(*args, **kwargs):
    return subprocess.run(args, cwd=BASE, check=True, capture_output=True, text=True, **kwargs)


def roda_com_retentativa(*args, tentativas=3, espera_s=5, **kwargs):
    ultimo_erro = None
    for tentativa in range(1, tentativas + 1):
        try:
            return roda(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            ultimo_erro = e
            print(f"Tentativa {tentativa}/{tentativas} falhou ({' '.join(args)}): {e.stderr.strip()}")
            if tentativa < tentativas:
                time.sleep(espera_s)
    raise ultimo_erro


def main():
    if len(sys.argv) != 3:
        print("Uso: python publica_github.py <dashboard.html> <data AAAA-MM-DD>")
        sys.exit(1)
    origem = Path(sys.argv[1])
    data = sys.argv[2]

    docs = BASE / "docs"
    docs.mkdir(exist_ok=True)
    shutil.copy(origem, docs / f"{data}.html")

    # index.html sempre reflete o relatorio mais recente por data, mesmo que
    # esta chamada esteja publicando/corrigindo um dia mais antigo.
    datados = sorted(f.name for f in docs.glob("*.html") if NOME_DATADO.match(f.name))
    if datados:
        shutil.copy(docs / datados[-1], docs / "index.html")

    roda("git", "add", "docs")
    resultado_status = roda("git", "status", "--porcelain", "docs")
    if not resultado_status.stdout.strip():
        print("Nada novo para publicar (docs/ sem alteracoes).")
        return

    roda("git", "commit", "-m", f"Dashboard {data}")
    url_push = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"
    roda_com_retentativa("git", "push", url_push, "HEAD:main")

    link = f"https://{GITHUB_USER}.github.io/{GITHUB_REPO}/"
    print(f"Publicado em: {link} (index.html = {datados[-1] if datados else data})")


if __name__ == "__main__":
    main()
