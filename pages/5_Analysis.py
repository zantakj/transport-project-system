import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import db  # เรียกใช้ไฟล์ db.py ที่เราสร้างขึ้นใหม่

# ดึงข้อมูลมาแสดงผล
df = db.load_data_from_db()
import database as db
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

# ดึงข้อมูลจากฐานข้อมูลกลางมาใช้
df = db.load_data_from_db()

if df.empty:
  st.warning(
      "ยังไม่มีข้อมูลในระบบ กรุณาไปที่หน้า 'นำเข้าข้อมูล (Import Data)' ก่อนครับ"
  )
else:
  st.title("📊 รายละเอียดข้อมูลในระบบ")
  st.dataframe(df, use_container_width=True)

# 🚨 ดักสิทธิ์เข้าถึงชั้นที่ 2
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⛔ กรุณาเข้าสู่ระบบก่อนใช้งานหน้านี้")
    st.stop()

st.set_page_config(page_title="Advanced Route & Profit Analysis", page_icon="📈", layout="wide")

st.title("📈 Advanced Route & Profit Analysis")
st.caption("วิเคราะห์เจาะลึกประสิทธิภาพเส้นทางขนส่ง กำไรขั้นต้น และจุดคุ้มทุนรายเที่ยววิ่ง")

def load_data():
    conn = sqlite3.connect('transport.db')
    try:
        df = pd.read_sql("SELECT * FROM shipments", conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

df = load_data()

if not df.empty:
    st.markdown("#### 📍 การวิเคราะห์รายได้และกำไรแยกตามเส้นทางขนส่ง (Route Code)")
    
    route_df = df.groupby('Route_Code').agg(
        Trips=('Trip_ID', 'count'),
        Total_Distance=('Distance_km', 'sum'),
        Total_Revenue=('Revenue_THB', 'sum'),
        Total_Fuel_Cost=('Fuel_Cost_THB', 'sum')
    ).reset_index()

    route_df['Net_Profit'] = route_df['Total_Revenue'] - route_df['Total_Fuel_Cost']
    route_df = route_df.sort_values(by='Total_Revenue', ascending=False)

    st.dataframe(route_df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        fig_rev = px.bar(route_df.head(10), x='Route_Code', y='Total_Revenue', title="Top 10 เส้นทางที่สร้างรายได้สูงสุด (บาท)", template="plotly_dark", color='Total_Revenue')
        st.plotly_chart(fig_rev, use_container_width=True)
    with col2:
        fig_profit = px.bar(route_df.head(10), x='Route_Code', y='Net_Profit', title="Top 10 เส้นทางที่มีกำไรสุทธิสูงสุด (บาท)", template="plotly_dark", color='Net_Profit', color_continuous_scale='Greens')
        st.plotly_chart(fig_profit, use_container_width=True)
else:
    st.info("💡 ไม่พบข้อมูลในระบบ กรุณาอัปโหลดไฟล์ในหน้า Import Data")
