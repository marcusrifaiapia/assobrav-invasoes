"""
Cria um rascunho de e-mail direto na pasta Rascunhos do Gmail via IMAP,
usando uma Senha de App (nao a senha normal da conta). Nunca envia nada --
so grava a mensagem com a flag \\Draft na pasta certa.

Uso:
    python cria_rascunho_gmail.py <assunto> <corpo_texto.txt> <corpo_html.html>
"""
import imaplib
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / "config" / ".env")

GMAIL_USER = os.environ["REPORT_EMAIL_TO"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]


def acha_pasta_rascunhos(imap: imaplib.IMAP4_SSL) -> str:
    status, pastas = imap.list()
    if status != "OK":
        raise RuntimeError("Nao consegui listar as pastas do Gmail")
    for linha in pastas:
        texto = linha.decode("utf-8", errors="replace")
        if "\\Drafts" in texto:
            # formato: (flags) "delimitador" "Nome/Da/Pasta"
            return texto.split(' "/" ')[-1].strip('"')
    raise RuntimeError("Nao encontrei a pasta de Rascunhos (\\Drafts) via IMAP")


def cria_rascunho(assunto: str, corpo_texto: str, corpo_html: str, destinatario: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = GMAIL_USER
    msg["To"] = destinatario
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(corpo_texto, "plain", "utf-8"))
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))

    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    try:
        imap.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        pasta = acha_pasta_rascunhos(imap)
        imap.append(pasta, "\\Draft", imaplib.Time2Internaldate(__import__("time").time()), msg.as_bytes())
    finally:
        imap.logout()


def main():
    if len(sys.argv) != 4:
        print("Uso: python cria_rascunho_gmail.py <assunto> <corpo_texto.txt> <corpo_html.html>")
        sys.exit(1)
    assunto = sys.argv[1]
    corpo_texto = Path(sys.argv[2]).read_text(encoding="utf-8")
    corpo_html = Path(sys.argv[3]).read_text(encoding="utf-8")

    cria_rascunho(assunto, corpo_texto, corpo_html, GMAIL_USER)
    print(f"Rascunho criado no Gmail de {GMAIL_USER}: {assunto}")


if __name__ == "__main__":
    main()
