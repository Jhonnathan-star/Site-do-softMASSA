import streamlit as st
from datetime import datetime
from modules.auth_utils import hash_password
from database.connection import conectar
from modules.login import db_config_padaria1, db_config_padaria2  # Importa os bancos

def mostrar_redefinir_senha():
    st.title("🔐 Redefinir Senha")

    token = st.query_params.get("token")
    if not token:
        st.error("Token de redefinição não encontrado.")
        return

    # Testar o token nos dois bancos
    for banco_config in [db_config_padaria1, db_config_padaria2]:
        conn = conectar(banco_config)
        if not conn:
            continue

        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT usuario_id, expira_em FROM tokens_recuperacao
                WHERE token = %s
            """, (token,))
            resultado = cursor.fetchone()

            if resultado:
                usuario_id, expira_em = resultado
                if expira_em < datetime.now():
                    st.error("Token expirado.")
                    return

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
                        st.success("✅ Senha redefinida com sucesso. Você pode fechar esta aba e fazer login.")
                return  # Interrompe após encontrar e processar no banco certo
        finally:
            cursor.close()
            conn.close()

    st.error("❌ Token inválido.")
