import sqlite3
import pandas as pd
import streamlit as st

st.title("🚚 ตารางข้อมูลการขนส่ง")

# เชื่อมต่อเพื่อดูตารางทั้งหมดในฐานข้อมูล
conn = sqlite3.connect('transport.db')
cursor = conn.cursor()

# ดึงชื่อตารางทั้งหมดที่มีอยู่ใน transport.db
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]

st.write("📋 **ตารางทั้งหมดที่มีอยู่ในฐานข้อมูลปัจจุบัน:**", tables)

if tables:
    # เลือกใช้ตารางแรกที่พบ
    table_name = tables[0]
    st.success(f"กำลังดึงข้อมูลจากตาราง: `{table_name}`")
    
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    
    if not df.empty:
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
            display_df = df.tail(num_items)
            st.caption(f"📌 กำลังแสดงข้อมูลล่าสุด **{len(display_df)}** รายการ จากทั้งหมด {len(df)} รายการ")
        else:
            display_df = df
            st.caption(f"📊 กำลังแสดงข้อมูลทั้งหมด **{len(display_df)}** รายการ")

        st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    conn.close()
    st.warning("⚠️ ยังไม่มีตารางใดๆ ถูกสร้างใน transport.db (โปรดกดอัปโหลดไฟล์ในหน้า Import Data อีกครั้ง)")
