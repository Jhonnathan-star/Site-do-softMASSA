import streamlit as st
from modules.processa_turno import processa_turno_front
def inserir_telas(conn):
    st.subheader("📅 Inserir dados de telas")

    # Data e dia da semana
    data = st.date_input("Selecione a data", format="YYYY-MM-DD")
    semana = data.strftime("%A")
    domingo_ou_feriado = semana == "Sunday"
    semana_pt = data.strftime("%A").capitalize()

    st.write(f"🗓️ Dia selecionado: **{semana_pt}**")

    # Turno da manhã
    telas_grossa_manha = st.number_input("Telas grossa - manhã", min_value=0, step=1)
    telas_fina_manha = st.number_input("Telas fina - manhã", min_value=0, step=1)

    # Turno da tarde (desabilitado se domingo)
    if not domingo_ou_feriado:
        telas_grossa_tarde = st.number_input("Telas grossa - tarde", min_value=0, step=1)
        telas_fina_tarde = st.number_input("Telas fina - tarde", min_value=0, step=1)
    else:
        telas_grossa_tarde = 0
        telas_fina_tarde = 0
        st.info("É domingo. Dados da tarde serão inseridos como 0.")

    # Pergunta se deseja adicionar dados de horários
    opcao = st.radio("Deseja inserir também os dados na tabela 'horários'?", ["Sim", "Não"], horizontal=True)

    # Botão de inserção
    if st.button("Inserir dados de telas"):
        try:
            cursor = conn.cursor()

            sql = """
                INSERT INTO telas (
                    data, semana,
                    telas_grossa_manha, telas_grossa_tarde,
                    telas_fina_manha, telas_fina_tarde
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            valores = (
                data.strftime("%Y-%m-%d"),
                semana,
                telas_grossa_manha, telas_grossa_tarde,
                telas_fina_manha, telas_fina_tarde
            )
            cursor.execute(sql, valores)
            conn.commit()

            cursor.execute("SELECT LAST_INSERT_ID()")
            id_telas = cursor.fetchone()[0]

            st.success(f"✅ Dados inseridos com sucesso para {semana_pt} ({data.strftime('%Y-%m-%d')})")

            # Salva no session_state
            st.session_state.show_horarios = (opcao == "Sim")
            st.session_state.id_telas = id_telas
            st.session_state.valores_telas = {
                "telas_grossa_manha": telas_grossa_manha,
                "telas_grossa_tarde": telas_grossa_tarde,
                "telas_fina_manha": telas_fina_manha,
                "telas_fina_tarde": telas_fina_tarde,
                "domingo_ou_feriado": domingo_ou_feriado
            }

        except Exception as e:
            st.error(f"❌ Erro ao inserir dados: {e}")

    # Mostra a tela de horários se necessário
    if st.session_state.get("show_horarios", False):
        st.info("📌 Insira agora os dados de horários para cada turno:")
        processa_turno_front(
            conn,
            st.session_state.id_telas,
            st.session_state.valores_telas["telas_grossa_manha"],
            st.session_state.valores_telas["telas_grossa_tarde"],
            st.session_state.valores_telas["telas_fina_manha"],
            st.session_state.valores_telas["telas_fina_tarde"],
            st.session_state.valores_telas["domingo_ou_feriado"]
        )
