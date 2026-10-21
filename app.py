import streamlit as st

# ตรวจสอบสถานะการเข้าสู่ระบบ
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 เข้าสู่ระบบก่อนใช้งาน")
    username = st.text_input("ชื่อผู้ใช้งาน")
    password = st.text_input("รหัสผ่าน", type="password")
    
    if st.button("เข้าสู่ระบบ"):
        # ตั้งค่ารหัสผ่านสมมติสำหรับทดสอบ
        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.success("เข้าสู่ระบบสำเร็จ!")
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    
    # ซ่อนส่วนที่เหลือหากยังไม่ Login
    st.stop()

st.success("ยินดีต้อนรับเข้าสู่ระบบจัดการขนส่ง")
