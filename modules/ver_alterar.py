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
            id_telas, data, semana, g_m, g_t, f_m, f_t = r
            with st.expander(f"📄 Registro - {data} (Semana {semana})", expanded=True):
                st.write(f"**Data:** {data}")
                st.write(f"**Semana:** {semana}")

                nova_grossa_manha = st.number_input("Telas Grossa (Manhã)", min_value=0, value=g_m, key=f"g_m_{id_telas}")
                nova_grossa_tarde = st.number_input("Telas Grossa (Tarde)", min_value=0, value=g_t, key=f"g_t_{id_telas}")
                nova_fina_manha = st.number_input("Telas Fina (Manhã)", min_value=0, value=f_m, key=f"f_m_{id_telas}")
                nova_fina_tarde = st.number_input("Telas Fina (Tarde)", min_value=0, value=f_t, key=f"f_t_{id_telas}")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("💾 Atualizar Registro", key=f"atualiza_{id_telas}"):
                        # Atualiza tabela telas
                        cursor.execute("""
                            UPDATE telas SET
                                telas_grossa_manha = %s,
                                telas_grossa_tarde = %s,
                                telas_fina_manha = %s,
                                telas_fina_tarde = %s
                            WHERE id_telas = %s
                        """, (nova_grossa_manha, nova_grossa_tarde, nova_fina_manha, nova_fina_tarde, id_telas))
                        conn.commit()

                        # Dicionário com os novos totais
                        novos_totais = {
                            ('grossa', 'manha'): nova_grossa_manha,
                            ('grossa', 'tarde'): nova_grossa_tarde,
                            ('fina', 'manha'): nova_fina_manha,
                            ('fina', 'tarde'): nova_fina_tarde,
                        }

                        # Atualiza valores de quantidade_vendida em horarios
                        for (tipo_pao, turno), novo_total in novos_totais.items():
                            cursor.execute("""
                                SELECT id, sobra FROM horarios
                                WHERE id_telas = %s AND tipo_pao = %s AND turno = %s
                            """, (id_telas, tipo_pao, turno))
                            registros_horarios = cursor.fetchall()

                            for id_horario, sobra in registros_horarios:
                                nova_venda = max(novo_total - (sobra or 0), 0)
                                cursor.execute("""
                                    UPDATE horarios SET quantidade_vendida = %s WHERE id = %s
                                """, (nova_venda, id_horario))

                                # Atualiza ou insere na telas_vendidas3
                                coluna = f"telas_{tipo_pao}_{turno}"
                                cursor.execute("SELECT COUNT(*) FROM telas_vendidas3 WHERE id_telas = %s", (id_telas,))
                                existe = cursor.fetchone()[0]

                                if existe:
                                    cursor.execute(f"""
                                        UPDATE telas_vendidas3 SET {coluna} = %s WHERE id_telas = %s
                                    """, (nova_venda, id_telas))
                                else:
                                    cursor.execute("""
                                        INSERT INTO telas_vendidas3 (id_telas, {}, data, semana)
                                        VALUES (%s, %s, %s, %s)
                                    """.format(coluna), (id_telas, nova_venda, data, semana))

                        conn.commit()
                        st.success("✅ Registro e vendas atualizados com sucesso!")

                with col2:
                    if st.button("🗑️ Excluir Registro", key=f"excluir_{id_telas}"):
                        st.session_state[f"mostrar_confirmacao_{id_telas}"] = True

                    if st.session_state.get(f"mostrar_confirmacao_{id_telas}", False):
                        confirma = st.checkbox("Confirmar exclusão do registro", key=f"confirma_excluir_{id_telas}")
                        if confirma:
                            cursor.execute("DELETE FROM horarios WHERE id_telas = %s", (id_telas,))
                            cursor.execute("DELETE FROM telas_vendidas3 WHERE id_telas = %s", (id_telas,))
                            cursor.execute("DELETE FROM telas WHERE id_telas = %s", (id_telas,))
                            conn.commit()
                            st.success("🗑️ Registro excluído com sucesso!")
                            st.session_state[f"mostrar_confirmacao_{id_telas}"] = False
                            st.rerun()

        cursor.close()
