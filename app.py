import streamlit as st
st.set_page_config(page_title="softMASSA", layout="centered")
import os
from database.connection import conectar
from modules.login import main as login_main, marcar_token_expirado, gerenciar_usuarios
from modules.inserir_telas import inserir_telas
from modules.processa_turno import inserir_horarios_separados_front, buscar_historico_por_data
from modules.predicao import criar_predicao_semana
from modules.ver_alterar import ver_e_alterar_telas_por_data
from modules.pedidos import inserir_pedidos_automatizado, inserir_pedidos_manual
from components.ver_conta_funcionario import ver_conta_funcionario
from streamlit_cookies_manager import EncryptedCookieManager

# --- Inicialização de Cookies ---
cookie_password = os.getenv("COOKIE_PASSWORD")
if not cookie_password:
    st.error("❌ Variável de ambiente 'COOKIE_PASSWORD' não definida.")
    st.stop()

cookies = EncryptedCookieManager(prefix="meuapp/", password=cookie_password)
if not cookies.ready():
    st.stop()

# --- Variáveis e estados iniciais ---
st.session_state.setdefault("logado", False)
st.session_state.setdefault("usuario", None)
st.session_state.setdefault("pagina", "Menu Principal")
st.session_state.setdefault("usuario_tipo", "comum")  # padrão

# --- Página protegida por login ---
conn = conectar()
if not conn:
    st.error("❌ Erro ao conectar ao banco de dados.")
    st.stop()

if not st.session_state["logado"]:
    login_main(cookies)
    conn.close()
    st.stop()

conn.close()

# --- Título e saudação ---
st.title("🍞 Sistema da softMASSA")
st.success(f"Bem-vindo, {st.session_state['usuario']}!")

# --- Definição do menu com base no tipo de usuário ---
if st.session_state['usuario_tipo'] == "admin":
    opcoes = [
        "Home",
        "Inserir telas",
        "Inserir horários",
        "Alterar telas",
        "Histórico por data",
        "Predição semanal com IA",
        "Previsão manual de pedidos",
        "Previsão automática de pedidos",
        "Ver conta do funcionário",
        "Gerenciar usuários",
        "Sair"
    ]
else:
    opcoes = [
        "Home",
        "Inserir horários",
        "Histórico por data",
        "Ver conta do funcionário",
        "Sair"
    ]

# --- Função utilitária para execução segura ---
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

# --- Interface lateral e controle de páginas ---
pagina = st.sidebar.selectbox("Menu", opcoes)

if pagina == "Sair":
    logout()

elif pagina == "Home":
    st.write("Página inicial do sistema.")

elif pagina == "Inserir telas":
    executar_pagina(inserir_telas)

elif pagina == "Inserir horários":
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