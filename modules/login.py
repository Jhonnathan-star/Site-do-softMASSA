import os
import time
import random
import string
import streamlit as st
from modules.auth_utils import (
    check_password, salvar_token, validar_token, marcar_token_expirado,
    obter_usuario_por_nome, gerar_token_recuperacao
)
from modules.email import enviar_email
from database.connection import conectar

# Gera código de 6 dígitos
def gerar_codigo_verificacao():
    return ''.join(random.choices(string.digits, k=6))

# Armazena códigos temporários
codigo_verificacao_temporario = {}

def obter_nome_usuario_por_id(usuario_id: int, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT usuario FROM usuarios WHERE id = %s", (usuario_id,))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado[0] if resultado else None

def login_usuario(conn, cookies):
    st.subheader("Login")

    if 'etapa_login' not in st.session_state:
        st.session_state['etapa_login'] = 'input_credenciais'

    # Etapa 1: Entrada de usuário e senha
    if st.session_state['etapa_login'] == 'input_credenciais':
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
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, email FROM usuarios WHERE usuario = %s", (usuario_recuperar,))
                    resultado = cursor.fetchone()
                    cursor.close()

                    if resultado:
                        usuario_id, email_destino = resultado
                        if not email_destino:
                            st.error("Usuário sem e-mail cadastrado. Contate o administrador.")
                            return
                        token = gerar_token_recuperacao(usuario_id, conn)
                        link = f"https://site-do-softmassa-evoj9v7l97aat9i6fptryx.streamlit.app/?token={token}"
                        enviar_email(email_destino, link)
                        st.success("✅ Instruções enviadas para o e-mail.")
                    else:
                        st.error("Usuário não encontrado.")

        if st.button("Entrar", key="botao_entrar"):
            if not usuario or not senha:
                st.warning("Preencha usuário e senha.")
                return

            dados = obter_usuario_por_nome(conn, usuario)
            if dados:
                usuario_id, senha_hashed, tipo_usuario = dados
                if check_password(senha, senha_hashed):
                    cursor = conn.cursor()
                    cursor.execute("SELECT email FROM usuarios WHERE id = %s", (usuario_id,))
                    resultado = cursor.fetchone()
                    cursor.close()
                    email = resultado[0] if resultado else None

                    if not email:
                        st.error("Usuário sem e-mail cadastrado.")
                        return

                    codigo = gerar_codigo_verificacao()
                    codigo_verificacao_temporario[usuario] = (codigo, time.time())

                    # Salva dados temporários na sessão
                    st.session_state.update({
                        'usuario_temp': usuario,
                        'senha_temp': senha,
                        'usuario_id_temp': usuario_id,
                        'usuario_tipo_temp': tipo_usuario,
                        'etapa_login': 'enviando_codigo'
                    })
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
            else:
                st.error("Usuário não encontrado.")

    # Etapa 2: Envio do código
    elif st.session_state['etapa_login'] == 'enviando_codigo':
        usuario = st.session_state.get('usuario_temp')
        usuario_id = st.session_state.get('usuario_id_temp')

        codigo, _ = codigo_verificacao_temporario.get(usuario, ("", 0))

        cursor = conn.cursor()
        cursor.execute("SELECT email FROM usuarios WHERE id = %s", (usuario_id,))
        resultado = cursor.fetchone()
        cursor.close()
        email = resultado[0] if resultado else None

        with st.spinner('Enviando código de verificação para seu e-mail, aguarde...'):
            enviar_email(email, f"Seu código de verificação: {codigo}")
            time.sleep(0.5)

        st.success("Código enviado com sucesso!")
        st.session_state['etapa_login'] = 'verificar_codigo'
        st.rerun()

    # Etapa 3: Verificação do código
    elif st.session_state['etapa_login'] == 'verificar_codigo':
        st.write("Digite o código de verificação enviado ao seu e-mail:")
        codigo_digitado = st.text_input("Código de verificação", key="input_codigo")

        if st.button("Verificar código"):
            usuario = st.session_state.get('usuario_temp')
            senha = st.session_state.get('senha_temp')
            usuario_id = st.session_state.get('usuario_id_temp')
            tipo_usuario = st.session_state.get('usuario_tipo_temp')

            dados = obter_usuario_por_nome(conn, usuario)
            if dados:
                codigo_salvo, timestamp = codigo_verificacao_temporario.get(usuario, ("", 0))
                if time.time() - timestamp > 90:
                    st.error("⏰ Código expirado. Tente novamente.")
                    st.session_state['etapa_login'] = 'input_credenciais'
                    return

                if codigo_digitado == codigo_salvo:
                    token = salvar_token(usuario_id, conn)

                    cookies["session_token"] = token  # Salva como string
                    cookies.save()

                    st.session_state.update({
                        'logado': True,
                        'usuario_id': usuario_id,
                        'usuario': usuario,
                        'usuario_tipo': tipo_usuario,
                        'token': token,
                        'etapa_login': 'input_credenciais'
                    })

                    # Limpa variáveis temporárias
                    codigo_verificacao_temporario.pop(usuario, None)
                    for key in ['usuario_temp', 'senha_temp', 'usuario_id_temp', 'usuario_tipo_temp']:
                        st.session_state.pop(key, None)

                    st.success(f"✅ Bem-vindo, {usuario}!")
                    st.rerun()
                else:
                    st.error("❌ Código incorreto.")

def logout(conn, cookies):
    if 'token' in st.session_state:
        marcar_token_expirado(st.session_state['token'], conn)

    cookies["session_token"] = ""  # Expira imediatamente
    cookies.save()
    st.session_state.clear()
    st.rerun()

def app_principal(conn, cookies):
    st.title("🔐 Acesso ao softMASSA")
    if st.session_state.get('logado'):
        st.write(f"Olá, {st.session_state['usuario']}! Você está logado.")
        if st.button("Sair", key="botao_logout"):
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
            st.session_state.update({
                'logado': True,
                'usuario_id': usuario_id,
                'usuario': obter_nome_usuario_por_id(usuario_id, conn)
            })

            cursor = conn.cursor()
            cursor.execute("SELECT tipo FROM usuarios WHERE id = %s", (usuario_id,))
            resultado = cursor.fetchone()
            cursor.close()
            st.session_state['usuario_tipo'] = resultado[0] if resultado else "comum"
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
