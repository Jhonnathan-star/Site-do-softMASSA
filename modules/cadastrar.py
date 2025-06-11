import streamlit as st
from modules.auth_utils import hash_password
from database.connection import conectar

def gerenciar_usuarios(conn):
    st.subheader("Gerenciar Usuários")
    acao = st.radio("Selecione uma ação:", ["Cadastrar novo usuário", "Alterar ou excluir usuário"])

    if acao == "Cadastrar novo usuário":
        novo_usuario = st.text_input("Novo usuário")
        nova_senha = st.text_input("Nova senha", type="password")
        confirmar_senha = st.text_input("Confirmar senha", type="password")
        tipo_usuario = st.selectbox("Tipo de usuário", ["comum", "admin"])

        if st.button("Cadastrar usuário"):
            if not novo_usuario or not nova_senha or not confirmar_senha:
                st.warning("Preencha todos os campos.")
                return

            if nova_senha != confirmar_senha:
                st.error("As senhas não coincidem.")
                return

            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = %s", (novo_usuario,))
            existe = cursor.fetchone()[0]

            if existe:
                st.error("Usuário já existe.")
            else:
                senha_hash = hash_password(nova_senha)
                cursor.execute(
                    "INSERT INTO usuarios (usuario, senha, tipo) VALUES (%s, %s, %s)",
                    (novo_usuario, senha_hash, tipo_usuario)
                )
                conn.commit()
                st.success(f"Usuário '{novo_usuario}' ({tipo_usuario}) cadastrado com sucesso!")
            cursor.close()

    elif acao == "Alterar ou excluir usuário":
        cursor = conn.cursor()
        cursor.execute("SELECT id, usuario, tipo FROM usuarios ORDER BY usuario")
        usuarios = cursor.fetchall()
        cursor.close()

        if not usuarios:
            st.info("Nenhum usuário encontrado.")
            return

        nomes_formatados = [f"{u[1]} ({u[2]})" for u in usuarios]
        usuario_escolhido = st.selectbox("Selecionar usuário", nomes_formatados)
        usuario_id, usuario_nome, usuario_tipo = usuarios[nomes_formatados.index(usuario_escolhido)]

        novo_nome = st.text_input("Novo nome de usuário", value=usuario_nome)
        nova_senha = st.text_input("Nova senha (deixe em branco para não alterar)", type="password")
        novo_tipo = st.selectbox("Tipo de usuário", ["comum", "admin"], index=0 if usuario_tipo == "comum" else 1)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Salvar alterações"):
                atualizacoes = []
                valores = []

                if novo_nome and novo_nome != usuario_nome:
                    atualizacoes.append("usuario = %s")
                    valores.append(novo_nome)

                if nova_senha:
                    senha_hash = hash_password(nova_senha)
                    atualizacoes.append("senha = %s")
                    valores.append(senha_hash)

                if novo_tipo != usuario_tipo:
                    atualizacoes.append("tipo = %s")
                    valores.append(novo_tipo)

                if atualizacoes:
                    valores.append(usuario_id)
                    query = f"UPDATE usuarios SET {', '.join(atualizacoes)} WHERE id = %s"
                    cursor = conn.cursor()
                    cursor.execute(query, tuple(valores))
                    conn.commit()
                    cursor.close()
                    st.success("Usuário atualizado com sucesso.")
                    st.rerun()
                else:
                    st.info("Nenhuma alteração feita.")

        with col2:
            if st.button("Excluir usuário"):
                if st.session_state.get("usuario_id") == usuario_id:
                    st.error("❌ Você não pode excluir o próprio usuário logado.")
                    return

                cursor = conn.cursor()
                # Verifica dependências
                cursor.execute("SELECT COUNT(*) FROM conta_funcionarios WHERE id_usuario = %s", (usuario_id,))
                vinculos = cursor.fetchone()[0]

                if vinculos > 0:
                    st.warning("⚠️ Este usuário possui dados vinculados (ex: conta_funcionarios).")
                    confirmar = st.radio(
                        "Deseja excluir mesmo assim? Isso irá apagar os dados associados.",
                        ["Não", "Sim"],
                        index=0,
                        key="confirmar_exclusao_usuario"
                    )
                    if confirmar == "Sim":
                        try:
                            cursor.execute("DELETE FROM conta_funcionarios WHERE id_usuario = %s", (usuario_id,))
                            cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
                            conn.commit()
                            st.success("✅ Usuário e dados associados excluídos com sucesso.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir: {e}")
                        finally:
                            cursor.close()
                    else:
                        st.info("Operação cancelada.")
                        cursor.close()
                else:
                    try:
                        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
                        conn.commit()
                        st.success("✅ Usuário excluído com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")
                    finally:
                        cursor.close()


