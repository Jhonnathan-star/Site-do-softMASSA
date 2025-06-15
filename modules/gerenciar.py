import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

def gerenciar_telas(conn):
    st.header("📅 Gerenciar Telas por Data")

    data = st.date_input("Selecione a data", format="YYYY-MM-DD")
    semana = data.strftime("%A")
    domingo = semana == "Sunday"
    semana_pt = data.strftime("%A").capitalize()
    feriado = st.checkbox("📌 Marcar caso for feriado")
    desativar_tarde = domingo or feriado

    st.write(f"🗓️ Dia selecionado: **{semana_pt}**{' (Feriado)' if feriado else ''}")

    # Buscar sugestões da semana passada (mesmo dia da semana anterior)
    sugestoes = {"grossa_manha": None, "grossa_tarde": None, "fina_manha": None, "fina_tarde": None}
    data_anterior = data - timedelta(days=7)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT telas_grossa_manha, telas_grossa_tarde, telas_fina_manha, telas_fina_tarde
        FROM telas_vendidas3
        WHERE data = %s
    """, (data_anterior,))
    venda_antiga = cursor.fetchone()
    if venda_antiga:
        sugestoes["grossa_manha"], sugestoes["grossa_tarde"], sugestoes["fina_manha"], sugestoes["fina_tarde"] = venda_antiga

    # Verificar se já existe registro para essa data
    cursor.execute("""
        SELECT id_telas, data, semana, telas_grossa_manha, telas_grossa_tarde, telas_fina_manha, telas_fina_tarde
        FROM telas
        WHERE data = %s
    """, (data,))
    registros = cursor.fetchall()

    if registros:
        st.subheader("✏️ Registro existente - Alterar ou Excluir")
        for r in registros:
            id_telas, data_str, semana, g_m, g_t, f_m, f_t = r
            with st.expander(f"📄 Registro - {data_str} (Semana {semana})", expanded=True):
                nova_grossa_manha = st.number_input(
                    f"Telas Grossa (Manhã){f' - vendido sem. passada: {sugestoes['grossa_manha']}' if sugestoes['grossa_manha'] is not None else ''}",
                    min_value=0, value=g_m, key=f"g_m_{id_telas}"
                )
                nova_grossa_tarde = st.number_input(
                    f"Telas Grossa (Tarde){f' - vendido sem. passada: {sugestoes['grossa_tarde']}' if sugestoes['grossa_tarde'] is not None else ''}",
                    min_value=0, value=g_t, key=f"g_t_{id_telas}"
                ) if not desativar_tarde else 0
                nova_fina_manha = st.number_input(
                    f"Telas Fina (Manhã){f' - vendido sem. passada: {sugestoes['fina_manha']}' if sugestoes['fina_manha'] is not None else ''}",
                    min_value=0, value=f_m, key=f"f_m_{id_telas}"
                )
                nova_fina_tarde = st.number_input(
                    f"Telas Fina (Tarde){f' - vendido sem. passada: {sugestoes['fina_tarde']}' if sugestoes['fina_tarde'] is not None else ''}",
                    min_value=0, value=f_t, key=f"f_t_{id_telas}"
                ) if not desativar_tarde else 0

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Atualizar Registro", key=f"atualiza_{id_telas}"):
                        cursor.execute("""
                            UPDATE telas SET
                                telas_grossa_manha = %s,
                                telas_grossa_tarde = %s,
                                telas_fina_manha = %s,
                                telas_fina_tarde = %s
                            WHERE id_telas = %s
                        """, (nova_grossa_manha, nova_grossa_tarde, nova_fina_manha, nova_fina_tarde, id_telas))
                        conn.commit()
                        st.success("✅ Registro atualizado com sucesso!")

                with col2:
                    # Inicializa flag de confirmação exclusão se não existir
                    if f"confirmar_excluir_{id_telas}" not in st.session_state:
                        st.session_state[f"confirmar_excluir_{id_telas}"] = False

                    if not st.session_state[f"confirmar_excluir_{id_telas}"]:
                        if st.button("🗑️ Excluir Registro", key=f"btn_excluir_{id_telas}"):
                            st.session_state[f"confirmar_excluir_{id_telas}"] = True
                    else:
                        st.warning("⚠️ Deseja realmente excluir este registro?")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Sim, excluir", key=f"btn_sim_{id_telas}"):
                            cursor.execute("DELETE FROM horarios WHERE id_telas = %s", (id_telas,))
                            cursor.execute("DELETE FROM telas_vendidas3 WHERE id_telas = %s", (id_telas,))
                            cursor.execute("DELETE FROM telas WHERE id_telas = %s", (id_telas,))
                            conn.commit()
                            st.success("🗑️ Registro excluído com sucesso!")
                            st.session_state[f"confirmar_excluir_{id_telas}"] = False
                            st.rerun()
                        if c2.button("❌ Não, cancelar", key=f"btn_nao_{id_telas}"):
                            st.session_state[f"confirmar_excluir_{id_telas}"] = False
                            st.rerun()

    else:
        st.subheader("➕ Nenhum registro - Inserir novos dados")
        telas_grossa_manha = st.number_input(
            f"📌 Telas Grossa - Manhã{f' (vendido sem. passada: {sugestoes['grossa_manha']})' if sugestoes['grossa_manha'] is not None else ''}",
            min_value=0, step=1
        )
        telas_grossa_tarde = st.number_input(
            f"📌 Telas Grossa - Tarde{f' (vendido sem. passada: {sugestoes['grossa_tarde']})' if sugestoes['grossa_tarde'] is not None else ''}",
            min_value=0, step=1
        ) if not desativar_tarde else 0

        telas_fina_manha = st.number_input(
            f"📌 Telas Fina - Manhã{f' (vendido sem. passada: {sugestoes['fina_manha']})' if sugestoes['fina_manha'] is not None else ''}",
            min_value=0, step=1
        )
        telas_fina_tarde = st.number_input(
            f"📌 Telas Fina - Tarde{f' (vendido sem. passada: {sugestoes['fina_tarde']})' if sugestoes['fina_tarde'] is not None else ''}",
            min_value=0, step=1
        ) if not desativar_tarde else 0

        if desativar_tarde:
            st.info("É domingo ou feriado. Campos da tarde serão registrados como 0 automaticamente.")

        if st.button("Inserir dados de telas"):
            try:
                cursor.execute("""
                    INSERT INTO telas (
                        data, semana,
                        telas_grossa_manha, telas_grossa_tarde,
                        telas_fina_manha, telas_fina_tarde
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (data.strftime("%Y-%m-%d"), semana, telas_grossa_manha, telas_grossa_tarde, telas_fina_manha, telas_fina_tarde))
                conn.commit()
                st.success(f"✅ Dados inseridos com sucesso para {semana_pt} ({data.strftime('%Y-%m-%d')})")
            except Exception as e:
                st.error(f"❌ Erro ao inserir dados: {e}")

    cursor.close()
