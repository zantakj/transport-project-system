import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# 🚨 ดักสิทธิ์เข้าถึงชั้นที่ 2
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⛔ กรุณาเข้าสู่ระบบก่อนใช้งานหน้านี้")
    st.stop()

st.set_page_config(page_title="Vehicle Performance Analytics", page_icon="🚛", layout="wide")

st.title("🚛 Vehicle Performance Analytics")
st.caption("วิเคราะห์ประสิทธิภาพการใช้งานยานพาหนะ รายได้ ค่าน้ำมัน และอัตราสิ้นเปลืองแยกตามประเภทรถ")

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
    v_summary = df.groupby('Vehicle_Type').agg(
        Total_Trips=('Trip_ID', 'count'),
        Total_Distance=('Distance_km', 'sum'),
        Total_Fuel=('Fuel_Liters', 'sum'),
        Total_Revenue=('Revenue_THB', 'sum'),
        Total_Fuel_Cost=('Fuel_Cost_THB', 'sum')
    ).reset_index()

    v_summary['KM_per_Liter'] = (v_summary['Total_Distance'] / v_summary['Total_Fuel']).round(2)
    v_summary['Profit'] = v_summary['Total_Revenue'] - v_summary['Total_Fuel_Cost']

    st.markdown("#### 📊 สรุปภาพรวมยานพาหนะแยกตามประเภทรถ")
    st.dataframe(v_summary, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        fig_trips = px.bar(v_summary, x='Vehicle_Type', y='Total_Trips', title="จำนวนเที่ยววิ่งแยกตามประเภทรถ", text='Total_Trips', template="plotly_dark")
        st.plotly_chart(fig_trips, use_container_width=True)
    with col2:
        fig_km = px.bar(v_summary, x='Vehicle_Type', y='KM_per_Liter', title="อัตราสิ้นเปลืองเฉลี่ย (กม./ลิตร)", text='KM_per_Liter', template="plotly_dark", color='KM_per_Liter', color_continuous_scale='Viridis')
        st.plotly_chart(fig_km, use_container_width=True)
else:
    st.info("💡 ไม่พบข้อมูลในระบบ กรุณาอัปโหลดไฟล์ในหน้า Import Data")
