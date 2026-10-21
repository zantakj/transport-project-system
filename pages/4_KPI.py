import streamlit as st

# ตรวจสอบสิทธิ์การเข้าถึง
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⛔ กรุณาเข้าสู่ระบบก่อนใช้งานหน้านี้")
    st.stop()
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="KPI", layout="wide")
st.title("🎯 4. KPI - ติดตาม KPI ของงานขนส่ง")

conn = sqlite3.connect('transport.db')
try:
    df = pd.read_sql("SELECT * FROM shipments", conn)
except Exception:
    df = pd.DataFrame()
conn.close()

if not df.empty:
    total_trips = len(df)
    completed_trips = len(df[df['Job_Status'] == 'Completed']) if 'Job_Status' in df.columns else total_trips
    
    # อัตราการวิ่งงานสำเร็จ
    completion_rate = (completed_trips / total_trips * 100) if total_trips > 0 else 0
    # ระยะทางเฉลี่ยต่อเที่ยว
    avg_distance = df['Distance_km'].mean() if 'Distance_km' in df.columns else 0
    # อัตราการจัดส่งตรงเวลา (OTD)
    otd_count = len(df[df['OTD_Calculated'] == 'On time']) if 'OTD_Calculated' in df.columns else 0
    otd_rate = (otd_count / total_trips * 100) if total_trips > 0 else 0

    st.subheader("🎯 สรุปตัวชี้วัดประสิทธิภาพ (KPIs)")
    col1, col2, col3 = st.columns(3)
    col1.metric("อัตราการวิ่งงานสำเร็จ", f"{completion_rate:.1f}%")
    col2.metric("ระยะทางเฉลี่ยต่อเที่ยว", f"{avg_distance:.1f} กม.")
    col3.metric("อัตราส่งตรงเวลา (OTD)", f"{otd_rate:.1f}%")

    st.divider()
    
    # แสดงสรุปรายเดือนหากมีข้อมูล
    if 'Year_Month' in df.columns:
        st.subheader("📅 สรุป KPI แยกตามเดือน")
        monthly = df.groupby('Year_Month').agg(
            เที่ยววิ่งรวม=('Trip_ID', 'count'),
            ระยะทางรวม_กม=('Distance_km', 'sum'),
            รายได้รวม_บาท=('Revenue_THB', 'sum'),
            กำไรรวม_บาท=('Profit_THB', 'sum')
        ).reset_index()
        st.dataframe(monthly, use_container_width=True, hide_index=True)
else:
    st.info("💡 ไม่พบข้อมูลสำหรับคำนวณ KPI")
