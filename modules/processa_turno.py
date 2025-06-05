import streamlit as st
from datetime import datetime

def processa_turno_front(conn, id_telas,
                         telas_grossa_manha, telas_grossa_tarde,
                         telas_fina_manha, telas_fina_tarde,
                         domingo_ou_feriado):

    cursor = conn.cursor()

    paes = [
        ('grossa', 'manha', telas_grossa_manha),
        ('grossa', 'tarde', telas_grossa_tarde),
        ('fina', 'manha', telas_fina_manha),
        ('fina', 'tarde', telas_fina_tarde),
    ]

    if "dados_telas" not in st.session_state:
        st.session_state.dados_telas = {}

    for tipo_pao, turno, total_telas in paes:
        if domingo_ou_feriado and turno == 'tarde':
            continue

        st.subheader(f"{tipo_pao.capitalize()} - Turno da {turno}")

        key_prefix = f"{tipo_pao}_{turno}"

        # Carrega os valores atuais ou define padrões
        dados = st.session_state.dados_telas.get(key_prefix, {
            "tipo_pao": tipo_pao,
            "turno": turno,
            "horario": None,
            "sobra": 0,
            "total_telas": total_telas
        })

        # Campos da interface
        if tipo_pao == 'grossa':
            acabou = st.radio(
                f"Acabou todo o pão {tipo_pao} no turno da {turno}?",
                ["Sim", "Não"],
                index=0 if dados.get("horario") else 1,
                key=f"{key_prefix}_acabou"
            )
            if acabou == "Sim":
                horario = st.time_input(
                    f"Que horas acabou o {tipo_pao} ({turno})?",
                    value=dados.get("horario") or None,
                    key=f"{key_prefix}_horario"
                )
                sobra = 0
            else:
                sobra = st.number_input(
                    f"Quantas telas sobraram do {tipo_pao} ({turno})?",
                    min_value=0,
                    value=dados.get("sobra") or 0,
                    key=f"{key_prefix}_sobra"
                )
                horario = None
        else:
            sobrou = st.radio(
                f"Sobrou alguma tela de {tipo_pao} no turno da {turno}?",
                ["Sim", "Não"],
                index=0 if dados.get("sobra") > 0 else 1,
                key=f"{key_prefix}_sobrou"
            )
            if sobrou == "Sim":
                sobra = st.number_input(
                    f"Quantas telas sobraram do {tipo_pao} ({turno})?",
                    min_value=0,
                    value=dados.get("sobra") or 0,
                    key=f"{key_prefix}_sobra"
                )
                horario = None
            else:
                horario = st.time_input(
                    f"Que horas acabou o {tipo_pao} ({turno})?",
                    value=dados.get("horario") or None,
                    key=f"{key_prefix}_horario"
                )
                sobra = 0

        # Atualiza dados
        dados["horario"] = horario
        dados["sobra"] = sobra
        dados["total_telas"] = total_telas
        st.session_state.dados_telas[key_prefix] = dados

    # Botão final para salvar
    if st.button("✅ Salvar todos os dados"):
        try:
            for dados in st.session_state.dados_telas.values():
                tipo_pao = dados["tipo_pao"]
                turno = dados["turno"]
                horario = dados["horario"]
                sobra = dados["sobra"]
                total_telas = dados["total_telas"]
                quantidade_vendida = total_telas - sobra

                cursor.execute("SELECT data, semana FROM telas WHERE id_telas = %s", (id_telas,))
                resultado = cursor.fetchone()
                data, dia_semana = resultado if resultado else (None, None)

                cursor.execute("""
                    INSERT INTO horarios (id_telas, tipo_pao, turno, horario, quantidade_vendida)
                    VALUES (%s, %s, %s, %s, %s)
                """, (id_telas, tipo_pao, turno, str(horario) if horario else None, quantidade_vendida))

                coluna = f"telas_{tipo_pao}_{turno}"
                colunas_validas = ['telas_grossa_manha', 'telas_grossa_tarde', 'telas_fina_manha', 'telas_fina_tarde']
                if coluna in colunas_validas:
                    cursor.execute("SELECT COUNT(*) FROM telas_vendidas3 WHERE id_telas = %s", (id_telas,))
                    existe = cursor.fetchone()[0]
                    if existe:
                        cursor.execute(f"""
                            UPDATE telas_vendidas3 SET {coluna} = %s WHERE id_telas = %s
                        """, (quantidade_vendida, id_telas))
                    else:
                        cursor.execute(f"""
                            INSERT INTO telas_vendidas3 (id_telas, {coluna}, data, semana)
                            VALUES (%s, %s, %s, %s)
                        """, (id_telas, quantidade_vendida, data, dia_semana))

            conn.commit()
            st.success("✅ Todos os dados foram salvos com sucesso!")
            del st.session_state.dados_telas

        except Exception as e:
            st.error(f"❌ Erro ao salvar os dados: {e}")

def inserir_horarios_separados_front(conn):
    st.title("Registro de Horários dos Pães")

    data = st.date_input("📅 Selecione a data para registrar os horários")

    if data:
        data_str = data.strftime('%Y-%m-%d')

        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_telas, telas_grossa_manha, telas_grossa_tarde, 
                   telas_fina_manha, telas_fina_tarde 
            FROM telas WHERE data = %s
        """, (data_str,))
        resultado = cursor.fetchone()

        if resultado:
            id_telas, telas_grossa_manha, telas_grossa_tarde, telas_fina_manha, telas_fina_tarde = resultado
            st.success(f"✅ Data encontrada: {data_str} (ID: {id_telas})")

            dia_da_semana = data.weekday()
            domingo_ou_feriado = (dia_da_semana == 6)

            if domingo_ou_feriado:
                st.info("🕒 É domingo: apenas turnos da manhã serão registrados.")
            else:
                st.info("🕒 Registrando turnos da manhã e da tarde.")

            processa_turno_front(
                conn,
                id_telas,
                telas_grossa_manha, telas_grossa_tarde,
                telas_fina_manha, telas_fina_tarde,
                domingo_ou_feriado
            )

        else:
            st.error(f"❌ Nenhuma entrada encontrada na tabela 'telas' para a data {data_str}.")

import streamlit as st

def buscar_historico_por_data(conn):
    st.header("🔎 Buscar Histórico por Data")

    data_input = st.date_input("Digite a data para buscar:", format="YYYY-MM-DD")

    if st.button("Buscar"):
        cursor = conn.cursor()
        sql = """
            SELECT 
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

        if resultados:
            st.markdown("---")
            st.markdown(f"### Resumo do dia {data_input}:\n")
            primeira_linha = resultados[0]
            st.write(f"**Data:** {primeira_linha[0]}")
            st.write(f"**Semana:** {primeira_linha[1]}")
            st.write(f"**Telas Grossa (Manhã):** {primeira_linha[2]}")
            st.write(f"**Telas Grossa (Tarde):** {primeira_linha[3]}")
            st.write(f"**Telas Fina (Manhã):** {primeira_linha[4]}")
            st.write(f"**Telas Fina (Tarde):** {primeira_linha[5]}")
            st.markdown("---")

            for row in resultados:
                tipo_pao = row[6]
                turno = row[7]
                horario = row[8]
                quantidade = row[9]

                st.write(f"**Tipo de Pão:** {tipo_pao} | **Turno:** {turno}")
                if horario:
                    st.write(f"⏰ Horário: {horario} | Vendido: {quantidade}")
                else:
                    st.write(f"Vendidos: {quantidade}")
                st.markdown("---")
        else:
            st.warning("Nenhum dado encontrado para essa data.")
        
        cursor.close()
