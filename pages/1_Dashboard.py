import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")
st.title("🏠 1. Dashboard — หน้าหลัก")

if not st.session_state.get("logged_in", False):
    st.warning("กรุณา Login ที่หน้าหลักก่อนใช้งาน")
    st.stop()

DB_NAME = "transport.db"


def load_data():
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM shipments", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


df = load_data()

if df.empty:
    st.info("ยังไม่มีข้อมูลในระบบ กรุณาอัปโหลดข้อมูลที่หน้า 6. Import Data ก่อนครับ")
else:
    # ตัวเลขสรุป (Key Metrics)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("จำนวนเที่ยววิ่งรวม", f"{len(df):,} เที่ยว")
    col2.metric(
        "จำนวนรถที่ใช้งาน",
        f"{df['plate_no'].nunique():,} คัน" if "plate_no" in df else "0 คัน",
    )
    col3.metric(
        "ระยะทางรวม",
        f"{df['distance'].sum():,.2f} กม." if "distance" in df else "N/A",
    )
    col4.metric(
        "ปริมาณเชื้อเพลิงรวม (ประมาณการ)",
        f"{df['distance'].sum() / 4.5:,.2f} ลิตร"
        if "distance" in df
        else "N/A",
    )

    st.divider()

    # กราฟสรุปผล
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 จำนวนเที่ยววิ่งแยกตามประเภทรถ")
        if "vehicle_type" in df:
            trip_by_type = df["vehicle_type"].value_counts()
            st.bar_chart(trip_by_type)

    with c2:
        st.subheader("📈 จำนวนเที่ยววิ่งแยกตามเส้นทาง (Top 10)")
        route_col = (
            "route_name"
            if "route_name" in df
            else ("destination" if "destination" in df else None)
        )
        if route_col:
            trip_by_dest = df[route_col].value_counts().head(10)
            st.bar_chart(trip_by_dest)