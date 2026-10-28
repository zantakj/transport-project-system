import os

import pandas as pd
import streamlit as st

import database as db

st.title("📥 นำเข้าข้อมูลการขนส่ง (Import Data)")
st.markdown(
    "อัปโหลดไฟล์ Excel ที่มีชีต **Trips, Vehicles, Routes, Cost_Parameters, Emission_Factors** "
    "ระบบจะตรวจสอบโครงสร้างแล้วบันทึกลงฐานข้อมูลกลาง"
)

if st.button("🗑️ ล้างข้อมูลเก่าในระบบทิ้งทั้งหมด"):
  if os.path.exists(db.DB_PATH):
    os.remove(db.DB_PATH)
    st.cache_data.clear()
    st.success("✅ ล้างฐานข้อมูลเดิมเรียบร้อยแล้ว!")
  else:
    st.info("ℹ️ ไม่มีข้อมูลในระบบอยู่แล้ว")

st.markdown("---")
uploaded = st.file_uploader("เลือกไฟล์ Excel (.xlsx)", type=["xlsx"])

if uploaded is None:
  st.warning("⚠️ กรุณาอัปโหลดไฟล์ Excel เพื่อเริ่มต้นใช้งานระบบ")
  st.stop()

try:
  sheets = pd.read_excel(uploaded, sheet_name=None, engine="openpyxl")
except Exception as e:
  st.error(f"❌ อ่านไฟล์ไม่ได้: {e}")
  st.stop()

problems = db.validate_workbook(sheets)
if problems:
  st.error("❌ โครงสร้างไฟล์ไม่ครบ:\n\n" + "\n".join(f"- {p}" for p in problems))
  st.stop()

st.success("✅ โครงสร้างไฟล์ถูกต้อง")
cols = st.columns(len(db.REQUIRED_SHEETS))
for c, name in zip(cols, db.REQUIRED_SHEETS):
  c.metric(name, f"{len(sheets[name]):,} แถว")

preview = st.selectbox("ดูตัวอย่างชีต:", list(db.REQUIRED_SHEETS))
st.dataframe(db.to_display(sheets[preview].head(10)), width="stretch", hide_index=True)

if st.button("🚀 ยืนยันการนำเข้าข้อมูล", type="primary"):
  with st.spinner("กำลังบันทึกข้อมูล..."):
    counts = db.save_workbook(sheets)
    st.cache_data.clear()
  st.success("✅ นำเข้าข้อมูลสำเร็จ! " + ", ".join(f"{k} {v:,} แถว" for k, v in counts.items()))
  st.balloons()
