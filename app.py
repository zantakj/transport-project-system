import streamlit as st

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="ระบบบริหารจัดการการขนส่ง - บริษัท ABC", page_icon="🚚", layout="wide")

# 1. ตรวจสอบสถานะการเข้าสู่ระบบใน Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 2. ฟังก์ชันหน้าเข้าสู่ระบบ (Login Form)
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
                    st.success("เข้าสู่ระบบสำเร็จ!")
                    st.rerun()
                else:
                    st.error("ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")

# 3. ควบคุมการเข้าถึงหน้าเว็บ (Routing & Navigation)
if not st.session_state.logged_in:
    # หากยังไม่ Login ให้เห็นเฉพาะหน้า Login และซ่อน Sidebar เมนูอื่นทั้งหมด
    pg = st.navigation([st.Page(login_page, title="เข้าสู่ระบบ", icon="🔒")])
else:
    # เมื่อ Login สำเร็จแล้ว จึงจะเปิดให้เห็นและเข้าถึงหน้าต่างๆ ได้
    pg = st.navigation({
        "การจัดการและวิเคราะห์ข้อมูล": [
            st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊"),
            st.Page("pages/2_Transportation_Data.py", title="Transportation Data", icon="🚚"),
            st.Page("pages/3_Vehicle.py", title="Vehicle", icon="🚛"),
            st.Page("pages/4_KPI.py", title="KPI", icon="🎯"),
            st.Page("pages/5_Analysis.py", title="Analysis", icon="📈"),
            st.Page("pages/6_Import_Data.py", title="Import Data", icon="📥"),
        ]
    })
    
    # ปุ่มออกจากระบบบริเวณ Sidebar
    if st.sidebar.button("🚪 ออกจากระบบ", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# สั่งรัวระบบ Navigation
pg.run()
