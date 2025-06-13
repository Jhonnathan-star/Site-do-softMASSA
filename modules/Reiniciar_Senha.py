import streamlit as st
from database.connection import conectar
from modules.auth_utils import hash_password
from datetime import datetime

st.title("🔐 Redefinir Senha")

token = st.query_params.get("token")

if not token:
    st.error("Token de redefinição não encontrado.")
    st.stop()

conn = conectar()
cursor = conn.cursor()
cursor.execute("""
    SELECT usuario_id, expira_em FROM tokens_recuperacao
    WHERE token = %s
""", (token,))
resultado = cursor.fetchone()

if not resultado:
    st.error("Token inválido.")
    st.stop()

usuario_id, expira_em = resultado
if expira_em < datetime.now():
    st.error("Token expirado.")
    st.stop()

nova_senha = st.text_input("Nova senha", type="password")
confirmar = st.text_input("Confirmar senha", type="password")

if st.button("Redefinir senha"):
    if nova_senha != confirmar:
        st.error("As senhas não coincidem.")
    elif len(nova_senha) < 4:
        st.warning("A senha deve ter ao menos 4 caracteres.")
    else:
        nova_hash = hash_password(nova_senha)
        cursor.execute("UPDATE usuarios SET senha = %s WHERE id = %s", (nova_hash, usuario_id))
        cursor.execute("DELETE FROM tokens_recuperacao WHERE token = %s", (token,))
        conn.commit()
        st.success("Senha redefinida com sucesso. Você pode fechar essa aba e fazer login.")
        conn.close()
