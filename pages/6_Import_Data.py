import database as db
import streamlit as st

st.set_page_config(
    page_title="นำเข้าข้อมูล (Import Data)", page_icon="📥", layout="wide"
)

st.title("📥 นำเข้าข้อมูลการขนส่ง (Import Data)")
st.markdown("อัปโหลดไฟล์ Excel ของคุณเพื่อประมวลผลและบันทึกลงฐานข้อมูลกลาง")

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
    st.info(
        "💡 ตอนนี้คุณสามารถคลิกเปลี่ยนไปดูหน้า 'KPI & Cost Analytics'"
        " หรือหน้าอื่นๆ ได้เลยครับ ข้อมูลจะแสดงขึ้นมาแล้ว"
    )

  except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")
else:
  st.warning("⚠️ กรุณาอัปโหลดไฟล์ Excel เพื่อเริ่มต้นใช้งานระบบ")
