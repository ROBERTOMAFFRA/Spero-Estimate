import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import datetime

from auth.auth import verify_user, add_user, delete_user, reset_password, load_users

st.set_page_config(page_title="Spero Estimate - Secure", layout="wide")

# Helpers
@st.cache_data
def load_data(path="estimate.xlsx"):
    try:
        df = pd.read_excel(path, sheet_name=0)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        return None

def generate_pdf_bytes(client_info, items, total):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    y = height - margin
    try:
        c.drawImage("static/logo/Logo Spero.png", margin, y-40, width=90, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin+100, y-30, "Spero Restoration")
    c.setFont("Helvetica", 10)
    c.drawString(margin+100, y-45, "Orçamento")
    y -= 70
    c.setFont("Helvetica-Bold", 10); c.drawString(margin, y, "Cliente:")
    c.setFont("Helvetica", 9); c.drawString(margin+60, y, client_info.get("name",""))
    y -= 14
    c.setFont("Helvetica-Bold", 10); c.drawString(margin, y, "Endereço:")
    c.setFont("Helvetica", 9); c.drawString(margin+60, y, client_info.get("address",""))
    y -= 14
    c.setFont("Helvetica-Bold", 10); c.drawString(margin, y, "E-mail:")
    c.setFont("Helvetica", 9); c.drawString(margin+60, y, client_info.get("email",""))
    y -= 14
    c.setFont("Helvetica-Bold", 10); c.drawString(margin, y, "Telefone:")
    c.setFont("Helvetica", 9); c.drawString(margin+60, y, client_info.get("phone",""))
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Descrição")
    c.drawString(margin+300, y, "Qtd")
    c.drawString(margin+350, y, "Unit R$")
    c.drawString(margin+430, y, "Total R$")
    y -= 10
    c.line(margin, y, width-margin, y)
    y -= 14
    c.setFont("Helvetica", 9)
    for it in items:
        if y < 80:
            c.showPage()
            y = height - margin
        c.drawString(margin, y, str(it.get("DESCRIPTION",""))[:80])
        c.drawString(margin+300, y, str(it.get("QTY",1)))
        c.drawRightString(margin+400, y, f"{it.get('UNIT_PRICE',0):,.2f}")
        c.drawRightString(width-margin, y, f"{it.get('UNIT_PRICE',0)*it.get('QTY',1):,.2f}")
        y -= 14
    y -= 20
    c.line(margin, y, width-margin, y)
    y -= 16
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width-margin-50, y, "Total:")
    c.drawRightString(width-margin, y, f"{total:,.2f}")
    y -= 40
    c.setFont("Helvetica", 8)
    c.drawString(margin, y, f"Gerado em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.save()
    buf.seek(0)
    return buf.getvalue()

# Session state init
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "welcome_shown" not in st.session_state:
    st.session_state["welcome_shown"] = False
if "cart" not in st.session_state:
    st.session_state["cart"] = []

# Welcome screen first (Opção A)
if not st.session_state["authenticated"] and not st.session_state["welcome_shown"]:
    col1, col2, col3 = st.columns([1,3,1])
    with col1:
        if os.path.exists("static/logo/Logo Spero.png"):
            st.image("static/logo/Logo Spero.png", width=120)
    with col2:
        st.markdown("<h1 style='text-align:center;'>Spero Estimate</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;'>Bem-vindo ao sistema de orçamentos da Spero Restoration.</p>", unsafe_allow_html=True)
        if st.button("Iniciar Estimativa"):
            st.session_state["welcome_shown"] = True
            st.experimental_rerun()
    st.stop()

# Login screen
if not st.session_state["authenticated"] and st.session_state["welcome_shown"]:
    st.title("Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if verify_user(username.strip(), password.strip()):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username.strip()
            st.success("Login bem-sucedido")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")

# Main app
if st.session_state["authenticated"]:
    df = load_data("estimate.xlsx")
    if df is None:
        st.error("Planilha não encontrada ou erro ao carregar.")
    else:
        # Header and logout
        c1, c2 = st.columns([1,9])
        with c1:
            if os.path.exists("static/logo/Logo Spero.png"):
                st.image("static/logo/Logo Spero.png", width=110)
        with c2:
            st.markdown("### Spero Estimate — Orçamentos")
            if st.button("Logout"):
                st.session_state["authenticated"] = False
                st.session_state["welcome_shown"] = False
                st.experimental_rerun()

        st.markdown("---")

        # Sidebar: if admin, show user management
        st.sidebar.title("Menu")
        st.sidebar.write(f"Usuário: **{st.session_state.get('username','')}**")
        if st.session_state.get("username") == "admin":
            st.sidebar.subheader("Admin")
            if st.sidebar.button("Gerenciar Usuários"):
                st.session_state["show_user_mgmt"] = True
        if st.sidebar.button("Limpar Sessão"):
            st.session_state["authenticated"] = False
            st.session_state["welcome_shown"] = False
            st.session_state["cart"] = []
            st.experimental_rerun()

        # User management panel (admin only)
        if st.session_state.get("show_user_mgmt", False) and st.session_state.get("username") == "admin":
            st.subheader("Gerenciar Usuários")
            users = load_users()
            st.write("Usuários cadastrados:")
            for u in users:
                st.write(f"- {u}")
            st.markdown("Adicionar novo usuário:")
            new_user = st.text_input("Novo usuário", key="new_user")
            new_pass = st.text_input("Senha inicial", key="new_pass")
            if st.button("Adicionar usuário"):
                if new_user.strip() == "" or new_pass.strip() == "":
                    st.error("Usuário e senha são obrigatórios.")
                else:
                    ok = add_user(new_user.strip(), new_pass.strip())
                    if ok:
                        st.success("Usuário adicionado com sucesso.")
                    else:
                        st.error("Usuário já existe.")
                    st.experimental_rerun()
            st.markdown("Excluir usuário:")
            del_user = st.text_input("Usuário a excluir", key="del_user")
            if st.button("Excluir usuário"):
                if del_user.strip() == "admin":
                    st.error("Não é permitido excluir o admin.")
                else:
                    ok = delete_user(del_user.strip())
                    if ok:
                        st.success("Usuário excluído.")
                    else:
                        st.error("Usuário não encontrado.")
                    st.experimental_rerun()
            st.markdown("Redefinir senha:")
            rst_user = st.text_input("Usuário para reset", key="rst_user")
            rst_pass = st.text_input("Nova senha", key="rst_pass")
            if st.button("Redefinir senha"):
                ok = reset_password(rst_user.strip(), rst_pass.strip())
                if ok:
                    st.success("Senha redefinida.")
                else:
                    st.error("Usuário não encontrado.")
                st.experimental_rerun()
            st.markdown("---")

        # Search and add items
        query = st.text_input("Buscar item (ex: drywall):").strip()
        price_col = None
        candidates = ['TOTAL','Total','Price','PRICE','PRICE_USD','PRICE_R$','CUSTO','COST','VALUE']
        for c in candidates:
            if c in df.columns:
                price_col = c
                break
        if price_col is None:
            num_cols = df.select_dtypes(include='number').columns.tolist()
            if num_cols:
                price_col = num_cols[0]

        matches = df[df['DESCRIPTION'].astype(str).str.contains(query, case=False, na=False)] if query else df.head(0)

        st.subheader("Resultados")
        if matches.empty:
            st.write("Nenhum item encontrado." if query else "Digite ao menos 2 caracteres para pesquisar.")
        else:
            for i, row in matches.iterrows():
                cols = st.columns([6,2,1])
                with cols[0]:
                    st.write(row.get('DESCRIPTION',''))
                with cols[1]:
                    price = float(row.get(price_col, 0)) if price_col in row else 0.0
                    st.write(f"{price:,.2f}")
                with cols[2]:
                    if st.button("Adicionar", key=f"add_{i}"):
                        cart = st.session_state.get("cart", [])
                        cart.append({"DESCRIPTION": row.get('DESCRIPTION',''), "UNIT_PRICE": price, "QTY": 1})
                        st.session_state["cart"] = cart
                        st.experimental_rerun()

        st.markdown("---")
        st.subheader("Dados do Cliente")
        c1, c2 = st.columns(2)
        with c1:
            client_name = st.text_input("Nome do Cliente")
            client_address = st.text_input("Endereço")
        with c2:
            client_email = st.text_input("E-mail")
            client_phone = st.text_input("Telefone")

        st.subheader("Orçamento (itens adicionados)")
        cart = st.session_state.get("cart", [])
        if not cart:
            st.info("Nenhum item no orçamento. Adicione itens a partir dos resultados.")
        else:
            total_general = 0.0
            for idx, item in enumerate(cart):
                cols = st.columns([5,2,2,1])
                with cols[0]:
                    st.write(item["DESCRIPTION"])
                with cols[1]:
                    st.write(f"{item['UNIT_PRICE']:,.2f}")
                with cols[2]:
                    new_qty = st.number_input(f"Quantidade {idx}", min_value=1, value=item.get('QTY',1), key=f"qty_{idx}")
                    cart[idx]["QTY"] = new_qty
                with cols[3]:
                    row_total = cart[idx]["UNIT_PRICE"] * cart[idx]["QTY"]
                    total_general += row_total
                    st.write(f"{row_total:,.2f}")

            st.markdown(f"**Total Geral: R$ {total_general:,.2f}**")

            c1, c2, c3 = st.columns([1,1,3])
            with c1:
                if st.button("Remover último"):
                    if st.session_state["cart"]:
                        st.session_state["cart"].pop(-1)
                        st.experimental_rerun()
            with c2:
                if st.button("Limpar tudo"):
                    st.session_state["cart"] = []
                    st.experimental_rerun()
            with c3:
                st.write("Gerar PDF do Orçamento:")

                if st.button("Gerar e Salvar PDF"):
                    client_info = {"name": client_name, "address": client_address, "email": client_email, "phone": client_phone}
                    pdf_bytes = generate_pdf_bytes(client_info, st.session_state["cart"], total_general)
                    outputs_dir = "outputs"
                    os.makedirs(outputs_dir, exist_ok=True)
                    filename = f"orcamento_{client_name.replace(' ','_') or 'cliente'}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    filepath = os.path.join(outputs_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(pdf_bytes)
                    st.success(f"PDF salvo em: {filepath}")
                    st.download_button("Baixar PDF", pdf_bytes, file_name=filename, mime="application/pdf")
