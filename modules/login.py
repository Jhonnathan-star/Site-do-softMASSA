import streamlit as st
import bcrypt
from database.connection import conectar

# Utilitários
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode()
    return bcrypt.checkpw(password.encode(), hashed)

def verificar_superusuario(conn, usuario, senha):
    cursor = conn.cursor()
    cursor.execute("SELECT senha FROM super_usuarios WHERE usuario = %s", (usuario,))
    resultado = cursor.fetchone()
    cursor.close()
    if resultado:
        senha_hash = resultado[0]
        return check_password(senha, senha_hash)
    return False

def verificar_usuario_normal(conn, usuario, senha):
    cursor = conn.cursor()
    cursor.execute("SELECT senha FROM usuarios WHERE usuario = %s", (usuario,))
    resultado = cursor.fetchone()
    cursor.close()
    if resultado:
        senha_hash = resultado[0]
        return check_password(senha, senha_hash)
    return False

# Função de login
def login_usuario(conn):
    st.subheader("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        # Primeiro tenta login como superusuário
        if verificar_superusuario(conn, usuario, senha):
            st.success(f"Bem-vindo, {usuario} (Superusuário)!")
            st.session_state['logado'] = True
            st.session_state['usuario'] = usuario
            st.session_state['superusuario'] = True
            st.rerun()  # Redireciona imediatamente após login

        # Se não for superusuário, tenta login como usuário normal
        elif verificar_usuario_normal(conn, usuario, senha):
            st.success(f"Bem-vindo, {usuario}!")
            st.session_state['logado'] = True
            st.session_state['usuario'] = usuario
            st.session_state['superusuario'] = False
            st.rerun()

        else:
            st.error("Usuário ou senha incorretos.")

# Cadastro (visível só para superusuário)
def cadastrar_usuario(conn):
    st.subheader("Cadastro de Novo Usuário")
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

        st.success("✅ Usuário cadastrado com sucesso!")
