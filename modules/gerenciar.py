import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from modules.processa_turno import extrair_hora_valida

def gerenciar_telas(conn):
    st.header("📅 Gerenciar Telas por Data")

    data = st.date_input("Selecione a data", format="YYYY-MM-DD")
    data_str = data.strftime("%Y-%m-%d")
    semana = data.strftime("%A")
    domingo = semana == "Sunday"
    semana_pt = data.strftime("%A").capitalize()
    feriado = st.checkbox("📌 Marcar caso for feriado")
    desativar_tarde = domingo or feriado

    st.write(f"🗓️ Dia selecionado: **{semana_pt}**{' (Feriado)' if feriado else ''}")

    # Mostrar histórico da semana anterior
    data_anterior = data - timedelta(days=7)
    st.markdown("### 🔙 Histórico do mesmo dia da semana passada")
    mostrar_historico_para_datas(conn, [data_anterior])

    # Buscar total vendido para telas fina na semana passada (manha e tarde)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.turno, SUM(h.quantidade_vendida)
        FROM telas t
        JOIN horarios h ON t.id_telas = h.id_telas
        WHERE t.data = %s AND h.tipo_pao = 'fina'
        GROUP BY h.turno
    """, (data_anterior,))
    resultados_vendidos = dict(cursor.fetchall())
    fina_manha_vendida = int(resultados_vendidos.get('manha', 0))
    fina_tarde_vendida = int(resultados_vendidos.get('tarde', 0))

    # Inicializa chaves no session_state para evitar KeyError, sempre que trocar data
    if "data_selecionada" not in st.session_state or st.session_state.data_selecionada != data_str:
        st.session_state.data_selecionada = data_str

        st.session_state[f"g_manha_{data_str}"] = 0
        st.session_state[f"g_tarde_{data_str}"] = 0
        st.session_state[f"f_manha_{data_str}"] = fina_manha_vendida
        st.session_state[f"f_tarde_{data_str}"] = fina_tarde_vendida

    # Para garantir, inicializa se não existir (caso seja rerun após exclusão)
    for chave, valor_padrao in [
        (f"g_manha_{data_str}", 0),
        (f"g_tarde_{data_str}", 0),
        (f"f_manha_{data_str}", fina_manha_vendida),
        (f"f_tarde_{data_str}", fina_tarde_vendida),
    ]:
        if chave not in st.session_state:
            st.session_state[chave] = valor_padrao

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
            id_telas, data_str_reg, semana_reg, g_m, g_t, f_m, f_t = r
            with st.expander(f"📄 Registro - {data_str_reg} (Semana {semana_reg})", expanded=True):
                nova_grossa_manha = st.number_input(f"Telas Grossa (Manhã)", min_value=0, value=g_m, key=f"g_m_{id_telas}")
                nova_grossa_tarde = st.number_input(f"Telas Grossa (Tarde)", min_value=0, value=g_t, key=f"g_t_{id_telas}") if not desativar_tarde else 0
                nova_fina_manha = st.number_input(f"Telas Fina (Manhã)", min_value=0, value=f_m, key=f"f_m_{id_telas}")
                nova_fina_tarde = st.number_input(f"Telas Fina (Tarde)", min_value=0, value=f_t, key=f"f_t_{id_telas}") if not desativar_tarde else 0

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
        telas_grossa_manha = st.number_input("📌 Telas Grossa - Manhã", min_value=0, step=1, value=st.session_state[f"g_manha_{data_str}"], key=f"g_manha_{data_str}")
        telas_grossa_tarde = st.number_input("📌 Telas Grossa - Tarde", min_value=0, step=1, value=st.session_state[f"g_tarde_{data_str}"], key=f"g_tarde_{data_str}") if not desativar_tarde else 0
        telas_fina_manha = st.number_input("📌 Telas Fina - Manhã", min_value=0, step=1, value=st.session_state[f"f_manha_{data_str}"], key=f"f_manha_{data_str}")
        telas_fina_tarde = st.number_input("📌 Telas Fina - Tarde", min_value=0, step=1, value=st.session_state[f"f_tarde_{data_str}"], key=f"f_tarde_{data_str}") if not desativar_tarde else 0

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

def mostrar_historico_para_datas(conn, datas):
    cursor = conn.cursor()

    for data_input in datas:
        sql = """
            SELECT 
                t.id_telas,
                t.data,
                t.semana,
                t.telas_grossa_manha,
                t.telas_grossa_tarde,
                t.telas_fina_manha,
                t.telas_fina_tarde,
                h.tipo_pao,
                h.turno,
                h.horario,
                h.quantidade_vendida
            FROM telas t
            LEFT JOIN horarios h ON t.id_telas = h.id_telas
            WHERE t.data = %s
        """
        cursor.execute(sql, (data_input,))
        resultados = cursor.fetchall()

        if not resultados:
            st.warning(f"❌ Nenhum dado encontrado para a data {data_input}.")
            continue

        primeira = resultados[0]
        data_ref = pd.to_datetime(primeira[1])
        st.markdown(f"### 🗓️ Resumo do dia {primeira[1]} - Semana {primeira[2]}")

        is_domingo = data_ref.weekday() == 6
        is_feriado_flag = is_feriado(data_ref.date())

        if is_domingo:
            st.info("📌 **DOMINGO**, funcionamento apenas no turno da manhã.")
        elif is_feriado_flag:
            st.info("📌 Foi **FERIADO**, funcionamento apenas no turno da manhã.")

        colocadas_dict = {
            ("grossa", "manha"): primeira[3],
            ("grossa", "tarde"): primeira[4],
            ("fina", "manha"): primeira[5],
            ("fina", "tarde"): primeira[6]
        }

        horarios_map = {}
        for row in resultados:
            tipo = row[7]
            turno = row[8]
            horario = extrair_hora_valida(row[9])
            vendida = row[10]
            if tipo and turno:
                horarios_map[(tipo, turno)] = {
                    "horario": horario.strftime("%H:%M") if horario else "-",
                    "vendida": vendida
                }

        ordem_fixa = [
            ("grossa", "manha"),
            ("grossa", "tarde"),
            ("fina", "manha"),
            ("fina", "tarde")
        ]

        dados = []
        for tipo, turno in ordem_fixa:
            if (is_domingo or is_feriado_flag) and turno == "tarde":
                continue

            colocado = colocadas_dict.get((tipo, turno), None)
            horario = horarios_map.get((tipo, turno), {}).get("horario", "-")
            vendida = horarios_map.get((tipo, turno), {}).get("vendida", None)

            dados.append({
                "🧆 Colocadas": colocado,
                "Tipo de Pão": tipo.capitalize(),
                "Turno": turno.capitalize(),
                "⏱️ Horário": horario,
                "🛒 Vendidas": vendida if vendida is not None else "-"
            })

        df = pd.DataFrame(dados)[["🧆 Colocadas", "Tipo de Pão", "Turno", "⏱️ Horário", "🛒 Vendidas"]]
        st.dataframe(df, use_container_width=True)
        st.markdown("---")

    cursor.close()

def is_feriado(data):
    return False  # Substitua com lógica real se quiser
