import pandas as pd
from datetime import timedelta
import streamlit as st
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.exceptions import ConvergenceWarning
import warnings

# Suprimir os avisos de convergência
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# Função para treinar o modelo
def treinar_modelo(df, coluna, impacto_clima):
    df_filtrado = df[[coluna, 'dia_semana', impacto_clima]].dropna()

    X = df_filtrado[['dia_semana', impacto_clima]]
    y = df_filtrado[coluna]

    preprocessor = ColumnTransformer(transformers=[
        ('cat', OneHotEncoder(drop='first'), ['dia_semana']),
        ('num', StandardScaler(), [impacto_clima])
    ])

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', GridSearchCV(
            estimator=MLPRegressor(max_iter=3000, random_state=42),
            param_grid={
                'hidden_layer_sizes': [(50,), (100,), (50, 50)],
                'alpha': [0.0001, 0.001]
            },
            scoring='r2',
            cv=5,
            n_jobs=-1,
            verbose=0
        ))
    ])

    pipeline.fit(X, y)
    return pipeline

# Função principal
def criar_predicao_semana(conn):
    if "previsoes" in st.session_state and st.session_state.previsoes is not None:
        df_previsoes = st.session_state.previsoes
    else:
        # Coleta dados da tabela telas_vendidas3
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT data, semana, telas_grossa_manha, telas_grossa_tarde, telas_fina_manha, telas_fina_tarde
            FROM telas_vendidas3
            WHERE telas_grossa_manha IS NOT NULL
        """)
        dados = cursor.fetchall()
        cursor.close()

        df = pd.DataFrame(dados)
        df['data'] = pd.to_datetime(df['data'])
        df['dia_semana'] = df['data'].dt.day_name()

        # Criar colunas de impacto climático
        df['impacto_clima_grossa'] = df['telas_grossa_manha'] - df['telas_grossa_tarde']
        df['impacto_clima_fina'] = df['telas_fina_manha'] - df['telas_fina_tarde']

        st.write("### ⏳ Treinando modelos de previsão...")

        with st.spinner("Treinando modelos, aguarde..."):
            modelos = {
                'telas_grossa_manha': treinar_modelo(df, 'telas_grossa_manha', 'impacto_clima_grossa'),
                'telas_grossa_tarde': treinar_modelo(df, 'telas_grossa_tarde', 'impacto_clima_grossa'),
                'telas_fina_manha': treinar_modelo(df, 'telas_fina_manha', 'impacto_clima_fina'),
                'telas_fina_tarde': treinar_modelo(df, 'telas_fina_tarde', 'impacto_clima_fina'),
            }

        # Obter a última data da tabela telas
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(data) FROM telas")
        ultima_data_telas = cursor.fetchone()[0]
        cursor.close()

        if ultima_data_telas:
            ultima_data_telas = pd.to_datetime(ultima_data_telas)

        # Obter a última data da tabela telas_vendidas3
        ultima_data_vendidas = df['data'].max()

        # Usar a mais recente entre as duas
        if ultima_data_telas and ultima_data_telas > ultima_data_vendidas:
            ultima_data = ultima_data_telas
        else:
            ultima_data = ultima_data_vendidas

        previsoes = []

        for i in range(1, 8):
            data_futura = ultima_data + timedelta(days=i)
            dia = data_futura.day_name()

            impacto_clima_grossa = df['impacto_clima_grossa'].mean()
            impacto_clima_fina = df['impacto_clima_fina'].mean()

            df_pred_grossa = pd.DataFrame([[dia, impacto_clima_grossa]], columns=['dia_semana', 'impacto_clima_grossa'])
            df_pred_fina = pd.DataFrame([[dia, impacto_clima_fina]], columns=['dia_semana', 'impacto_clima_fina'])

            previsao_dia = {
                'data': data_futura.strftime('%Y-%m-%d'),
                'semana': dia,
                'telas_grossa_manha': round(modelos['telas_grossa_manha'].predict(df_pred_grossa)[0]),
                'telas_grossa_tarde': round(modelos['telas_grossa_tarde'].predict(df_pred_grossa)[0]) if dia != 'Sunday' else 0,
                'telas_fina_manha': round(modelos['telas_fina_manha'].predict(df_pred_fina)[0]),
                'telas_fina_tarde': round(modelos['telas_fina_tarde'].predict(df_pred_fina)[0]) if dia != 'Sunday' else 0,
            }

            previsoes.append(previsao_dia)

        df_previsoes = pd.DataFrame(previsoes)
        df_previsoes.set_index('data', inplace=True)
        st.session_state.previsoes = df_previsoes

    st.write("### 📊 Previsões para a próxima semana (edite se quiser):")
    edited_df = st.data_editor(st.session_state.previsoes, num_rows="dynamic")
    st.session_state.previsoes = edited_df

    if st.button("📤 Inserir previsões no banco de dados"):
        cursor = conn.cursor()
        for idx, row in edited_df.iterrows():
            query = """
                INSERT INTO telas (data, semana, telas_grossa_manha, telas_grossa_tarde, telas_fina_manha, telas_fina_tarde)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    semana=VALUES(semana),
                    telas_grossa_manha=VALUES(telas_grossa_manha),
                    telas_grossa_tarde=VALUES(telas_grossa_tarde),
                    telas_fina_manha=VALUES(telas_fina_manha),
                    telas_fina_tarde=VALUES(telas_fina_tarde)
            """
            cursor.execute(query, (
                idx, row['semana'], int(row['telas_grossa_manha']), int(row['telas_grossa_tarde']),
                int(row['telas_fina_manha']), int(row['telas_fina_tarde'])
            ))
        conn.commit()
        cursor.close()
        st.success("✅ Previsões inseridas/atualizadas com sucesso no banco de dados!")
    