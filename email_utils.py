import os
import smtplib
from email.mime.text import MIMEText


def send_email(subject: str, recipient: str, html_body: str) -> None:
    mail_server = os.getenv("MAIL_SERVER")
    mail_port = int(os.getenv("MAIL_PORT", "587"))
    mail_use_tls = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")
    mail_from = os.getenv("MAIL_FROM", mail_username)

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = recipient

    with smtplib.SMTP(mail_server, mail_port) as server:
        if mail_use_tls:
            server.starttls()
        if mail_username and mail_password:
            server.login(mail_username, mail_password)
        server.sendmail(mail_from, [recipient], msg.as_string())
