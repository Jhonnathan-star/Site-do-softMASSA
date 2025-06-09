import streamlit as st
import bcrypt
import uuid
from datetime import datetime, timedelta
from database.connection import conectar

# ---------- UTILITÁRIOS ------------

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password: str, hashed: bytes) -> bool:
    if isinstance(hashed, str):
        hashed = hashed.encode()
    return bcrypt.checkpw(password.encode(), hashed)

def gerar_token() -> str:
    return str(uuid.uuid4())

# ---------- FUNÇÕES DE BANCO ------------

def obter_usuario_por_nome(conn, usuario: str):
    cursor = conn.cursor()
    cursor.execute("SELECT id, senha, tipo FROM usuarios WHERE usuario = %s", (usuario,))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado

def obter_nome_usuario_por_id(usuario_id: int, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT usuario FROM usuarios WHERE id = %s", (usuario_id,))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado[0] if resultado else None

def salvar_token(usuario_id: int, conn, dias_validade=7) -> str:
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

def validar_token(token: str, conn):
    cursor = conn.cursor()
    agora = datetime.now()
    cursor.execute("""
        SELECT usuario_id FROM sessao_tokens
        WHERE token = %s AND expirado = FALSE AND (expiracao IS NULL OR expiracao > %s)
    """, (token, agora))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado[0] if resultado else None

def marcar_token_expirado(token: str, conn):
    cursor = conn.cursor()
    cursor.execute("UPDATE sessao_tokens SET expirado = TRUE WHERE token = %s", (token,))
    conn.commit()
    cursor.close()

# ---------- CADASTRO DE USUÁRIO ------------

def cadastrar_usuario(conn):
    st.subheader("Cadastrar novo usuário")

    novo_usuario = st.text_input("Novo usuário", key="cad_usuario")
    nova_senha = st.text_input("Nova senha", type="password", key="cad_senha")
    confirmar_senha = st.text_input("Confirmar senha", type="password", key="cad_confirmar")

    if st.button("Cadastrar"):
        if not novo_usuario or not nova_senha or not confirmar_senha:
            st.warning("Preencha todos os campos.")
            return

        if nova_senha != confirmar_senha:
            st.error("As senhas não coincidem.")
            return

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = %s", (novo_usuario,))
        existe = cursor.fetchone()[0]

        if existe:
            st.error("Usuário já existe.")
        else:
            senha_hash = hash_password(nova_senha)
            cursor.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES (%s, %s, %s)", (novo_usuario, senha_hash, 'comum'))
            conn.commit()
            st.success(f"Usuário '{novo_usuario}' cadastrado com sucesso!")
        cursor.close()

def gerenciar_usuarios(conn):
    st.subheader("Cadastrar novo usuário")

    novo_usuario = st.text_input("Novo usuário")
    nova_senha = st.text_input("Nova senha", type="password")
    confirmar_senha = st.text_input("Confirmar senha", type="password")
    tipo_usuario = st.selectbox("Tipo de usuário", ["comum", "admin"])

    if st.button("Cadastrar usuário"):
        if not novo_usuario or not nova_senha or not confirmar_senha:
            st.warning("Preencha todos os campos.")
            return

        if nova_senha != confirmar_senha:
            st.error("As senhas não coincidem.")
            return

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = %s", (novo_usuario,))
        existe = cursor.fetchone()[0]

        if existe:
            st.error("Usuário já existe.")
        else:
            senha_hash = hash_password(nova_senha)
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, tipo) VALUES (%s, %s, %s)",
                (novo_usuario, senha_hash, tipo_usuario)
            )
            conn.commit()
            st.success(f"Usuário '{novo_usuario}' ({tipo_usuario}) cadastrado com sucesso!")
        cursor.close()

# ---------- LÓGICA DE LOGIN ------------

def login_usuario(conn, cookies):
    st.subheader("Login")
    usuario = st.text_input("Usuário", key="login_usuario")
    senha = st.text_input("Senha", type="password", key="login_senha")

    if st.button("Entrar", key="botao_entrar"):
        if not usuario or not senha:
            st.warning("Preencha usuário e senha.")
            return

        dados = obter_usuario_por_nome(conn, usuario)
        if dados:
            usuario_id, senha_hashed, tipo_usuario = dados
            if check_password(senha, senha_hashed):
                token = salvar_token(usuario_id, conn)
                cookies["session_token"] = token
                cookies.save()

                st.session_state['logado'] = True
                st.session_state['usuario_id'] = usuario_id
                st.session_state['usuario'] = usuario
                st.session_state['usuario_tipo'] = tipo_usuario
                st.session_state['token'] = token

                st.success(f"Bem-vindo, {usuario}!")
                st.rerun()
            else:
                st.error("Senha incorreta.")
        else:
            st.error("Usuário não encontrado.")

def logout(conn, cookies):
    if 'token' in st.session_state:
        marcar_token_expirado(st.session_state['token'], conn)
    cookies["session_token"] = ""
    cookies.save()
    st.session_state.clear()
    st.rerun()

def app_principal(conn, cookies):
    st.title("🔐 Acesso ao softMASSA")

    if st.session_state.get('logado'):
        st.write(f"Olá, {st.session_state['usuario']}! Você está logado.")
        if st.button("Continuar", key="botao_logout"):
            logout(conn, cookies)
    else:
        login_usuario(conn, cookies)

def checar_sessao(conn, cookies):
    if st.session_state.get('logado'):
        return

    token = cookies.get("session_token")
    if token:
        usuario_id = validar_token(token, conn)
        if usuario_id:
            st.session_state['logado'] = True
            st.session_state['usuario_id'] = usuario_id
            st.session_state['usuario'] = obter_nome_usuario_por_id(usuario_id, conn)

            # Obtém o tipo do usuário
            cursor = conn.cursor()
            cursor.execute("SELECT tipo FROM usuarios WHERE id = %s", (usuario_id,))
            resultado = cursor.fetchone()  # ✅ Lê o resultado corretamente
            tipo = resultado[0] if resultado else "comum"
            cursor.close()
            st.session_state['usuario_tipo'] = tipo

            st.session_state['token'] = token
        else:
            cookies["session_token"] = ""
            cookies.save()

# ---------- PONTO DE ENTRADA ------------

def main(cookies):
    conn = conectar()
    if not conn:
        st.error("Erro ao conectar ao banco de dados.")
        st.stop()

    checar_sessao(conn, cookies)
    app_principal(conn, cookies)
    conn.close()
