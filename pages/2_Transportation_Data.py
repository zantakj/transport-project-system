import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Transportation Data", page_icon="📊", layout="wide"
)
st.title("📊 2. Transportation Data - ข้อมูลดิบ/จัดการข้อมูล")

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
    st.subheader("🔍 Search & Filter ค้นหาและคัดกรองข้อมูล")

    col1, col2, col3 = st.columns(3)
    with col1:
        search_plate = st.selectbox(
            "เลือกรถ (ทะเบียนรถ)", ["ทั้งหมด"] + list(df["plate_no"].unique())
        )
    with col2:
        search_type = st.selectbox(
            "เลือกประเภทเที่ยวรถ",
            ["ทั้งหมด"] + list(df["trip_type"].unique())
            if "trip_type" in df
            else ["ทั้งหมด"],
        )
    with col3:
        search_keyword = st.text_input("ค้นหาด้วยเลขใบเที่ยว / สถานที่ส่ง")

    # กรองข้อมูล
    filtered_df = df.copy()
    if search_plate != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df["plate_no"] == search_plate]
    if search_type != "ทั้งหมด" and "trip_type" in filtered_df:
        filtered_df = filtered_df[filtered_df["trip_type"] == search_type]
    if search_keyword:
        filtered_df = filtered_df[
            filtered_df["trip_no"].astype(str).str.contains(search_keyword)
            | filtered_df["destination"].astype(str).str.contains(search_keyword)
        ]

    st.write(f"ผลการค้นหา: **{len(filtered_df)}** รายการ")
    st.dataframe(filtered_df, use_container_width=True)