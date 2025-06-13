import streamlit as st

# --- Configuração da página ---
st.set_page_config(page_title="softMASSA", layout="centered")

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
from modules.Reiniciar_Senha import mostrar_redefinir_senha
from streamlit_cookies_manager import EncryptedCookieManager

# --- Inicialização de Cookies ---
cookie_password = os.getenv("COOKIE_PASSWORD")
if not cookie_password:
    st.error("❌ Variável de ambiente 'COOKIE_PASSWORD' não definida.")
    st.stop()

cookies = EncryptedCookieManager(prefix="meuapp/", password=cookie_password)
if not cookies.ready():
    st.stop()

# --- Verificar se é link de redefinição ---
if "token" in st.query_params:
    mostrar_redefinir_senha()
    st.stop()

# --- Inicializar sessão ---
st.session_state.setdefault("logado", False)
st.session_state.setdefault("usuario", None)
st.session_state.setdefault("pagina", "Home")
st.session_state.setdefault("usuario_tipo", "comum")
if "menu_visivel" not in st.session_state:
    st.session_state.menu_visivel = False  # começa escondido

# --- Função utilitária para conectar e executar ---
def executar_pagina(funcao):
    conn = conectar()
    if not conn:
        st.error("❌ Não foi possível conectar ao banco de dados.")
        return
    try:
        funcao(conn)
    finally:
        conn.close()

# --- Logout ---
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

# --- Autenticação ---
conn = conectar()
if not conn:
    st.error("❌ Erro ao conectar ao banco de dados.")
    st.stop()

if not st.session_state["logado"]:
    login_main(cookies)
    conn.close()
    st.stop()

conn.close()

# --- Botão para mostrar/ocultar menu ---
col1, col2 = st.columns([1, 9])
with col1:
    if st.button("☰"):
        st.session_state.menu_visivel = not st.session_state.menu_visivel

# --- Mostrar o menu se estiver visível ---
if st.session_state.menu_visivel:
    with st.sidebar:
        st.markdown("## 🍞 Sistema da softMASSA")
        st.markdown(f"👤 {st.session_state['usuario']} ({st.session_state['usuario_tipo']})")
        st.markdown("### 📂 Menu")

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

        for opcao in opcoes:
            if st.button(opcao, use_container_width=True):
                st.session_state["pagina"] = opcao
                st.session_state.menu_visivel = False
                st.rerun()

        if st.button("🚪 Sair"):
            logout()

# --- Página inicial ou selecionada ---
pagina = st.session_state.get("pagina", "Home")

if pagina == "Home":
    st.markdown("## 🍞 Sistema da softMASSA")
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

