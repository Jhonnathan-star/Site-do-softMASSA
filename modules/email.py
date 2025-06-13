import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def enviar_email(destinatario, link_recuperacao):
    remetente = "softmassa25@gmail.com"
    senha = "vzbd ivib coka jcev"  # Crie uma senha de app no Gmail

    assunto = "Redefinição de senha"
    corpo = f"Olá,\n\nClique no link abaixo para redefinir sua senha:\n{link_recuperacao}\n\nSe você não solicitou isso, ignore esta mensagem."

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
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")

def obter_usuario_com_email(conn, usuario: str):
    cursor = conn.cursor()
    cursor.execute("SELECT id, senha, tipo, email FROM usuarios WHERE usuario = %s", (usuario,))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado
