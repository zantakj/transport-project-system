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

# 🔒 หากยังไม่ Login ให้แสดงเฉพาะหน้า Login เท่านั้น
if not st.session_state.logged_in:
    pg = st.navigation([st.Page(login_page, title="เข้าสู่ระบบ", icon="🔒")])
    pg.run()
else:
    # ------------------------------------
    # 🌟 CSS สลับตำแหน่ง DOM บังคับย้าย Content ขึ้นไปอยู่บนสุดเหนือ Navigation Menu
    # ------------------------------------
    st.markdown("""
    <style>
        div[data-testid="stSidebarNavItems"] {
            order: 2 !important;
        }
        div[data-testid="stSidebarHeader"] {
            order: 1 !important;
        }
        div[data-testid="stSidebarUserContent"] {
            order: 0 !important;
            margin-bottom: 20px !important;
        }
        
        div[data-testid="stSidebarUserContent"] button[kind="primary"] {
            background-color: #F97316 !important;
            color: #FFFFFF !important;
            font-weight: 800 !important;
            font-size: 1.1rem !important;
            border-radius: 10px !important;
            border: 2px solid #FB923C !important;
            padding: 12px 16px !important;
            box-shadow: 0 4px 15px rgba(249, 115, 22, 0.4) !important;
        }
        div[data-testid="stSidebarUserContent"] button[kind="primary"]:hover {
            background-color: #EA580C !important;
            box-shadow: 0 6px 20px rgba(249, 115, 22, 0.6) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 📌 ส่วนสร้างปุ่ม Quick Action บนสุด
    with st.sidebar:
        st.markdown("### ⚡ QUICK ACTION")
        if st.button("📥 นำเข้าข้อมูล (Import Data)", type="primary", use_container_width=True):
            st.switch_page("pages/6_Import_Data.py")
        st.markdown("---")

    # 📊 เมนูวิเคราะห์และ Dashboard ด้านล่าง (เอาตัวเลขนำหน้าออกทั้งหมด)
    pg = st.navigation({
        "รายการเมนูวิเคราะห์ข้อมูล": [
            st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊"),
            st.Page("pages/2_Transportation_Data.py", title="Transportation Data", icon="🚚"),
            st.Page("pages/3_Vehicle.py", title="Vehicle", icon="🚛"),
            st.Page("pages/4_KPI.py", title="KPI & Real-Time Fuel", icon="🎯"),
            st.Page("pages/5_Analysis.py", title="Analysis", icon="📈"),
        ]
    })
    
    pg.run()

    with st.sidebar:
        st.write("")
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
