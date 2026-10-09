import sqlite3
import pandas as pd
import streamlit as st

st.title("🚚 ตารางข้อมูลการขนส่ง")

# ฟังก์ชันดึงข้อมูลแบบเสถียร (เชื่อมต่อแล้วปิด Connection ทุกครั้ง)
def get_transport_data():
    conn = sqlite3.connect('transport.db')
    # ดึงข้อมูลโดยเรียงจาก ID ล่าสุดขึ้นก่อนเสมอ
    query = "SELECT * FROM transport_data ORDER BY id DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# ดึงข้อมูลล่าสุด
df = get_transport_data()

if not df.empty:
    # 1. ส่วนเลือกโหมดการแสดงผล
    col1, col2 = st.columns([2, 1])
    with col1:
        view_mode = st.radio(
            "เลือกรูปแบบการแสดงผลข้อมูล:",
            ["เฉพาะรายการล่าสุด (เพิ่งเพิ่ม)", "แสดงข้อมูลทั้งหมดในระบบ"],
            horizontal=True
        )
    
    # 2. กรองข้อมูลตามโหมดที่เลือก
    if view_mode == "เฉพาะรายการล่าสุด (เพิ่งเพิ่ม)":
        with col2:
            num_items = st.number_input("จำนวนรายการล่าสุด:", min_value=1, max_value=500, value=10)
        
        # แสดงเฉพาะ N รายการแรก (เนื่องจากเรา ORDER BY id DESC มาแล้ว)
        display_df = df.head(num_items)
        st.caption(f"📌 กำลังแสดงข้อมูลล่าสุด **{len(display_df)}** รายการ จากทั้งหมด {len(df)} รายการ")
    else:
        display_df = df
        st.caption(f"📊 กำลังแสดงข้อมูลทั้งหมด **{len(display_df)}** รายการ")

    # 3. แสดงตารางข้อมูล
    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.info("💡 ยังไม่มีข้อมูลในฐานข้อมูล กรุณาไปที่หน้า Import Data เพื่ออัปโหลดไฟล์")