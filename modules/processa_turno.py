import streamlit as st
from datetime import datetime, time, timedelta
import pandas as pd

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

def buscar_historico_por_data(conn):
    st.header("📊 Histórico de Produção e Vendas")

    modo = st.radio("🔍 Como deseja consultar?", ["Ver por data específica", "Consulta por intervalo de datas"])

    if modo == "Ver por data específica":
        data_input = st.date_input("Selecione a data:", format="YYYY-MM-DD")

        if st.button("Buscar"):
            mostrar_historico_para_datas(conn, [data_input])

    elif modo == "Consulta por intervalo de datas":
        col1, col2 = st.columns(2)
        with col1:
            data_ini = st.date_input("🗕️ Data inicial", format="YYYY-MM-DD")
        with col2:
            data_fim = st.date_input("🗕️ Data final", format="YYYY-MM-DD")

        if st.button("Buscar intervalo"):
            if data_ini > data_fim:
                st.error("⚠️ Data inicial deve ser anterior à final.")
            else:
                datas = pd.date_range(start=data_ini, end=data_fim).to_list()
                mostrar_historico_para_datas(conn, datas)

def is_feriado(data):
    return False

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

        # Verifica se é domingo ou feriado
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
            # Pula os turnos da tarde se for domingo ou feriado
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


