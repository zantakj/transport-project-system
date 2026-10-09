import sqlite3
import pandas as pd
import streamlit as st

st.title("🚚 ตารางข้อมูลการขนส่ง")

# ฟังก์ชันดึงข้อมูลจากตาราง shipments
def get_transport_data():
    conn = sqlite3.connect('transport.db')
    cursor = conn.cursor()
    
    # ตรวจสอบว่ามีตาราง shipments หรือไม่
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shipments';")
    has_table = cursor.fetchone()
    
    if not has_table:
        conn.close()
        return pd.DataFrame()
        
    try:
        # เรียงลำดับจาก ID ล่าสุดขึ้นก่อน
        query = "SELECT * FROM shipments ORDER BY id DESC"
        df = pd.read_sql(query, conn)
    except Exception:
        # หากไม่มีคอลัมน์ id ให้ดึงแบบธรรมดา
        query = "SELECT * FROM shipments"
        df = pd.read_sql(query, conn)
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

    # แสดงตารางข้อมูล
    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.info("💡 ยังไม่มีข้อมูลในฐานข้อมูล กรุณาไปที่หน้า Import Data เพื่ออัปโหลดไฟล์ข้อมูลก่อนครับ")
