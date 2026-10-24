import sqlite3
import pandas as pd
import streamlit as st
import db  # เรียกใช้ไฟล์ db.py ที่เราสร้างขึ้นใหม่

# ดึงข้อมูลมาแสดงผล
df = db.load_data_from_db()

# 🚨 ดักสิทธิ์เข้าถึงชั้นที่ 2
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⛔ กรุณาเข้าสู่ระบบก่อนใช้งานหน้านี้")
    st.stop()

st.set_page_config(page_title="Transportation Data Management", page_icon="🚚", layout="wide")

st.title("🚚 Transportation Data Management")
st.caption("ตารางจัดการและค้นหาข้อมูลการขนส่งทั้งหมดในฐานข้อมูลระบบ")

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
    search = st.text_input("🔍 ค้นหารหัสเที่ยววิ่ง / ประเภทรถ / เส้นทาง:", "")
    if search:
        df = df[
            df['Trip_ID'].astype(str).str.contains(search, case=False) |
            df['Vehicle_Type'].astype(str).str.contains(search, case=False) |
            df['Route_Code'].astype(str).str.contains(search, case=False)
        ]
    
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("💡 ไม่พบข้อมูลในระบบ กรุณาอัปโหลดไฟล์ในหน้า Import Data")