def inserir_horarios_separados_front(conn):
    st.title("Registro de Horários dos Pães")

    data = st.date_input("📅 Selecione a data para registrar os horários")
    if not data:
        return

    data_str = data.strftime('%Y-%m-%d')
    dia_semana = data.weekday()  # 6 = domingo
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

    id_telas, grossa_manha, grossa_tarde, fina_manha, fina_tarde = resultado
    st.success(f"✅ Data encontrada: {data_str} (ID: {id_telas})")

    turno = st.radio("🕒 Selecione o turno", ["manha", "tarde"])
    valor_grossa = grossa_manha if turno == "manha" else grossa_tarde
    valor_fina = fina_manha if turno == "manha" else fina_tarde

    feriado = False
    if turno == "manha":
        feriado = st.checkbox("📌 Marque aqui se hoje for feriado")

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
    st.subheader(f"{'📍 Editar' if editando else '🆕 Inserir'} Horários - Turno da {turno}")

    for tipo in tipos_pao:
        reg = next((r for r in registros if r[1] == tipo), None)
        st.markdown(f"#### {tipo.capitalize()}")

        if reg:
            id_horario, _, _, horario, sobra, qtd_vendida, colocadas = reg
            col1, col2 = st.columns([3, 2])
            horario_validado = extrair_hora_valida(horario)
            with col1:
                hora_input = st.text_input(
                    f"⏱️ Horário ({tipo})",
                    value=horario_validado.strftime("%H:%M") if horario_validado else "",
                    key=f"{tipo}_hora"
                )
            with col2:
                sobra_input = st.number_input(f"🥖 Sobra ({tipo})", min_value=0, value=sobra or 0, key=f"{tipo}_sobra")

            colocadas_input = st.number_input(
                f"🧺 Telas Colocadas ({tipo})", min_value=0, value=colocadas or 0, key=f"{tipo}_colocadas"
            ) if tipo == "fina" else None
            valores[tipo] = {
                "id_horario": id_horario,
                "hora": hora_input.strip(),
                "sobra": sobra_input,
                "colocadas": colocadas_input
            }
        else:
            col1, col2 = st.columns([3, 2])
            with col1:
                hora_input = st.text_input(f"⏱️ Horário ({tipo})", key=f"novo_{tipo}_hora")
            with col2:
                sobra_input = st.number_input(f"🥖 Sobra ({tipo})", min_value=0, key=f"novo_{tipo}_sobra")

            colocadas_input = st.number_input(
                f"🧺 Telas Colocadas ({tipo})", min_value=0, key=f"novo_{tipo}_colocadas"
            ) if tipo == "fina" else None
            valores[tipo] = {
                "id_horario": None,
                "hora": hora_input.strip(),
                "sobra": sobra_input,
                "colocadas": colocadas_input
            }

    if st.button("💾 Salvar" if not editando else "💾 Salvar Alterações"):
        atualizados, inseridos, erros = 0, 0, []

        for tipo, dados in valores.items():
            try:
                hora = datetime.strptime(dados["hora"], "%H:%M").time() if dados["hora"] else None
                sobra = dados["sobra"]
                colocadas = dados["colocadas"] if tipo == "fina" else None

                quantidade_base = valor_fina if tipo == "fina" else valor_grossa
                quantidade_vendida = max(quantidade_base - sobra, 0)

                if dados["id_horario"]:
                    cursor.execute("""
                        UPDATE horarios 
                        SET horario = %s, sobra = %s, quantidade_vendida = %s, telas_colocadas = %s
                        WHERE id = %s
                    """, (hora, sobra, quantidade_vendida, colocadas, dados["id_horario"]))
                    atualizados += 1
                else:
                    cursor.execute("""
                        INSERT INTO horarios (id_telas, tipo_pao, turno, horario, sobra, quantidade_vendida, telas_colocadas)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (id_telas, tipo, turno, hora, sobra, quantidade_vendida, colocadas))
                    inseridos += 1

                coluna_vendida = f"telas_{tipo}_{turno}"
                cursor.execute("SELECT COUNT(*) FROM telas_vendidas3 WHERE id_telas = %s", (id_telas,))
                existe = cursor.fetchone()[0]

                if existe:
                    cursor.execute(f"""
                        UPDATE telas_vendidas3 SET {coluna_vendida} = %s WHERE id_telas = %s
                    """, (quantidade_vendida, id_telas))
                else:
                    cursor.execute("SELECT data, semana FROM telas WHERE id_telas = %s", (id_telas,))
                    data_telas, semana = cursor.fetchone()
                    valores_iniciais = {
                        f"telas_grossa_manha": 0, f"telas_grossa_tarde": 0,
                        f"telas_fina_manha": 0, f"telas_fina_tarde": 0
                    }
                    valores_iniciais[coluna_vendida] = quantidade_vendida

                    if dia_semana == 6 and turno == "manha":
                        valores_iniciais[f"telas_grossa_tarde"] = 0
                        valores_iniciais[f"telas_fina_tarde"] = 0

                    cursor.execute(f"""
                        INSERT INTO telas_vendidas3 (id_telas, telas_grossa_manha, telas_grossa_tarde,
                            telas_fina_manha, telas_fina_tarde, data, semana)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (id_telas, valores_iniciais['telas_grossa_manha'], valores_iniciais['telas_grossa_tarde'],
                          valores_iniciais['telas_fina_manha'], valores_iniciais['telas_fina_tarde'],
                          data_telas, semana))

                if tipo == "fina":
                    total_telas = colocadas + sobra
                    if (turno == "manha") and (dia_semana == 6 or feriado):
                        cursor.execute("SELECT data FROM telas WHERE id_telas = %s", (id_telas,))
                        data_atual = cursor.fetchone()[0]
                        dia_seguinte = data_atual + timedelta(days=1)
                        cursor.execute("""
                            UPDATE telas SET telas_fina_manha = %s WHERE data = %s
                        """, (total_telas, dia_seguinte))
                    elif turno == "manha":
                        cursor.execute("""
                            UPDATE telas SET telas_fina_tarde = %s WHERE id_telas = %s
                        """, (total_telas, id_telas))
                    elif turno == "tarde":
                        cursor.execute("SELECT data FROM telas WHERE id_telas = %s", (id_telas,))
                        data_atual = cursor.fetchone()[0]
                        dia_seguinte = data_atual + timedelta(days=1)
                        cursor.execute("""
                            UPDATE telas SET telas_fina_manha = %s WHERE data = %s
                        """, (total_telas, dia_seguinte))

            except Exception as e:
                erros.append(f"{tipo}: {e}")

        conn.commit()

        if erros:
            st.error("⚠️ Erros encontrados:")
            for e in erros:
                st.write(e)
        else:
            st.success(f"✅ {atualizados} atualizados, {inseridos} inseridos com sucesso!")