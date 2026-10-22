import sqlite3
import pandas as pd
import streamlit as st

# 🚨 ระบบป้องกันขั้นที่ 2
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⛔ กรุณาเข้าสู่ระบบก่อนใช้งานหน้านี้")
    st.stop()

st.set_page_config(page_title="Import Data", page_icon="📥", layout="wide")

st.title("📥 นำเข้าข้อมูลการขนส่ง (Import Data)")
st.caption("อัปโหลดไฟล์ Excel (.xlsx) เพื่อบันทึกข้อมูลเข้าสู่ฐานข้อมูล SQLite")

uploaded_file = st.file_uploader("เลือกไฟล์ Excel ข้อมูลการขนส่ง", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("📂 อ่านไฟล์สำเร็จ! ตัวอย่างข้อมูลที่กำลังจะนำเข้า:")
        st.dataframe(df.head(), use_container_width=True)

        if st.button("💾 ยืนยันบันทึกข้อมูลลงฐานข้อมูล", type="primary"):
            conn = sqlite3.connect('transport.db')
            df.to_sql('shipments', conn, if_exists='append', index=False)
            conn.close()
            st.cache_data.clear()
            st.balloons()
            st.success("🎉 บันทึกข้อมูลลงฐานข้อมูลเรียบร้อยแล้ว! สามารถไปที่หน้า Dashboard เพื่อดูการวิเคราะห์ได้ทันที")
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
