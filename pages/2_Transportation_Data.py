import database as db
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Transportation Data Management", page_icon="🚚", layout="wide"
)

st.title("🚚 Transportation Data Management")
st.caption("ตารางจัดการและค้นหาข้อมูลการขนส่งทั้งหมดในฐานข้อมูลระบบ")

# ดึงข้อมูลจากฐานข้อมูลกลาง database.py
df = db.load_data_from_db()

if df.empty:
  st.warning(
      "ยังไม่มีข้อมูลในระบบ กรุณาไปที่หน้า 'นำเข้าข้อมูล (Import Data)'"
      " เพื่ออัปโหลดไฟล์ Excel ก่อนครับ"
  )
else:
  search = st.text_input(
      "🔍 ค้นหารหัสเที่ยววิ่ง / ประเภทรถ / เส้นทาง:", ""
  )
  if search:
    # ค้นหาแบบปลอดภัยจากคอลัมน์ที่มีอยู่
    mask = pd.Series(False, index=df.index)
    for col in ["Trip_ID", "Vehicle_Type", "Route_Code"]:
      if col in df.columns:
        mask = mask | df[col].astype(str).str.contains(
            search, case=False, na=False
        )
    df = df[mask]

  st.dataframe(df, use_container_width=True, hide_index=True)
  st.caption(f"📌 แสดงผลข้อมูลทั้งหมด {len(df):,} รายการ")
