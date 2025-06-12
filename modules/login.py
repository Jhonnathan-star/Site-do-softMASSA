import streamlit as st
from database.connection import conectar
from modules.auth_utils import check_password, salvar_token, validar_token, marcar_token_expirado

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
        if st.button("Entrar", key="botao_logout"):
            logout(conn, cookies)
    else:
        login_usuario(conn, cookies)
        # Caso queira permitir cadastro diretamente no login:
        # cadastrar_usuario(conn)

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

            cursor = conn.cursor()
            cursor.execute("SELECT tipo FROM usuarios WHERE id = %s", (usuario_id,))
            resultado = cursor.fetchone()
            tipo = resultado[0] if resultado else "comum"
            cursor.close()
            st.session_state['usuario_tipo'] = tipo

            st.session_state['token'] = token
        else:
            cookies["session_token"] = ""
            cookies.save()

def main(cookies):
    conn = conectar()
    if not conn:
        st.error("Erro ao conectar ao banco de dados.")
        st.stop()

    checar_sessao(conn, cookies)
    app_principal(conn, cookies)
    conn.close()
    