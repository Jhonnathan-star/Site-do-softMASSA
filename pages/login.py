import streamlit as st
import bcrypt
from database.connection import conectar  # importa sua função de conexão

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

def cadastrar_usuario(conn):
    st.subheader("Cadastro de Usuário")
    novo_usuario = st.text_input("Novo usuário")
    nova_senha = st.text_input("Nova senha", type="password")
    confirmar_senha = st.text_input("Confirme a senha", type="password")

    if st.button("Cadastrar"):
        if not novo_usuario or not nova_senha or not confirmar_senha:
            st.warning("Preencha todos os campos.")
            return
        if nova_senha != confirmar_senha:
            st.warning("Senhas não conferem.")
            return

        cursor = conn.cursor()
        cursor.execute("SELECT usuario FROM usuarios WHERE usuario = %s", (novo_usuario,))
        if cursor.fetchone():
            st.warning("Usuário já existe.")
            cursor.close()
            return
        
        senha_hashed = hash_password(nova_senha)
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)", (novo_usuario, senha_hashed))
        conn.commit()
        cursor.close()
        st.success("Usuário cadastrado com sucesso! Faça login.")

def login_usuario(conn):
    st.subheader("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        cursor = conn.cursor()
        cursor.execute("SELECT senha FROM usuarios WHERE usuario = %s", (usuario,))
        resultado = cursor.fetchone()
        cursor.close()
        if resultado:
            senha_hashed = resultado[0]
            # Se o hash está vindo como str, converte para bytes
            if isinstance(senha_hashed, str):
                senha_hashed = senha_hashed.encode('utf-8')
            if check_password(senha, senha_hashed):
                st.success(f"Bem-vindo, {usuario}!")
                st.session_state['logado'] = True
                st.session_state['usuario'] = usuario
                st.rerun()  # <- Roda novamente o app para redirecionar ao menu
            else:
                st.error("Senha incorreta.")
        else:
            st.error("Usuário não encontrado.")

def main():
    conn = conectar()
    if conn is None:
        st.error("Falha na conexão com o banco.")
        return

    if 'logado' not in st.session_state:
        st.session_state['logado'] = False
    
    if not st.session_state['logado']:
        aba = st.sidebar.selectbox("Ação", ["Login", "Cadastro"])
        if aba == "Login":
            login_usuario(conn)
        else:
            cadastrar_usuario(conn)
    else:
        st.write(f"Usuário logado: {st.session_state['usuario']}")
        if st.button("Logout"):
            st.session_state['logado'] = False
            st.session_state['usuario'] = None
            st.rerun()  # <- Corrigido aqui também
    
    conn.close()

if __name__ == "__main__":
    main()
