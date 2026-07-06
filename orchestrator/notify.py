"""Kanal-agnostik bildirim. Ortam değişkeni yoksa sessizce hiçbir şey yapmaz.

WhatsApp (CallMeBot, ücretsiz/3.parti):
  ARENA_WA_PHONE   = +90XXXXXXXXXX
  ARENA_WA_APIKEY  = CallMeBot'un verdiği anahtar

E-posta (SMTP, güvenilir omurga):
  ARENA_SMTP_HOST, ARENA_SMTP_PORT (vars. 587), ARENA_SMTP_USER,
  ARENA_SMTP_PASS, ARENA_MAIL_TO
"""
from __future__ import annotations

import os
import smtplib
import urllib.parse
import urllib.request
from email.mime.text import MIMEText


def send(msg: str, subject: str = "BIST AI Arena — uyarı") -> bool:
    """En az bir kanaldan gönderilirse True."""
    ok = False
    ok = _whatsapp(msg) or ok
    ok = _email(msg, subject) or ok
    return ok


def _whatsapp(msg: str) -> bool:
    phone = os.environ.get("ARENA_WA_PHONE")
    apikey = os.environ.get("ARENA_WA_APIKEY")
    if not phone or not apikey:
        return False
    url = "https://api.callmebot.com/whatsapp.php?" + urllib.parse.urlencode(
        {"phone": phone, "text": msg, "apikey": apikey})
    try:
        urllib.request.urlopen(url, timeout=20)
        return True
    except Exception:
        return False


def _email(msg: str, subject: str = "BIST AI Arena — uyarı") -> bool:
    host = os.environ.get("ARENA_SMTP_HOST")
    user = os.environ.get("ARENA_SMTP_USER")
    pw = os.environ.get("ARENA_SMTP_PASS")
    to = os.environ.get("ARENA_MAIL_TO", user)
    if not (host and user and pw and to):
        return False
    port = int(os.environ.get("ARENA_SMTP_PORT", "587"))
    m = MIMEText(msg, "plain", "utf-8")
    m["Subject"] = subject
    m["From"] = user
    m["To"] = to
    try:
        with smtplib.SMTP(host, port, timeout=25) as s:
            s.starttls()
            s.login(user, pw)
            s.sendmail(user, [to], m.as_string())
        return True
    except Exception:
        return False


if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "BIST AI Arena test bildirimi"
    print("gönderildi" if send(text) else "kanal kurulu değil / gönderilemedi")
