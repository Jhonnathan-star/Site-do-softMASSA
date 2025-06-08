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

    id_telas, telas_grossa_manha, telas_grossa_tarde, telas_fina_manha, telas_fina_tarde = resultado
    st.success(f"✅ Data encontrada: {data_str} (ID: {id_telas})")

    turno_selecionado = st.radio("🕓 Selecione o turno para edição", ["manha", "tarde"])

    # Busca registros em horarios só do turno selecionado
    cursor.execute("""
        SELECT id, tipo_pao, turno, horario, sobra, quantidade_vendida
        FROM horarios
        WHERE id_telas = %s AND turno = %s
        ORDER BY tipo_pao
    """, (id_telas, turno_selecionado))
    registros = cursor.fetchall()

    if registros:
        st.subheader(f"📝 Editar Horários - Turno da {turno_selecionado.capitalize()}")
        novos_valores = {}

        for reg in registros:
            id_horario, tipo_pao, turno, horario, sobra, qtd_vendida = reg

            # Corrige horário se for timedelta
            if horario and isinstance(horario, timedelta):
                horario = timedelta_para_time(horario)

            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                hora_formatada = horario.strftime("%H:%M") if horario else ""
                nova_hora = st.text_input(
                    f"{tipo_pao.capitalize()} - Horário (HH:MM)",
                    value=hora_formatada,
                    key=f"hora_{id_horario}"
                )

            with col2:
                nova_sobra = st.number_input(
                    f"Sobra ({tipo_pao.capitalize()})",
                    min_value=0,
                    value=sobra if sobra is not None else 0,
                    step=1,
                    key=f"sobra_{id_horario}"
                )

            with col3:
                st.markdown(f"**Vendidos:** {qtd_vendida}")

            novos_valores[id_horario] = {
                "tipo_pao": tipo_pao,
                "nova_hora": nova_hora,
                "nova_sobra": nova_sobra,
                "original_hora": horario,
                "original_sobra": sobra,
                "qtd_vendida": qtd_vendida
            }

        if st.button("💾 Salvar alterações"):
            erros = []
            atualizados = 0
            for id_horario, dados in novos_valores.items():
                try:
                    tipo_pao = dados["tipo_pao"]
                    hora_atual = dados["original_hora"]
                    sobra_atual = dados["original_sobra"]
                    nova_hora_str = dados["nova_hora"]
                    nova_sobra = dados["nova_sobra"]
                    qtd_vendida = dados["qtd_vendida"]

                    hora_formatada = hora_atual.strftime("%H:%M") if hora_atual else ""
                    houve_alteracao_hora = nova_hora_str.strip() != hora_formatada
                    houve_alteracao_sobra = nova_sobra != sobra_atual

                    if not (houve_alteracao_hora or houve_alteracao_sobra):
                        continue

                    if nova_hora_str.strip() == "":
                        horario_sql = None
                    else:
                        horario_sql = datetime.strptime(nova_hora_str, "%H:%M").time()

                    # Atualiza tabela horarios
                    cursor.execute("""
                        UPDATE horarios
                        SET horario = %s, sobra = %s
                        WHERE id = %s
                    """, (horario_sql, nova_sobra, id_horario))

                    # Atualiza quantidade vendida conforme sobra alterada
                    if houve_alteracao_sobra:
                        diferenca_sobra = nova_sobra - (sobra_atual or 0)
                        nova_qtd_vendida = max(qtd_vendida - diferenca_sobra, 0)
                        cursor.execute("""
                            UPDATE horarios
                            SET quantidade_vendida = %s
                            WHERE id = %s
                        """, (nova_qtd_vendida, id_horario))
                    else:
                        nova_qtd_vendida = qtd_vendida

                    # Atualiza ou insere em telas_vendidas3
                    coluna = f"telas_{tipo_pao}_{turno_selecionado}"
                    cursor.execute("SELECT COUNT(*) FROM telas_vendidas3 WHERE id_telas = %s", (id_telas,))
                    existe = cursor.fetchone()[0]

                    if existe:
                        cursor.execute(f"""
                            UPDATE telas_vendidas3 SET {coluna} = %s WHERE id_telas = %s
                        """, (nova_qtd_vendida, id_telas))
                    else:
                        # Para inserir, precisamos dos dados de data e semana de 'telas'
                        cursor.execute("SELECT data, semana FROM telas WHERE id_telas = %s", (id_telas,))
                        res = cursor.fetchone()
                        data_telas, semana_telas = res if res else (None, None)

                        cursor.execute(f"""
                            INSERT INTO telas_vendidas3 (id_telas, {coluna}, data, semana)
                            VALUES (%s, %s, %s, %s)
                        """, (id_telas, nova_qtd_vendida, data_telas, semana_telas))

                    atualizados += 1
                except Exception as e:
                    erros.append(f"Erro no ID {id_horario}: {str(e)}")

            conn.commit()

            if erros:
                st.error("⚠️ Alguns erros ocorreram:")
                for e in erros:
                    st.write(e)
            elif atualizados > 0:
                st.success(f"✅ {atualizados} registros atualizados com sucesso!")
            else:
                st.info("🔄 Nenhuma alteração detectada.")

    else:
        st.subheader(f"🆕 Inserir Horários - Turno da {turno_selecionado.capitalize()}")

        paes = []
        if turno_selecionado == "manha":
            paes = [("grossa", telas_grossa_manha), ("fina", telas_fina_manha)]
        else:
            paes = [("grossa", telas_grossa_tarde), ("fina", telas_fina_tarde)]

        novos_dados = {}
        for tipo_pao, total in paes:
            col1, col2 = st.columns(2)

            with col1:
                nova_hora = st.text_input(
                    f"🕒 Horário ({tipo_pao.capitalize()} - {turno_selecionado}) (HH:MM)",
                    value="",
                    placeholder="HH:MM",
                    key=f"novo_hora_{tipo_pao}"
                )
            with col2:
                nova_sobra = st.number_input(
                    f"🥖 Sobra ({tipo_pao.capitalize()} - {turno_selecionado})",
                    min_value=0,
                    value=0,
                    step=1,
                    key=f"novo_sobra_{tipo_pao}"
                )
            novos_dados[tipo_pao] = {
                "hora": nova_hora.strip(),
                "sobra": nova_sobra,
                "total": total
            }

        if st.button("💾 Enviar para o banco"):
            erros = []
            inseridos = 0
            for tipo_pao, dados in novos_dados.items():
                try:
                    if dados["hora"] == "":
                        horario_sql = None
                    else:
                        try:
                            horario_sql = datetime.strptime(dados["hora"], "%H:%M").time()
                        except ValueError:
                            st.error(f"❌ Horário inválido para {tipo_pao} - {turno_selecionado}. Use formato HH:MM.")
                            continue

                    sobra = dados["sobra"]
                    total = dados["total"]
                    quantidade_vendida = max(total - sobra, 0)

                    # Inserção em horarios
                    cursor.execute("""
                        INSERT INTO horarios (id_telas, tipo_pao, turno, horario, sobra, quantidade_vendida)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (id_telas, tipo_pao, turno_selecionado, horario_sql, sobra, quantidade_vendida))

                    # Atualização automática em telas_vendidas3
                    coluna = f"telas_{tipo_pao}_{turno_selecionado}"
                    cursor.execute("SELECT data, semana FROM telas WHERE id_telas = %s", (id_telas,))
                    res = cursor.fetchone()
                    data_telas, semana_telas = res if res else (None, None)

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
                        """, (id_telas, quantidade_vendida, data_telas, semana_telas))

                    inseridos += 1
                except Exception as e:
                    erros.append(f"Erro ao inserir {tipo_pao}: {str(e)}")

            conn.commit()

            if erros:
                st.error("⚠️ Alguns erros ocorreram ao inserir dados:")
                for e in erros:
                    st.write(e)
            elif inseridos > 0:
                st.success(f"✅ {inseridos} registros inseridos com sucesso!")
            else:
                st.info("ℹ️ Nenhum dado enviado (campos vazios ou inválidos).")
