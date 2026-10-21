import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บแบบ Wide Layout
st.set_page_config(page_title="Transportation Dashboard", page_icon="📊", layout="wide")

# 2. ตกแต่งด้วย CSS เพื่อบังคับใช้ Modern Light UI Style (สไตล์ Power BI / Geckoboard)
st.markdown("""
<style>
    /* ปรับพื้นหลังหลักของแอป */
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
    }
    
    /* สไตล์สำหรับ KPI Card */
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s;
    }
    .kpi-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.875rem;
        font-weight: 700;
        color: #0F172A;
    }
    .kpi-sub {
        font-size: 0.8rem;
        font-weight: 500;
        color: #10B981;
        margin-top: 4px;
    }

    /* สไตล์สำหรับ Card ครอบกราฟ */
    .chart-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .chart-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ดึงข้อมูลจากฐานข้อมูล SQLite
def load_data():
    conn = sqlite3.connect('transport.db')
    try:
        df = pd.read_sql("SELECT * FROM shipments", conn)
        if 'Trip_Date' in df.columns:
            df['Trip_Date'] = pd.to_datetime(df['Trip_Date'])
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

raw_df = load_data()

# Header ส่วนบน
st.markdown("<h2 style='color:#0F172A; font-weight:800; margin-bottom: 0px;'>📊 Logistics & Transportation Analytics</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748B; margin-bottom: 24px;'>ภาพรวมประสิทธิภาพการขนส่ง ต้นทุนเชื้อเพลิง และการปล่อยก๊าซเรือนกระจก — บริษัท ABC</p>", unsafe_allow_html=True)

if not raw_df.empty:
    # ------------------------------------
    # 🔍 SIDEBAR FILTER (ตัวกรอง)
    # ------------------------------------
    st.sidebar.markdown("### 🎯 ตัวกรองข้อมูล")
    
    min_date = raw_df['Trip_Date'].min() if 'Trip_Date' in raw_df.columns else None
    max_date = raw_df['Trip_Date'].max() if 'Trip_Date' in raw_df.columns else None
    
    if min_date and max_date:
        date_range = st.sidebar.date_input(
            "ช่วงวันที่:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_d, end_d = date_range
            df = raw_df[(raw_df['Trip_Date'].dt.date >= start_d) & (raw_df['Trip_Date'].dt.date <= end_d)]
        else:
            df = raw_df.copy()
    else:
        df = raw_df.copy()

    if 'Vehicle_Type' in df.columns:
        v_types = ['ทั้งหมด'] + list(df['Vehicle_Type'].dropna().unique())
        selected_vtype = st.sidebar.selectbox("ประเภทรถ:", v_types)
        if selected_vtype != 'ทั้งหมด':
            df = df[df['Vehicle_Type'] == selected_vtype]

    st.sidebar.caption(f"📌 แสดงข้อมูล **{len(df):,}** / {len(raw_df):,} รายการ")

    # ------------------------------------
    # 📌 TOP KPI CARDS
    # ------------------------------------
    total_trips = len(df)
    total_distance = df['Distance_km'].sum() if 'Distance_km' in df.columns else 0
    total_fuel =
