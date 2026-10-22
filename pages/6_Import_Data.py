import sqlite3
import streamlit as st

st.set_page_config(page_title="ระบบบริหารจัดการการขนส่ง - บริษัท ABC", page_icon="🚚", layout="wide")

# ฟังก์ชันลบข้อมูลเก่าทั้งหมดออกจากฐานข้อมูลเมื่อ Login ใหม่
def clear_old_database():
    try:
        conn = sqlite3.connect('transport.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shipments")
        conn.commit()
        conn.close()
    except Exception:
        pass

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.markdown("<h2 style='text-align: center;'>🔒 เข้าสู่ระบบบริหารจัดการการขนส่ง</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>กรณีศึกษา: บริษัท ABC</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("ชื่อผู้ใช้งาน (Username)")
            password = st.text_input("รหัสผ่าน (Password)", type="password")
            submit_button = st.form_submit_button("เข้าสู่ระบบ", type="primary", use_container_width=True)
            
            if submit_button:
                if username == "admin" and password == "1234":
                    st.session_state.logged_in = True
                    clear_old_database()
                    st.cache_data.clear()
                    st.success("เข้าสู่ระบบสำเร็จ! (ทำการรีเซ็ตข้อมูลเก่าในระบบเรียบร้อยแล้ว)")
                    st.rerun()
                else:
                    st.error("ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")

if not st.session_state.logged_in:
    pg = st.navigation([st.Page(login_page, title="เข้าสู่ระบบ", icon="🔒")])
else:
    # 📌 ปุ่ม Quick Import Data วางเหนือ Sidebar กดง่าย ชัดเจน
    st.sidebar.markdown("### 📥 Quick Action")
    if st.sidebar.button("📥 นำเข้าข้อมูล (Import Data)", type="primary", use_container_width=True):
        st.switch_page("pages/6_Import_Data.py")
    
    st.sidebar.divider()

    # 📌 เมนูระบบงานการวิเคราะห์
    pg = st.navigation({
        "การจัดการและวิเคราะห์ข้อมูล": [
            st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊"),
            st.Page("pages/2_Transportation_Data.py", title="Transportation Data", icon="🚚"),
            st.Page("pages/3_Vehicle.py", title="Vehicle", icon="🚛"),
            st.Page("pages/4_KPI.py", title="KPI & Real-Time Fuel", icon="🎯"),
            st.Page("pages/5_Analysis.py", title="Analysis", icon="📈"),
            st.Page("pages/6_Import_Data.py", title="Import Data", icon="📥"),
        ]
    })
    
    st.sidebar.write("")
    if st.sidebar.button("🚪 ออกจากระบบ", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

pg.run()
