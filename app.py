import streamlit as st

st.set_page_config(
    page_title="ระบบบริหารจัดการการขนส่ง", page_icon="🚛", layout="wide"
)

# กำหนดเส้นทางหน้า Multi-page
dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊")
transport_data_page = st.Page(
    "pages/2_Transportation_Data.py", title="Transportation Data", icon="📋"
)
vehicle_page = st.Page("pages/3_Vehicle.py", title="Vehicle", icon="🚛")
kpi_page = st.Page(
    "pages/4_KPI.py", title="KPI & Cost Analytics", icon="🎯"
)
analysis_page = st.Page("pages/5_Analysis.py", title="Analysis", icon="📈")
import_data_page = st.Page(
    "pages/6_Import_Data.py", title="นำเข้าข้อมูล (Import Data)", icon="📥"
)

# ตั้งค่าระบบนำทาง Navigation
pg = st.navigation({
    "QUICK ACTION": [import_data_page],
    "รายการเมนูวิเคราะห์ข้อมูล": [
        dashboard_page,
        transport_data_page,
        vehicle_page,
        kpi_page,
        analysis_page,
    ],
})

pg.run()
