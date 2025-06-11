import streamlit as st
from datetime import datetime, time
from mysql.connector import Error

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

import streamlit as st
from datetime import datetime, time, timedelta

def extrair_hora_valida(horario):
    if horario is None:
        return None
    if isinstance(horario, time):
        return horario
    if isinstance(horario, timedelta):
        total_segundos = int(horario.total_seconds())
        horas = total_segundos // 3600
        minutos = (total_segundos % 3600) // 60
        segundos = total_segundos % 60
        return time(horas, minutos, segundos)
    try:
        return datetime.strptime(str(horario), "%H:%M:%S").time()
    except:
        return None

import streamlit as st
from datetime import datetime, time, timedelta

def timedelta_para_time(td):
    total_segundos = int(td.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60
    return time(horas, minutos, segundos)

def inserir_horarios_separados_front(conn):
    st.title("Registro de Horários dos Pães")

    data = st.date_input("📅 Selecione a data para registrar os horários")
    if not data:
        return

    data_str = data.strftime('%Y-%m-%d')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_telas, telas_grossa_manha, telas_grossa_tarde, 
               telas_fina_manha, telas_fina_tarde 
        FROM telas WHERE data = %s
    """, (data_str,))
    resultado = cursor.fetchone()

    if not resultado:
        st.error(f"❌ Nenhuma entrada na tabela 'telas' para a data {data_str}.")
        return

    id_telas, *_ = resultado
    st.success(f"✅ Data encontrada: {data_str} (ID: {id_telas})")

    turno = st.radio("🕒 Selecione o turno", ["manha", "tarde"])

    cursor.execute("""
        SELECT id, tipo_pao, turno, horario, sobra, quantidade_vendida, telas_colocadas
        FROM horarios
        WHERE id_telas = %s AND turno = %s
        ORDER BY tipo_pao
    """, (id_telas, turno))
    registros = cursor.fetchall()

    tipos_pao = ["grossa", "fina"]
    valores = {}

    editando = bool(registros)
    if editando:
        st.subheader(f"📝 Editar Horários - Turno da {turno}")
    else:
        st.subheader(f"🆕 Inserir Horários - Turno da {turno}")

    for tipo in tipos_pao:
        reg = next((r for r in registros if r[1] == tipo), None)
        st.markdown(f"#### {tipo.capitalize()}")

        if reg:
            id_horario, _, _, horario, sobra, qtd_vendida, colocadas = reg
            
            # Converter timedelta para time se necessário
            if isinstance(horario, timedelta):
                horario = timedelta_para_time(horario)

            col1, col2 = st.columns([3, 2])

            with col1:
                hora_input = st.text_input(f"⏱️ Horário ({tipo})", value=horario.strftime("%H:%M") if horario else "", key=f"{tipo}_hora")
            with col2:
                sobra_input = st.number_input(f"🥖 Sobra ({tipo})", min_value=0, value=sobra or 0, key=f"{tipo}_sobra")

            colocadas_input = None
            if tipo == "fina":
                colocadas_input = st.number_input(f"🧺 Telas Colocadas ({tipo})", min_value=0, value=colocadas or 0, key=f"{tipo}_colocadas")

            valores[tipo] = {
                "id_horario": id_horario,
                "hora": hora_input.strip(),
                "sobra": sobra_input,
                "colocadas": colocadas_input,
                "qtd_vendida": qtd_vendida
            }

        else:
            col1, col2 = st.columns([3, 2])

            with col1:
                hora_input = st.text_input(f"⏱️ Horário ({tipo})", key=f"novo_{tipo}_hora")
            with col2:
                sobra_input = st.number_input(f"🥖 Sobra ({tipo})", min_value=0, key=f"novo_{tipo}_sobra")

            colocadas_input = None
            if tipo == "fina":
                colocadas_input = st.number_input(f"🧺 Telas Colocadas ({tipo})", min_value=0, key=f"novo_{tipo}_colocadas")

            valores[tipo] = {
                "id_horario": None,
                "hora": hora_input.strip(),
                "sobra": sobra_input,
                "colocadas": colocadas_input
            }

    botao_label = "💾 Salvar Alterações" if editando else "💾 Salvar"
    if st.button(botao_label):
        atualizados, inseridos, erros = 0, 0, []

        for tipo, dados in valores.items():
            try:
                hora = datetime.strptime(dados["hora"], "%H:%M").time() if dados["hora"] else None
                sobra = dados["sobra"]

                if tipo == "fina":
                    colocadas = dados["colocadas"]
                    vendidas = max(colocadas - sobra, 0) if colocadas is not None else None
                else:
                    colocadas = None
                    vendidas = None

                if dados["id_horario"]:
                    cursor.execute("""
                        UPDATE horarios 
                        SET horario = %s, sobra = %s, quantidade_vendida = %s, telas_colocadas = %s
                        WHERE id = %s
                    """, (hora, sobra, vendidas, colocadas, dados["id_horario"]))
                    atualizados += 1
                else:
                    cursor.execute("""
                        INSERT INTO horarios (id_telas, tipo_pao, turno, horario, sobra, quantidade_vendida, telas_colocadas)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (id_telas, tipo, turno, hora, sobra, vendidas, colocadas))
                    inseridos += 1

                if tipo == "fina":
                    coluna_vendida = f"telas_{tipo}_{turno}"
                    cursor.execute("SELECT COUNT(*) FROM telas_vendidas3 WHERE id_telas = %s", (id_telas,))
                    existe = cursor.fetchone()[0]

                    if existe:
                        cursor.execute(f"""
                            UPDATE telas_vendidas3 SET {coluna_vendida} = %s WHERE id_telas = %s
                        """, (vendidas, id_telas))
                    else:
                        cursor.execute("SELECT data, semana FROM telas WHERE id_telas = %s", (id_telas,))
                        data_telas, semana = cursor.fetchone()
                        cursor.execute(f"""
                            INSERT INTO telas_vendidas3 (id_telas, {coluna_vendida}, data, semana)
                            VALUES (%s, %s, %s, %s)
                        """, (id_telas, vendidas, data_telas, semana))

                    campo_fina = f"telas_fina_{turno}"
                    cursor.execute(f"""
                        UPDATE telas SET {campo_fina} = %s WHERE id_telas = %s
                    """, (colocadas, id_telas))

            except Exception as e:
                erros.append(f"{tipo}: {e}")

        conn.commit()

        if erros:
            st.error("⚠️ Erros encontrados:")
            for e in erros:
                st.write(e)
        else:
            st.success(f"✅ {atualizados} atualizados, {inseridos} inseridos com sucesso!")
