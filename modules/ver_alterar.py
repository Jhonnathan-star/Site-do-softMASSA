import streamlit as st
from datetime import datetime

def ver_e_alterar_telas_por_data(conn):
    st.header("🔍 Ver, Alterar ou Excluir Telas por Data")

    if 'consultou_data' not in st.session_state:
        st.session_state.consultou_data = False

    data_input = st.date_input("Selecione a data que deseja consultar:", format="YYYY-MM-DD")

    if st.button("Consultar"):
        st.session_state.consultou_data = True
        st.session_state.data_input_salva = data_input

    if st.session_state.consultou_data:
        data_consulta = st.session_state.data_input_salva

        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_telas, data, semana, telas_grossa_manha, telas_grossa_tarde, telas_fina_manha, telas_fina_tarde
            FROM telas
            WHERE data = %s
        """, (data_consulta,))

        registros = cursor.fetchall()

        if not registros:
            st.warning("⚠️ Nenhum dado encontrado para essa data.")
            st.session_state.consultou_data = False
            return

        for r in registros:
            with st.expander(f"📄 Registro - {r[1]} (Semana {r[2]})", expanded=True):
                st.write(f"**Data:** {r[1]}")
                st.write(f"**Semana:** {r[2]}")

                nova_grossa_manha = st.number_input(
                    "Telas Grossa (Manhã)", min_value=0, value=r[3], key=f"g_m_{r[0]}"
                )
                nova_grossa_tarde = st.number_input(
                    "Telas Grossa (Tarde)", min_value=0, value=r[4], key=f"g_t_{r[0]}"
                )
                nova_fina_manha = st.number_input(
                    "Telas Fina (Manhã)", min_value=0, value=r[5], key=f"f_m_{r[0]}"
                )
                nova_fina_tarde = st.number_input(
                    "Telas Fina (Tarde)", min_value=0, value=r[6], key=f"f_t_{r[0]}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("💾 Atualizar Registro", key=f"atualiza_{r[0]}"):
                        cursor.execute("""
                            UPDATE telas SET
                                telas_grossa_manha = %s,
                                telas_grossa_tarde = %s,
                                telas_fina_manha = %s,
                                telas_fina_tarde = %s
                            WHERE id_telas = %s
                        """, (nova_grossa_manha, nova_grossa_tarde, nova_fina_manha, nova_fina_tarde, r[0]))
                        conn.commit()
                        st.success("✅ Registro atualizado com sucesso!")

                with col2:
                    if st.button("🗑️ Excluir Registro", key=f"excluir_{r[0]}"):
                        st.session_state[f"mostrar_confirmacao_{r[0]}"] = True

                    if st.session_state.get(f"mostrar_confirmacao_{r[0]}", False):
                        confirma = st.checkbox("Confirmar exclusão do registro", key=f"confirma_excluir_{r[0]}")
                        if confirma:
                            cursor.execute("DELETE FROM telas WHERE id_telas = %s", (r[0],))
                            conn.commit()
                            st.success("🗑️ Registro excluído com sucesso!")
                            st.session_state[f"mostrar_confirmacao_{r[0]}"] = False
                            st.rerun()

        cursor.close()
