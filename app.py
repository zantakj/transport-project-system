import streamlit as st

st.set_page_config(
    page_title="ระบบบริหารจัดการการขนส่ง", page_icon="🚚", layout="wide"
)

# ระบบ Login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["role"] = None

if not st.session_state["logged_in"]:
    st.title("🔐 Login - เข้าสู่ระบบ")
    col1, col2 = st.columns([1, 2])
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("เข้าสู่ระบบ", type="primary"):
            if username == "admin" and password == "1234":
                st.session_state["logged_in"] = True
                st.session_state["role"] = "Admin"
                st.success("เข้าสู่ระบบสำเร็จ!")
                st.rerun()
            elif username == "user" and password == "1234":
                st.session_state["logged_in"] = True
                st.session_state["role"] = "User"
                st.success("เข้าสู่ระบบสำเร็จ!")
                st.rerun()
            else:
                st.error("Username หรือ Password ไม่ถูกต้อง")
else:
    st.sidebar.write(f"👤 ผู้ใช้งาน: **{st.session_state['role']}**")
    if st.sidebar.button("ออกจากระบบ"):
        st.session_state["logged_in"] = False
        st.rerun()

    st.title("🚚 ระบบบริหารจัดการการขนส่ง (Transportation Management System)")
    st.info("👈 กรุณาเลือกเมนูการใช้งานจากแถบด้านข้าง (Sidebar)")