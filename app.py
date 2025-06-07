import streamlit as st
from database.connection import conectar
from modules.inserir_telas import inserir_telas
from modules.processa_turno import inserir_horarios_separados_front, buscar_historico_por_data
from modules.predicao import criar_predicao_semana
from modules.ver_alterar import ver_e_alterar_telas_por_data
from modules.pedidos import inserir_pedidos_automatizado, inserir_pedidos_manual
from modules.login import login_usuario, cadastrar_usuario
from modules.ver_conta import ver_conta_funcionario  # ✅ NOVO IMPORT

# Configuração da página
st.set_page_config(page_title="softMASSA", layout="centered")

# Constantes
SUPERUSUARIO = st.secrets.get("SUPERUSUARIO")

# Inicializa estados da sessão
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "Menu Principal"

# Conecta ao banco
conn = conectar()
if conn is None:
    st.error("Erro ao conectar ao banco de dados.")
    st.stop()

# Se não estiver logado, exibe tela de login
if not st.session_state.logado:
    st.title("🔐 Acesso ao softMASSA")
    login_usuario(conn)
    conn.close()
    st.stop()

# Usuário logado — mostra menu
st.title("🍞 Sistema da softMASSA")
st.success(f"Bem-vindo, {st.session_state.usuario}!")

# Menu lateral
opcoes = [
    "Home",
    "Inserir dados de telas",
    "Inserir somente horários",
    "Ver/Alterar dados das telas",
    "Buscar relatório por data",
    "Ver Conta",  # ✅ NOVA OPÇÃO
]

# Adiciona opções exclusivas do superusuário
if st.session_state.get("superusuario", False):
    opcoes.extend([
        "Criar predição da semana",
        "Previsão automática de pedidos",
        "Previsão manual de pedidos",
        "Cadastrar novo usuário"
    ])

# Seleção do menu
st.sidebar.header("📋 Menu")
st.session_state.pagina = st.sidebar.selectbox("Escolha uma opção:", opcoes)

# Função para execução das páginas com conexão
def executar_pagina(funcao):
    conn = conectar()
    if not conn:
        st.error("❌ Não foi possível conectar ao banco de dados.")
        return
    try:
        funcao(conn)
    finally:
        conn.close()

# Tela Home
if st.session_state.pagina == "Home":
    st.info("Use o menu lateral para navegar pelas funcionalidades.")

    # Botão de logout no menu Home
    col1, col2 = st.columns([7, 1])
    with col2:
        if st.button("🚪 Sair"):
            st.session_state.logado = False
            st.session_state.usuario = None
            st.session_state.pagina = "Home"
            st.rerun()

# Chamada das funcionalidades
elif st.session_state.pagina == "Inserir dados de telas":
    executar_pagina(inserir_telas)

elif st.session_state.pagina == "Inserir somente horários":
    executar_pagina(inserir_horarios_separados_front)

elif st.session_state.pagina == "Ver/Alterar dados das telas":
    executar_pagina(ver_e_alterar_telas_por_data)

elif st.session_state.pagina == "Buscar relatório por data":
    executar_pagina(buscar_historico_por_data)

elif st.session_state.pagina == "Ver Conta":  # ✅ NOVA CHAMADA
    executar_pagina(ver_conta_funcionario)

elif st.session_state.pagina == "Criar predição da semana":
    executar_pagina(criar_predicao_semana)

elif st.session_state.pagina == "Previsão automática de pedidos":
    executar_pagina(inserir_pedidos_automatizado)

elif st.session_state.pagina == "Previsão manual de pedidos":
    executar_pagina(inserir_pedidos_manual)

elif st.session_state.pagina == "Cadastrar novo usuário":
    if st.session_state.usuario == SUPERUSUARIO:
        executar_pagina(cadastrar_usuario)
    else:
        st.error("Acesso negado.")
