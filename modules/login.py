
import streamlit as st
import bcrypt
import uuid
from datetime import datetime, timedelta
from database.connection import conectar
from streamlit_cookies_manager import EncryptedCookieManager

# ---------- UTILITÁRIOS ------------

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode()
    return bcrypt.checkpw(password.encode(), hashed)

def gerar_token():
    return str(uuid.uuid4())

# ---------- FUNÇÕES DE BANCO ------------

def obter_usuario_por_nome(conn, usuario):
    cursor = conn.cursor()
    cursor.execute("SELECT id, senha FROM usuarios WHERE usuario = %s", (usuario,))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado  # (id, senha_hashed) ou None

def salvar_token(usuario_id, conn, dias_validade=7):
    token = gerar_token()
    criado_em = datetime.now()
    expiracao = criado_em + timedelta(days=dias_validade)

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessao_tokens (usuario_id, token, criado_em, expirado, expiracao)
        VALUES (%s, %s, %s, %s, %s)
    """, (usuario_id, token, criado_em, False, expiracao))
    conn.commit()
    cursor.close()
    return token

def validar_token(token, conn):
    cursor = conn.cursor()
    agora = datetime.now()
    cursor.execute("""
        SELECT usuario_id FROM sessao_tokens
        WHERE token = %s AND expirado = FALSE AND (expiracao IS NULL OR expiracao > %s)
    """, (token, agora))
    resultado = cursor.fetchone()
    cursor.close()
    if resultado:
        return resultado[0]
    return None

def marcar_token_expirado(token, conn):
    cursor = conn.cursor()
    cursor.execute("UPDATE sessao_tokens SET expirado = TRUE WHERE token = %s", (token,))
    conn.commit()
    cursor.close()

def cadastrar_novo_usuario(usuario, senha, conn):
    senha_hashed = hash_password(senha)
    cursor = conn.cursor()
    cursor.execute("SELECT usuario FROM usuarios WHERE usuario = %s", (usuario,))
    if cursor.fetchone():
        cursor.close()
        return False  # Usuário já existe
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)", (usuario, senha_hashed))
    conn.commit()
    cursor.close()
    return True

def obter_nome_usuario_por_id(usuario_id, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT usuario FROM usuarios WHERE id = %s", (usuario_id,))
    resultado = cursor.fetchone()
    cursor.close()
    if resultado:
        return resultado[0]
    return None

# --------- LÓGICA STREAMLIT ------------

def login_page(conn, cookies):
    st.subheader("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        dados = obter_usuario_por_nome(conn, usuario)
        if dados:
            usuario_id, senha_hashed = dados
            if check_password(senha, senha_hashed):
                token = salvar_token(usuario_id, conn)
                # Salva token no cookie para persistência
                cookies["session_token"] = token
                cookies.save()

                st.session_state['logado'] = True
                st.session_state['usuario_id'] = usuario_id
                st.session_state['usuario'] = usuario
                st.session_state['token'] = token

                st.success(f"Bem-vindo, {usuario}!")
                st.experimental_rerun()
            else:
                st.error("Senha incorreta.")
        else:
            st.error("Usuário não encontrado.")

def logout(conn, cookies):
    if 'token' in st.session_state:
        marcar_token_expirado(st.session_state['token'], conn)
    # Apaga o cookie
    cookies["session_token"] = ""
    cookies.save()

    st.session_state.clear()
    st.experimental_rerun()

def cadastro_page(conn):
    st.subheader("Cadastro")
    novo_usuario = st.text_input("Novo usuário", key="novo_usuario")
    nova_senha = st.text_input("Nova senha", type="password", key="nova_senha")
    confirmar_senha = st.text_input("Confirme a senha", type="password", key="confirmar_senha")

    if st.button("Cadastrar"):
        if not novo_usuario or not nova_senha or not confirmar_senha:
            st.warning("Preencha todos os campos.")
            return
        if nova_senha != confirmar_senha:
            st.warning("Senhas não conferem.")
            return
        if cadastrar_novo_usuario(novo_usuario, nova_senha, conn):
            st.success("Usuário cadastrado com sucesso! Faça login.")
        else:
            st.warning("Usuário já existe.")

def app_principal(conn, cookies):
    st.title("App com Login e Sessão por Token e Cookie")

    if 'logado' in st.session_state and st.session_state['logado']:
        st.write(f"Olá, {st.session_state['usuario']}! Você está logado.")
        if st.button("Logout"):
            logout(conn, cookies)
    else:
        aba = st.radio("Escolha:", ["Login", "Cadastro"])
        if aba == "Login":
            login_page(conn, cookies)
        else:
            cadastro_page(conn)

def checar_sessao(conn, cookies):
    # Se já está no session_state, ok
    if 'logado' in st.session_state and st.session_state['logado']:
        return

    token = cookies.get("session_token")
    if token:
        usuario_id = validar_token(token, conn)
        if usuario_id:
            st.session_state['logado'] = True
            st.session_state['usuario_id'] = usuario_id
            st.session_state['usuario'] = obter_nome_usuario_por_id(usuario_id, conn)
            st.session_state['token'] = token
        else:
            # Token inválido ou expirado, remove cookie
            cookies["session_token"] = ""
            cookies.save()

if __name__ == '__main__':
    conn = conectar()
    if conn is None:
        st.error("Não foi possível conectar ao banco de dados.")
    else:
        # Inicializa cookies
        cookies = EncryptedCookieManager(
            prefix="myapp_",
            password="uma_senha_super_secreta_e_grande_123456"  # Troque por uma senha forte sua
        )
        if not cookies.ready():
            st.stop()

        checar_sessao(conn, cookies)
        app_principal(conn, cookies)
