import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Vehicle", layout="wide")
st.title("🚚 3. Vehicle - หน้าดูข้อมูลเกี่ยวกับรถ")

conn = sqlite3.connect('transport.db')
try:
    df = pd.read_sql("SELECT * FROM shipments", conn)
except Exception:
    df = pd.DataFrame()
conn.close()

if not df.empty and 'Vehicle_Code' in df.columns:
    st.subheader("📋 สรุปข้อมูลการใช้งานรถแต่ละคัน")
    
    # รวมกลุ่มตามรหัสรถ และประเภทรถ
    v_summary = df.groupby(['Vehicle_Code', 'Vehicle_Type']).agg(
        จำนวนเที่ยววิ่ง=('Trip_ID', 'count'),
        ระยะทางรวม_กม=('Distance_km', 'sum'),
        น้ำมันที่ใช้_ลิตร=('Fuel_Liters', 'sum'),
        ค่าน้ำมันรวม_บาท=('Fuel_Cost_THB', 'sum')
    ).reset_index()

    # คำนวณ อัตราสิ้นเปลือง (km/L)
    v_summary['อัตราสิ้นเปลือง (กม./ลิตร)'] = (v_summary['ระยะทางรวม_กม'] / v_summary['น้ำมันที่ใช้_ลิตร']).round(2)

    st.dataframe(v_summary, use_container_width=True, hide_index=True)
else:
    st.info("💡 ไม่พบข้อมูลรถในระบบ")
