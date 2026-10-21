import streamlit as st
import pandas as pd
import sqlite3

st.title("📥 นำเข้าข้อมูลการขนส่ง (Import Data)")

uploaded_file = st.file_uploader("เลือกไฟล์ Excel หรือ CSV", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        # หากเป็นไฟล์ Excel
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_names = excel_file.sheet_names
            
            # 1. สร้าง Dropdown ให้เลือก Sheet (ตั้ง default ไว้ที่ 'Trips' หากมี)
            default_index = sheet_names.index('Trips') if 'Trips' in sheet_names else 0
            selected_sheet = st.selectbox("เลือก Sheet ที่ต้องการนำเข้า:", sheet_names, index=default_index)
            
            # อ่านข้อมูลจาก Sheet ที่เลือก
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        else:
            # หากเป็นไฟล์ CSV
            df = pd.read_csv(uploaded_file)

        # แสดงตัวอย่างข้อมูล
        st.subheader("📋 ตัวอย่างข้อมูลที่จะนำเข้า")
        st.dataframe(df.head(), use_container_width=True)

        # ปุ่มบันทึกลง Database
        if st.button("💾 บันทึกเข้า Database (SQLite)", type="primary"):
            conn = sqlite3.connect('transport.db')
            
            # บันทึกลงตาราง shipments (if_exists='replace' เพื่อเขียนทับ หรือ 'append' เพื่อเพิ่มต่อ)
            df.to_sql('shipments', conn, if_exists='replace', index=False)
            conn.close()
            
            st.success(f"✅ บันทึกข้อมูลสำเร็จเรียบร้อยแล้ว! (จำนวน {len(df)} รายการ จาก Sheet: {selected_sheet})")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")
