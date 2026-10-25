import os
import database as db
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="นำเข้าข้อมูล (Import Data)", page_icon="📥", layout="wide"
)

st.title("📥 นำเข้าข้อมูลการขนส่ง (Import Data)")
st.markdown(
    "อัปโหลดไฟล์ Excel และเลือกชีตที่ต้องการเพื่อประมวลผลและบันทึกลงฐานข้อมูลกลาง"
)

# ปุ่มล้างข้อมูลเก่าทิ้ง
if st.button("🗑️ ล้างข้อมูลเก่าในระบบทิ้งทั้งหมด"):
  if os.path.exists("transport.db"):
    os.remove("transport.db")
    st.success("✅ ล้างฐานข้อมูลเดิมเรียบร้อยแล้ว!")
    st.rerun()
  else:
    st.info("ℹ️ ไม่มีข้อมูลในระบบอยู่แล้ว")

st.markdown("---")

uploaded_file = st.file_uploader("เลือกไฟล์ Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
  try:
    with open("temp_upload.xlsx", "wb") as f:
      f.write(uploaded_file.getbuffer())

    # โหลดรายชื่อ Sheet ทั้งหมดในไฟล์ Excel ออกมาให้เลือก
    excel_file = pd.ExcelFile("temp_upload.xlsx")
    sheet_names = excel_file.sheet_names

    st.markdown("### 📋 เลือก Sheet ที่ต้องการใช้งาน")
    selected_sheet = st.selectbox(
        "ระบุชื่อชีต (Sheet) ในไฟล์ Excel:", sheet_names
    )

    if st.button("🚀 ยืนยันการนำเข้าข้อมูลจากชีตนี้"):
      with st.spinner("กำลังประมวลผลและบันทึกข้อมูล..."):
        # อ่านชีตที่ผู้ใช้เลือกแล้วบันทึกทับลงไฟล์ชั่วคราวแบบระบุชีต
        df_selected = pd.read_excel("temp_upload.xlsx", sheet_name=selected_sheet)
        df_selected.to_excel("temp_upload_processed.xlsx", index=False)

        # ส่งไฟล์ชั่วคราวที่เลือกชีตแล้วไปให้ฟังก์ชันกลางประมวลผล
        rows_imported = db.process_and_save_excel("temp_upload_processed.xlsx")

        st.success(
            f"✅ นำเข้าข้อมูลจากชีต '{selected_sheet}' สำเร็จ! (จำนวน"
            f" {rows_imported:,} รายการ)"
        )
        st.balloons()

  except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์หรือเลือกชีต: {e}")
else:
  st.warning("⚠️ กรุณาอัปโหลดไฟล์ Excel เพื่อเริ่มต้นใช้งานระบบ")
