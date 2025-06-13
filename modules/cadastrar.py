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
        email_usuario = st.text_input("E-mail")

        if st.button("Cadastrar usuário"):
            if not novo_usuario or not nova_senha or not confirmar_senha or not email_usuario:
                st.warning("Preencha todos os campos.")
                return

            if nova_senha != confirmar_senha:
                st.error("As senhas não coincidem.")
                return

            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = %s", (novo_usuario,))
                existe = cursor.fetchone()[0]

                if existe:
                    st.error("Usuário já existe.")
                else:
                    senha_hash = hash_password(nova_senha)
                    cursor.execute(
                        "INSERT INTO usuarios (usuario, senha, tipo, email) VALUES (%s, %s, %s, %s)",
                        (novo_usuario, senha_hash, tipo_usuario, email_usuario)
                    )
                    conn.commit()
                    st.success(f"Usuário '{novo_usuario}' ({tipo_usuario}) cadastrado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao cadastrar usuário: {e}")
            finally:
                cursor.close()

    elif acao == "Alterar ou excluir usuário":
        cursor = conn.cursor()
        cursor.execute("SELECT id, usuario, tipo, email FROM usuarios ORDER BY usuario")
        usuarios = cursor.fetchall()
        cursor.close()

        if not usuarios:
            st.info("Nenhum usuário encontrado.")
            return

        nomes_formatados = [f"{u[1]} ({u[2]})" for u in usuarios]
        usuario_escolhido = st.selectbox("Selecionar usuário", nomes_formatados)
        usuario_id, usuario_nome, usuario_tipo, usuario_email = usuarios[nomes_formatados.index(usuario_escolhido)]

        novo_nome = st.text_input("Novo nome de usuário", value=usuario_nome)
        nova_senha = st.text_input("Nova senha (deixe em branco para não alterar)", type="password")
        novo_tipo = st.selectbox("Tipo de usuário", ["comum", "admin"], index=0 if usuario_tipo == "comum" else 1)
        novo_email = st.text_input("Novo e-mail", value=usuario_email)

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

                if novo_email != usuario_email:
                    atualizacoes.append("email = %s")
                    valores.append(novo_email)

                if atualizacoes:
                    valores.append(usuario_id)
                    try:
                        cursor = conn.cursor()
                        query = f"UPDATE usuarios SET {', '.join(atualizacoes)} WHERE id = %s"
                        cursor.execute(query, tuple(valores))
                        conn.commit()
                        st.success("Usuário atualizado com sucesso.")
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")
                    finally:
                        cursor.close()
                    st.rerun()
                else:
                    st.info("Nenhuma alteração feita.")

        with col2:
            if "confirmar_exclusao_usuario" not in st.session_state:
                st.session_state.confirmar_exclusao_usuario = False
            if "usuario_id_excluir" not in st.session_state:
                st.session_state.usuario_id_excluir = None

            if not st.session_state.confirmar_exclusao_usuario:
                if st.button("Excluir usuário"):
                    if st.session_state.get("usuario_id") == usuario_id:
                        st.error("❌ Você não pode excluir o próprio usuário logado.")
                    else:
                        st.session_state.confirmar_exclusao_usuario = True
                        st.session_state.usuario_id_excluir = usuario_id
                        st.session_state.usuario_nome_excluir = usuario_nome
                        st.rerun()
            else:
                try:
                    cursor = conn.cursor()

                    # Verificações vinculadas
                    cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM conta_funcionarios WHERE id_usuario = %s", 
                                   (st.session_state.usuario_id_excluir,))  # Relacionado à conta
                    total_conta = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM faltas WHERE id_usuario = %s", 
                                   (st.session_state.usuario_id_excluir,))  # Relacionado à faltas
                    total_faltas = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM extras WHERE id_usuario = %s", 
                                   (st.session_state.usuario_id_excluir,))  # Relacionado à extras
                    total_extras = cursor.fetchone()[0]

                    st.markdown("---")
                    st.warning(f"⚠️ Deseja realmente excluir o usuário **{st.session_state.usuario_nome_excluir}**?")

                    if total_conta > 0:
                        st.info(f"💵 Este usuário possui **R$ {total_conta:.2f}** em registros de gastos.")
                    else:
                        st.info("💵 Nenhum gasto registrado.")

                    if total_faltas > 0:
                        st.info(f"📋 Este usuário possui **{total_faltas} falta(s)** registrada(s).")
                    else:
                        st.info("📋 Nenhuma falta registrada.")

                    if total_extras > 0:
                        st.info(f"🕒 Este usuário possui **{total_extras} registro(s) de horas extras**.")
                    else:
                        st.info("🕒 Nenhuma hora extra registrada.")
                except Exception as e:
                    st.error(f"Erro ao verificar dados vinculados: {e}")
                finally:
                    cursor.close()

                col3, col4 = st.columns(2)
                if col3.button("✅ Sim, excluir"):
                    try:
                        cursor = conn.cursor()

                        # Excluir dados vinculados
                        cursor.execute("DELETE FROM conta_funcionarios WHERE id_usuario = %s", 
                                       (st.session_state.usuario_id_excluir,))  # Excluir contas
                        cursor.execute("DELETE FROM faltas WHERE id_usuario = %s", 
                                       (st.session_state.usuario_id_excluir,))  # Excluir faltas
                        cursor.execute("DELETE FROM extras WHERE id_usuario = %s", 
                                       (st.session_state.usuario_id_excluir,))  # Excluir extras

                        # Excluir usuário
                        cursor.execute("DELETE FROM usuarios WHERE id = %s", 
                                       (st.session_state.usuario_id_excluir,))  # Excluir do sistema
                        conn.commit()
                        st.success("✅ Usuário e todos os dados vinculados foram excluídos com sucesso.")
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")
                    finally:
                        cursor.close()

                    # Resetar estados
                    st.session_state.confirmar_exclusao_usuario = False
                    st.session_state.usuario_id_excluir = None
                    st.rerun()

                if col4.button("❌ Não, cancelar"):
                    st.session_state.confirmar_exclusao_usuario = False
                    st.session_state.usuario_id_excluir = None
                    st.rerun()


