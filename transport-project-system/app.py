import streamlit as st

st.set_page_config(page_title="ระบบบริหารจัดการการขนส่ง", page_icon="🚛", layout="wide")

pg = st.navigation({
    "QUICK ACTION": [
        st.Page("pages/6_Import_Data.py", title="นำเข้าข้อมูล (Import Data)", icon="📥"),
    ],
    "รายการเมนูวิเคราะห์ข้อมูล": [
        st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊"),
        st.Page("pages/2_Transportation_Data.py", title="Transportation Data", icon="📋"),
        st.Page("pages/3_Vehicle.py", title="Vehicle", icon="🚛"),
        st.Page("pages/4_KPI.py", title="KPI & Cost Analytics", icon="🎯"),
        st.Page("pages/5_Analysis.py", title="Analysis", icon="📈"),
    ],
    "ข้อมูลอ้างอิง": [
        st.Page("pages/7_Master_Data.py", title="Master Data & สมมติฐาน", icon="📚"),
    ],
})
pg.run()
