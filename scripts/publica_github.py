"""
Publica o dashboard do dia no GitHub Pages: copia o HTML gerado para docs/,
atualiza docs/index.html (sempre = ultimo relatorio) e faz commit + push.

Uso:
    python publica_github.py <dashboard.html> <data AAAA-MM-DD>

O link fixo apos a primeira publicacao fica em:
    https://<GITHUB_USER>.github.io/<GITHUB_REPO>/
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / "config" / ".env")

GITHUB_USER = os.environ["GITHUB_USER"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]


def roda(*args, **kwargs):
    return subprocess.run(args, cwd=BASE, check=True, capture_output=True, text=True, **kwargs)


def main():
    if len(sys.argv) != 3:
        print("Uso: python publica_github.py <dashboard.html> <data AAAA-MM-DD>")
        sys.exit(1)
    origem = Path(sys.argv[1])
    data = sys.argv[2]

    docs = BASE / "docs"
    docs.mkdir(exist_ok=True)
    shutil.copy(origem, docs / f"{data}.html")
    shutil.copy(origem, docs / "index.html")

    roda("git", "add", "docs")
    resultado_status = roda("git", "status", "--porcelain", "docs")
    if not resultado_status.stdout.strip():
        print("Nada novo para publicar (docs/ sem alteracoes).")
        return

    roda("git", "commit", "-m", f"Dashboard {data}")
    url_push = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"
    roda("git", "push", url_push, "HEAD:main")

    link = f"https://{GITHUB_USER}.github.io/{GITHUB_REPO}/"
    print(f"Publicado em: {link}")


if __name__ == "__main__":
    main()
