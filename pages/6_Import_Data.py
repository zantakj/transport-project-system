import os
import database as db
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="นำเข้าข้อมูล (Import Data)", page_icon="📥", layout="wide"
)

st.title("📥 นำเข้าข้อมูลการขนส่ง (Import Data)")
st.markdown("อัปโหลดไฟล์ Excel เพื่อประมวลผลและบันทึกลงฐานข้อมูลกลาง")

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
    # บันทึกไฟล์ชั่วคราว
    with open("temp_upload.xlsx", "wb") as f:
      f.write(uploaded_file.getbuffer())

    # โหลดรายชื่อชีตทั้งหมดมาให้ผู้ใช้เลือก (โดยไม่บังคับชื่อ)
    excel_file = pd.ExcelFile("temp_upload.xlsx", engine="openpyxl")
    sheet_names = excel_file.sheet_names

    st.markdown("### 📋 เลือก Sheet ที่ต้องการใช้งาน")
    selected_sheet = st.selectbox(
        "เลือกชีตข้อมูลในไฟล์ Excel:", sheet_names, index=0
    )

    # แสดงตัวอย่างข้อมูลจากชีตที่เลือก
    df_preview = pd.read_excel(
        "temp_upload.xlsx", sheet_name=selected_sheet, engine="openpyxl"
    )
    st.markdown(f"**ตัวอย่างข้อมูลในชีต '{selected_sheet}' (5 รายการแรก):**")
    st.dataframe(df_preview.head(5), use_container_width=True)

    if st.button("🚀 ยืนยันการนำเข้าข้อมูล"):
      with st.spinner("กำลังบันทึกข้อมูล..."):
        # บันทึกชีตที่เลือกแปลงเป็นไฟล์กลางสำหรับประมวลผล
        df_preview.to_excel("temp_upload_processed.xlsx", index=False)

        # ส่งเข้าฐานข้อมูลกลาง
        rows_imported = db.process_and_save_excel("temp_upload_processed.xlsx")

        st.success(
            f"✅ นำเข้าข้อมูลสำเร็จ! จากชีต '{selected_sheet}' (จำนวน"
            f" {rows_imported:,} รายการ)"
        )
        st.balloons()

  except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาด: {e}")
else:
  st.warning("⚠️ กรุณาอัปโหลดไฟล์ Excel เพื่อเริ่มต้นใช้งานระบบ")
