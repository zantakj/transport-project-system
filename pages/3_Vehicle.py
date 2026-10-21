import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Vehicle", layout="wide")
st.title("🚚 3. Vehicle - หน้าดูข้อมูลเกี่ยวกับรถ")

# ดึงข้อมูลจากฐานข้อมูล
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

if not df.empty and 'Vehicle_Code' in df.columns:
    st.subheader("📋 สรุปข้อมูลการใช้งานรถแต่ละคัน")
    
    # 1. กลุ่มข้อมูลโดยใช้ชื่อภาษาอังกฤษทั้งหมดก่อนเพื่อป้องกัน Encoding Error
    v_summary = df.groupby(['Vehicle_Code', 'Vehicle_Type']).agg(
        total_trips=('Trip_ID', 'count'),
        total_distance=('Distance_km', 'sum'),
        total_fuel=('Fuel_Liters', 'sum'),
        total_fuel_cost=('Fuel_Cost_THB', 'sum')
    ).reset_index()

    # 2. คำนวณอัตราสิ้นเปลือง (กม./ลิตร)
    v_summary['fuel_efficiency'] = (v_summary['total_distance'] / v_summary['total_fuel']).round(2)

    # 3. เปลี่ยนชื่อคอลัมน์เป็นภาษาไทยสวยงามก่อนแสดงผล
    v_summary = v_summary.rename(columns={
        'Vehicle_Code': 'รหัสรถ',
        'Vehicle_Type': 'ประเภทรถ',
        'total_trips': 'จำนวนเที่ยววิ่ง',
        'total_distance': 'ระยะทางรวม (กม.)',
        'total_fuel': 'น้ำมันที่ใช้ (ลิตร)',
        'total_fuel_cost': 'ค่าน้ำมันรวม (บาท)',
        'fuel_efficiency': 'อัตราสิ้นเปลือง (กม./ลิตร)'
    })

    # แสดงผลตารางข้อมูล
    st.dataframe(v_summary, use_container_width=True, hide_index=True)

else:
    st.info("💡 ยังไม่มีข้อมูลรถในระบบ กรุณาอัปโหลดไฟล์ข้อมูลในหน้า Import Data")
