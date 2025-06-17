import streamlit as st
from mysql.connector import connect, Error
from modules.auth_utils import check_password, salvar_token, validar_token, marcar_token_expirado
from modules.auth_utils import gerar_token_recuperacao
from modules.email import enviar_email
from dotenv import load_dotenv
import os

load_dotenv()

def get_port(env_var_name, default=3306):
    port_str = os.getenv(env_var_name)
    try:
        return int(port_str)
    except (TypeError, ValueError):
        return default

db_config_padaria1 = {
    "host": os.getenv("DB_HOST_PADARIA1"),
    "port": get_port("DB_PORT_PADARIA1"),
    "user": os.getenv("DB_USER_PADARIA1"),
    "password": os.getenv("DB_PASSWORD_PADARIA1"),
    "database": os.getenv("DB_NAME_PADARIA1"),
}

db_config_padaria2 = {
    "host": os.getenv("DB_HOST_PADARIA2"),
    "port": get_port("DB_PORT_PADARIA2"),
    "user": os.getenv("DB_USER_PADARIA2"),
    "password": os.getenv("DB_PASSWORD_PADARIA2"),
    "database": os.getenv("DB_NAME_PADARIA2"),
}

def conectar(db_config):
    try:
        conn = connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
        )
        if conn.is_connected():
            print(f"Conectado ao banco {db_config['database']} em {db_config['host']}")
            return conn
    except Error as e:
        print(f"Erro ao conectar: {e}")
        return None


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

def encontrar_banco_do_usuario(usuario):
    # Tenta no banco da padaria 1
    conn1 = conectar(db_config_padaria1)
    if conn1:
        dados = obter_usuario_por_nome(conn1, usuario)
        conn1.close()
        if dados:
            return db_config_padaria1

    # Tenta no banco da padaria 2
    conn2 = conectar(db_config_padaria2)
    if conn2:
        dados = obter_usuario_por_nome(conn2, usuario)
        conn2.close()
        if dados:
            return db_config_padaria2

    return None

def login_usuario(cookies):
    st.subheader("Login")
    usuario = st.text_input("Usuário", key="login_usuario")
    senha = st.text_input("Senha", type="password", key="login_senha")

    esqueceu_senha = st.checkbox("Esqueci minha senha", key="checkbox_esqueci_senha")

    if esqueceu_senha:
        st.info("Digite seu nome de usuário para receber instruções de recuperação.")
        usuario_recuperar = st.text_input("Usuário para recuperação", key="recuperar_usuario")

        if st.button("Enviar instruções de recuperação", key="botao_recuperar"):
            if not usuario_recuperar:
                st.warning("Por favor, digite o nome de usuário.")
            else:
                banco = encontrar_banco_do_usuario(usuario_recuperar)
                if not banco:
                    st.error("Usuário para recuperação não encontrado.")
                    return

                conn = conectar(banco)
                if not conn:
                    st.error("Erro ao conectar ao banco para recuperação.")
                    return

                cursor = conn.cursor()
                cursor.execute("SELECT id, email FROM usuarios WHERE usuario = %s", (usuario_recuperar,))
                resultado = cursor.fetchone()
                cursor.close()

                if resultado:
                    usuario_id, email_destino = resultado

                    if not email_destino or email_destino.strip() == "":
                        st.error(f"{usuario_recuperar}, você não tem e-mail cadastrado. Entre em contato com o administrador.")
                        conn.close()
                        return

                    token = gerar_token_recuperacao(usuario_id, conn)
                    conn.close()

                    link = f"https://site-do-softmassa-evoj9v7l97aat9i6fptryx.streamlit.app/?token={token}"

                    enviar_email(email_destino, link)
                    st.success("✅ Instruções de recuperação foram enviadas para seu e-mail.")
                else:
                    st.error("Usuário não encontrado no banco.")

    if st.button("Entrar", key="botao_entrar"):
        if not usuario or not senha:
            st.warning("Preencha usuário e senha.")
            return

        banco_usuario = encontrar_banco_do_usuario(usuario)
        if banco_usuario is None:
            st.error("Usuário não encontrado em nenhum banco.")
            return

        conn = conectar(banco_usuario)
        if not conn:
            st.error("Erro ao conectar ao banco de dados do usuário.")
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
                st.session_state['banco_config'] = banco_usuario  # Salva o banco para usar depois

                st.success(f"Bem-vindo, {usuario}!")
                st.rerun()
            else:
                st.error("Senha incorreta.")
        else:
            st.error("Usuário não encontrado.")
        conn.close()

def logout(conn, cookies):
    if 'token' in st.session_state:
        marcar_token_expirado(st.session_state['token'], conn)
    cookies["session_token"] = ""
    cookies.save()
    st.session_state.clear()
    st.rerun()

def app_principal(cookies):
    st.title("🔐 Acesso ao softMASSA")

    if st.session_state.get('logado'):
        st.write(f"Olá, {st.session_state['usuario']}! Você está logado.")
        if st.button("Entrar", key="botao_logout"):
            # Usa o banco salvo na sessão para logout
            banco = st.session_state.get('banco_config')
            if banco:
                conn = conectar(banco)
                if conn:
                    logout(conn, cookies)
                    conn.close()
                else:
                    st.error("Erro ao conectar para logout.")
            else:
                st.error("Banco do usuário não definido.")
    else:
        login_usuario(cookies)

def checar_sessao(cookies):
    if st.session_state.get('logado'):
        return

    token = cookies.get("session_token")
    if token:
        # Como o token está relacionado a um usuário em um banco específico, 
        # precisamos tentar validar o token nos dois bancos:
        for banco in [db_config_padaria1, db_config_padaria2]:
            conn = conectar(banco)
            if not conn:
                continue
            usuario_id = validar_token(token, conn)
            conn.close()
            if usuario_id:
                st.session_state['logado'] = True
                st.session_state['usuario_id'] = usuario_id
                st.session_state['usuario'] = obter_nome_usuario_por_id(usuario_id, conectar(banco))
                st.session_state['usuario_tipo'] = "comum"  # Ou buscar no banco se quiser
                st.session_state['token'] = token
                st.session_state['banco_config'] = banco
                return

        # Se não achou token válido em nenhum banco:
        cookies["session_token"] = ""
        cookies.save()

def main(cookies):
    checar_sessao(cookies)
    app_principal(cookies)
