import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def enviar_email(destinatario, link_recuperacao):
    remetente = os.getenv("EMAIL_REMETENTE")
    senha = os.getenv("EMAIL_SENHA")

    if not remetente or not senha:
        st.error("❌ Variáveis de ambiente para e-mail não configuradas.")
        return

    assunto = "Redefinição de senha"
    corpo = f"""Olá,

Clique no link abaixo para redefinir sua senha:
{link_recuperacao}

Se você não solicitou isso, ignore esta mensagem."""

    msg = MIMEMultipart()
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(remetente, senha)
            server.sendmail(remetente, destinatario, msg.as_string())
        st.success("✅ E-mail enviado com sucesso.")
    except Exception as e:
        st.error("❌ Erro ao enviar e-mail.")
        st.exception(e)

def obter_usuario_com_email(conn, usuario: str):
    cursor = conn.cursor()
    cursor.execute("SELECT id, senha, tipo, email FROM usuarios WHERE usuario = %s", (usuario,))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado
