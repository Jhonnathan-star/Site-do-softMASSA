import streamlit as st

# --- Configuração da página ---
st.set_page_config(page_title="softMASSA", layout="centered")

from datetime import datetime, time, timedelta
import pandas as pd
import os

from database.connection import conectar
from modules.login import main as login_main, marcar_token_expirado
from modules.inserir_telas import inserir_telas
from modules.processa_turno import inserir_horarios_separados_front, buscar_historico_por_data
from modules.predicao import criar_predicao_semana
from modules.ver_alterar import ver_e_alterar_telas_por_data
from modules.pedidos import inserir_pedidos_automatizado, inserir_pedidos_manual
from components.ver_conta_funcionario import ver_conta_funcionario
from modules.cadastrar import gerenciar_usuarios
from streamlit_cookies_manager import EncryptedCookieManager

# --- Inicialização de Cookies ---
cookie_password = os.getenv("COOKIE_PASSWORD")
if not cookie_password:
    st.error("❌ Variável de ambiente 'COOKIE_PASSWORD' não definida.")
    st.stop()

cookies = EncryptedCookieManager(prefix="meuapp/", password=cookie_password)
if not cookies.ready():
    st.stop()

# --- Inicializar estados da sessão ---
st.session_state.setdefault("logado", False)
st.session_state.setdefault("usuario", None)
st.session_state.setdefault("pagina", "Home")
st.session_state.setdefault("usuario_tipo", "comum")
st.session_state.setdefault("mostrar_menu", True)
st.session_state.setdefault("mostrar_menu_usuario", False)

# --- Função utilitária para conexão e execução segura ---
def executar_pagina(funcao):
    conn = conectar()
    if not conn:
        st.error("❌ Não foi possível conectar ao banco de dados.")
        return
    try:
        funcao(conn)
    finally:
        conn.close()

# --- Função de logout ---
def logout():
    if 'token' in st.session_state:
        conn = conectar()
        if conn:
            try:
                marcar_token_expirado(st.session_state['token'], conn)
            finally:
                conn.close()
    cookies["session_token"] = ""
    cookies.save()
    st.session_state.clear()
    st.rerun()

# --- Verifica sessão antes de prosseguir ---
conn = conectar()
if not conn:
    st.error("❌ Erro ao conectar ao banco de dados.")
    st.stop()

if not st.session_state["logado"]:
    login_main(cookies)
    conn.close()
    st.stop()

conn.close()

# --- Definir opções do menu ---
if st.session_state['usuario_tipo'] == "admin":
    opcoes = [
        "Inserir telas",
        "Registrar horários",
        "Alterar telas",
        "Histórico por data",
        "Predição semanal com IA",
        "Previsão manual de pedidos",
        "Previsão automática de pedidos",
        "Ver conta do funcionário",
        "Gerenciar usuários"
    ]
else:
    opcoes = [
        "Registrar horários",
        "Histórico por data",
        "Ver conta do funcionário"
    ]

# --- Página atual ---
pagina = st.session_state.get("pagina", "Home")

# --- Barra superior: botão menu + usuário + perfil ---
col_top = st.columns([1, 8, 3])

# Botão suspenso (menu) no canto superior esquerdo
with col_top[0]:
    st.markdown("""
        <style>
            .css-18ni7ap {
                padding: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    if not st.session_state["mostrar_menu"]:
        if st.button("☰", key="open_menu", help="Menu"):
            st.session_state["mostrar_menu"] = True
            st.session_state["pagina"] = "Home"
            st.rerun()

# Título apenas na Home
with col_top[1]:
    if pagina == "Home":
        st.markdown("## 🍞 Sistema da softMASSA")

with col_top[2]:
    perfil_col1, perfil_col2 = st.columns([5, 1])
    with perfil_col1:
        st.markdown(
            f"""
            <div style='
                font-size: 11px;
                line-height: 32px;
                text-align: right;
                padding-right: 6px;
                white-space: nowrap;
                max-width: 150px;
                overflow: hidden;
                text-overflow: ellipsis;
            '>
                {st.session_state.get('usuario', '')}({st.session_state.get('usuario_tipo', '').lower()})
            </div>
            """,
            unsafe_allow_html=True,
        )
    with perfil_col2:
        if st.button("👤", key="perfil_btn", help="Perfil"):
            st.session_state["mostrar_menu_usuario"] = not st.session_state["mostrar_menu_usuario"]

        if st.session_state["mostrar_menu_usuario"]:
            st.markdown("""
                <style>
                div.stButton > button:first-child {
                    font-size: 8px !important;
                    padding: 2px 6px !important;
                    min-width: 40px !important;
                    white-space: nowrap !important;
                    height: 22px !important;
                    margin-top: -4px !important;  /* valor negativo para colar */
                }
                </style>
                """, unsafe_allow_html=True)
            if st.button("Sair", key="logout_btn"):
                logout()


# --- Menu lateral ---
if st.session_state["mostrar_menu"]:
    with st.sidebar:
        st.markdown("## 🍞 Sistema da softMASSA")
        st.markdown("### 📂 Menu")
        for opcao in opcoes:
            if st.button(opcao, use_container_width=True):
                st.session_state["pagina"] = opcao
                st.session_state["mostrar_menu"] = False
                st.rerun()

# --- Conteúdo das páginas ---
if pagina == "Home":
    st.success(f"Bem-vindo, {st.session_state['usuario']}!")
    st.write("Página inicial do sistema.")

elif pagina == "Inserir telas":
    executar_pagina(inserir_telas)

elif pagina == "Registrar horários":
    executar_pagina(inserir_horarios_separados_front)

elif pagina == "Alterar telas":
    executar_pagina(ver_e_alterar_telas_por_data)

elif pagina == "Histórico por data":
    executar_pagina(buscar_historico_por_data)

elif pagina == "Predição semanal com IA":
    executar_pagina(criar_predicao_semana)

elif pagina == "Previsão manual de pedidos":
    executar_pagina(inserir_pedidos_manual)

elif pagina == "Previsão automática de pedidos":
    executar_pagina(inserir_pedidos_automatizado)

elif pagina == "Ver conta do funcionário":
    executar_pagina(ver_conta_funcionario)

elif pagina == "Gerenciar usuários":
    executar_pagina(gerenciar_usuarios)