import streamlit as st

st.set_page_config(page_title="เข้าสู่ระบบ - Transport System", page_icon="🔒", layout="centered")

# เช็กสถานะการเข้าสู่ระบบ
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 เข้าสู่ระบบก่อนใช้งาน")
    st.caption("ระบบวิเคราะห์และติดตามข้อมูลด้านการขนส่ง — บริษัท ABC")

    username = st.text_input("ชื่อผู้ใช้งาน (Username)")
    password = st.text_input("รหัสผ่าน (Password)", type="password")

    if st.button("เข้าสู่ระบบ", type="primary", use_container_width=True):
        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.success("เข้าสู่ระบบสำเร็จ!")
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")

    # บล็อกไม่ให้โหลดเนื้อหาด้านล่างหากยังไม่ Login
    st.stop()

# ถ้า Login แล้วจะแสดงหน้านี้
st.title("🚚 ยินดีต้อนรับเข้าสู่ระบบจัดการขนส่ง")
st.success("คุณได้เข้าสู่ระบบเรียบร้อยแล้ว เลือกเมนูวิเคราะห์ข้อมูลจากแถบด้านข้างได้เลยครับ")

if st.sidebar.button("🚪 ออกจากระบบ"):
    st.session_state.logged_in = False
    st.rerun()
