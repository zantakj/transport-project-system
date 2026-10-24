import os
import database as db
import streamlit as st

st.set_page_config(
    page_title="นำเข้าข้อมูล (Import Data)", page_icon="📥", layout="wide"
)

st.title("📥 นำเข้าข้อมูลการขนส่ง (Import Data)")
st.markdown("อัปโหลดไฟล์ Excel ของคุณเพื่อประมวลผลและบันทึกลงฐานข้อมูลกลาง")

# ปุ่มล้างข้อมูลเก่าทิ้ง
if st.st.button if hasattr(st, "st") else st.button("🗑️ ล้างข้อมูลเก่าในระบบทิ้งทั้งหมด"):
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

    rows_imported = db.process_and_save_excel("temp_upload.xlsx")

    st.success(
        f"✅ นำเข้าข้อมูลและบันทึกลงฐานข้อมูลสำเร็จ! (จำนวน {rows_imported:,}"
        " รายการ)"
    )
    st.balloons()

  except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")
else:
  st.warning("⚠️ กรุณาอัปโหลดไฟล์ Excel เพื่อเริ่มต้นใช้งานระบบ")
