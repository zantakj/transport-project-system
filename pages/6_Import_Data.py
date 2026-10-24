import database as db
import streamlit as st

st.set_page_config(
    page_title="นำเข้าข้อมูล (Import Data)", page_icon="📥", layout="wide"
)

st.title("📥 นำเข้าข้อมูลการขนส่ง (Import Data)")
st.markdown("อัปโหลดไฟล์ Excel ของคุณเพื่อประมวลผลและบันทึกลงฐานข้อมูลกลาง")

# ช่องสำหรับอัปโหลดไฟล์ Excel
uploaded_file = st.file_uploader("เลือกไฟล์ Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
  try:
    # บันทึกไฟล์ชั่วคราวเพื่อส่งให้ database.py ประมวลผล
    with open("temp_upload.xlsx", "wb") as f:
      f.write(uploaded_file.getbuffer())

    # เรียกใช้ฟังก์ชันประมวลผลและบันทึกลง SQLite
    rows_imported = db.process_and_save_excel("temp_upload.xlsx")

    st.success(
        f"✅ นำเข้าข้อมูลและบันทึกลงฐานข้อมูลสำเร็จ! (จำนวน {rows_imported:,}"
        " รายการ)"
    )
    st.balloons()

    st.info(
        "💡 ตอนนี้คุณสามารถคลิกเปลี่ยนไปดูหน้าที่เมนู 'KPI & Cost Analytics'"
        " หรือหน้า 'Dashboard' ได้เลยครับ ข้อมูลจะแสดงขึ้นมาทันที"
    )

  except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")
else:
  st.warning("⚠️ กรุณาอัปโหลดไฟล์ Excel เพื่อเริ่มต้นใช้งานระบบ")

  # แสดงข้อมูลตัวอย่างโครงสร้างไฟล์ที่รองรับ
  with st.expander("📌 ดูโครงสร้างคอลัมน์ Excel ที่จำเป็นต้องมี"):
    st.markdown("""
        ไฟล์ Excel ของคุณควรมีชีทชื่อ **Trips** และมีคอลัมน์หลัก ๆ ดังนี้:
        - `Trip_ID`, `Trip_Date`, `Vehicle_Type`, `Route_Code`
        - `Departure_Time`, `Actual_Delivery`, `Scheduled_Delivery`, `Completion_Time`
        - `Distance_km`, `Agreed_Price_THB` (Revenue)
        - `Fuel_Cost_THB`, `Driver_Allowance_THB`, `Tollway_Cost_THB`, `Insurance_Allocated_THB`, `Other_Variable_Cost_THB`
        """)
