import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("🏠 1. Dashboard — หน้าหลัก")

def get_data():
    conn = sqlite3.connect('transport.db')
    try:
        df = pd.read_sql("SELECT * FROM shipments", conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

df = get_data()

if not df.empty:
    # คำนวณตัวเลข KPI หลัก
    total_trips = len(df)
    unique_vehicles = df['Vehicle_Code'].nunique() if 'Vehicle_Code' in df.columns else 0
    total_distance = df['Distance_km'].sum() if 'Distance_km' in df.columns else 0
    total_fuel = df['Fuel_Liters'].sum() if 'Fuel_Liters' in df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("จำนวนเที่ยววิ่งรวม", f"{total_trips:,} เที่ยว")
    col2.metric("จำนวนรถที่ใช้งาน", f"{unique_vehicles:,} คัน")
    col3.metric("ระยะทางรวม", f"{total_distance:,.1f} กม.")
    col4.metric("ปริมาณเชื้อเพลิงรวม", f"{total_fuel:,.1f} ลิตร")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 จำนวนเที่ยววิ่งแยกตามประเภทรถ")
        if 'Vehicle_Type' in df.columns:
            fig1 = px.bar(df['Vehicle_Type'].value_counts().reset_index(), 
                          x='Vehicle_Type', y='count', labels={'Vehicle_Type':'ประเภทรถ', 'count':'จำนวนเที่ยว'})
            st.plotly_chart(fig1, use_container_width=True)
    
    with c2:
        st.subheader("🚩 จำนวนเที่ยววิ่งแยกตามเส้นทาง (Top 10)")
        if 'Route_Code' in df.columns:
            top_routes = df['Route_Code'].value_counts().head(10).reset_index()
            fig2 = px.bar(top_routes, x='Route_Code', y='count', labels={'Route_Code':'เส้นทาง', 'count':'จำนวนเที่ยว'})
            st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("💡 ยังไม่มีข้อมูลในฐานข้อมูล กรุณาอัปโหลดไฟล์ในหน้า Import Data")
