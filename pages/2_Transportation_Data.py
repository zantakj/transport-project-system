import sqlite3
import pandas as pd
import streamlit as st

st.title("🚚 ตารางข้อมูลการขนส่ง")

# ฟังก์ชันดึงข้อมูลแบบปลอดภัย (สร้างตารางให้อัตโนมัติหากยังไม่มี)
def get_transport_data():
    conn = sqlite3.connect('transport.db')
    cursor = conn.cursor()
    
    # 1. ตรวจสอบชื่อตารางที่มีทั้งหมดในฐานข้อมูล SQLite
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    
    # ถ้ายังไม่มีตาราง transport_data ให้ส่งกลับเป็น DataFrame ว่าง
    if 'transport_data' not in tables:
        conn.close()
        return pd.DataFrame()
        
    # 2. ถ้ามีตารางแล้ว ให้ลองดึงข้อมูล
    try:
        # เช็กคอลัมน์เพื่อดูว่ามี id สำหรับสั่ง ORDER BY หรือไม่
        cursor.execute("PRAGMA table_info(transport_data);")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'id' in columns:
            query = "SELECT * FROM transport_data ORDER BY id DESC"
        else:
            query = "SELECT * FROM transport_data"
            
        df = pd.read_sql(query, conn)
    except Exception as e:
        df = pd.DataFrame()
    finally:
        conn.close()
        
    return df

# ดึงข้อมูลล่าสุด
df = get_transport_data()

if not df.empty:
    # ส่วนเลือกโหมดการแสดงผล
    col1, col2 = st.columns([2, 1])
    with col1:
        view_mode = st.radio(
            "เลือกรูปแบบการแสดงผลข้อมูล:",
            ["เฉพาะรายการล่าสุด (เพิ่งเพิ่ม)", "แสดงข้อมูลทั้งหมดในระบบ"],
            horizontal=True
        )
    
    if view_mode == "เฉพาะรายการล่าสุด (เพิ่งเพิ่ม)":
        with col2:
            num_items = st.number_input("จำนวนรายการล่าสุด:", min_value=1, max_value=500, value=10)
        display_df = df.head(num_items)
        st.caption(f"📌 กำลังแสดงข้อมูลล่าสุด **{len(display_df)}** รายการ จากทั้งหมด {len(df)} รายการ")
    else:
        display_df = df
        st.caption(f"📊 กำลังแสดงข้อมูลทั้งหมด **{len(display_df)}** รายการ")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.info("💡 ยังไม่มีข้อมูลในฐานข้อมูล หรือตาราง 'transport_data' ยังไม่ถูกสร้าง กรุณาไปที่หน้า Import Data เพื่ออัปโหลดไฟล์ข้อมูลก่อนครับ")
