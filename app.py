import streamlit as st
# --- Configuração da página ---
st.set_page_config(page_title="softMASSA", layout="centered")
import os
from database.connection import conectar
from modules.login import main as login_main, marcar_token_expirado
from modules.processa_turno import inserir_horarios_separados_front, buscar_historico_por_data
from modules.predicao import criar_predicao_semana
from modules.pedidos import pagina_previsao_pedidos
from components.ver_conta_funcionario import ver_conta_funcionario
from modules.cadastrar import gerenciar_usuarios
from streamlit_cookies_manager import EncryptedCookieManager
from modules.gerenciar import gerenciar_telas 
from modules.producao import main as producao_main

# --- Verificar se é link de redefinição de senha ---
query_params = st.query_params
if "token" in query_params:
    from modules.Reiniciar_Senha import mostrar_redefinir_senha
    mostrar_redefinir_senha()
    st.stop()

# --- Inicialização de Cookies ---
cookie_password = os.getenv("COOKIE_PASSWORD")
if not cookie_password:
    st.error("❌ Variável de ambiente 'COOKIE_PASSWORD' não definida.")
    st.stop()

cookies = EncryptedCookieManager(prefix="meuapp/", password=cookie_password)
if not cookies.ready():
    st.stop()

# --- Inicializar sessão ---
st.session_state.setdefault("logado", False)
st.session_state.setdefault("usuario", None)
st.session_state.setdefault("pagina", "Home")
st.session_state.setdefault("usuario_tipo", "comum")
if "menu_visivel" not in st.session_state:
    st.session_state.menu_visivel = False  # começa escondido

# --- Função utilitária para conectar e executar, usando banco da sessão ---
def executar_pagina(funcao):
    banco_config = st.session_state.get('banco_config')
    if banco_config is None:
        st.error("❌ Banco do usuário não definido na sessão.")
        return
    conn = conectar(banco_config)
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
        banco_config = st.session_state.get('banco_config')
        if banco_config:
            conn = conectar(banco_config)
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
if not st.session_state["logado"]:
    login_main(cookies)
    st.stop()

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
                "Gerenciar telas",
                "Registrar horários",
                "Histórico por data",
                "Predição semanal com IA",
                "Previsão de pedidos",
                "Ver conta do funcionário",
                "Gerenciar usuários",
                "Produção e Lucro"
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

elif pagina == "Gerenciar telas":
    executar_pagina(gerenciar_telas)

elif pagina == "Registrar horários":
    executar_pagina(inserir_horarios_separados_front)

elif pagina == "Histórico por data":
    executar_pagina(buscar_historico_por_data)

elif pagina == "Predição semanal com IA":
    executar_pagina(criar_predicao_semana)

elif pagina == "Previsão de pedidos":
    executar_pagina(pagina_previsao_pedidos)

elif pagina == "Ver conta do funcionário":
    executar_pagina(ver_conta_funcionario)

elif pagina == "Gerenciar usuários":
    executar_pagina(gerenciar_usuarios)

elif pagina == "Produção e Lucro":
    producao_main()

