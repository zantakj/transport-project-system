import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Vehicle", page_icon="🚚", layout="wide")
st.title("🚚 3. Vehicle - หน้าดูข้อมูลเกี่ยวกับรถ")

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
    st.subheader("📋 สรุปข้อมูลการใช้งานรถแต่ละคัน")

    # Groupby สรุปข้อมูลตามทะเบียนรถ
    vehicle_summary = (
        df.groupby(["plate_no", "vehicle_type"])
        .agg(
            จำนวนเที่ยววิ่ง=("id", "count"),
            ระยะทางรวม_กม=("distance", "sum"),
        )
        .reset_index()
    )

    st.dataframe(vehicle_summary, use_container_width=True)

    st.divider()
    st.subheader("📊 เปรียบเทียบระยะทางวิ่งของรถแต่ละคัน")
    st.bar_chart(vehicle_summary.set_index("plate_no")["ระยะทางรวม_กม"])