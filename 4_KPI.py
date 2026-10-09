import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="KPI", page_icon="📈", layout="wide")
st.title("📈 4. KPI - ติดตาม KPI ของงานขนส่ง")

if not st.session_state.get("logged_in", False):
    st.warning("กรุณา Login ที่หน้าหลักก่อนใช้งาน")
    st.stop()

conn = sqlite3.connect("transport.db")
try:
    df = pd.read_sql_query("SELECT * FROM shipments", conn)
except Exception:
    df = pd.DataFrame()
conn.close()

if df.empty:
    st.info("ยังไม่มีข้อมูลในระบบ")
else:
    st.subheader("🎯 สรุปตัวชีวัดประสิทธิภาพ (KPIs)")

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "อัตราการวิ่งงานสำเร็จ (Completed Trips)",
        "100%",
        help="จำนวนเที่ยวที่จัดส่งสำเร็จ",
    )
    col2.metric(
        "ระยะทางเฉลี่ยต่อเที่ยว",
        f"{df['distance'].mean():,.2f} กม."
        if "distance" in df
        else "N/A",
    )
    col3.metric(
        "จำนวนเที่ยวเฉลี่ยต่อรถ 1 คัน",
        f"{len(df) / df['plate_no'].nunique():,.1f} เที่ยว/คัน",
    )

    st.divider()
    st.subheader("📌 ตารางติดตามผลการดำเนินงานตามรถ")
    kpi_df = df.groupby("plate_no").agg(
        เที่ยววิ่งทั้งหมด=("id", "count"),
        ระยะทางรวม=("distance", "sum"),
        ระยะทางเฉลี่ย=("distance", "mean"),
    )
    st.dataframe(kpi_df, use_container_width=True)