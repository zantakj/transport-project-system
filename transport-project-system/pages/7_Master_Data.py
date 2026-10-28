import streamlit as st

import database as db
from common import get_data

st.title("📚 Master Data & สมมติฐานการคำนวณ")
st.caption("ข้อมูลอ้างอิงที่ระบบใช้คำนวณ (มาจากไฟล์ที่นำเข้า) — ผู้ใช้ไม่ต้องกรอกค่าเสื่อมหรือต้นทุนเอง")

tables, _, _ = get_data()
names = {"Vehicles": "🚚 กองรถ (Vehicles)", "Routes": "📍 เส้นทาง (Routes)",
         "Cost_Parameters": "🧾 พารามิเตอร์ต้นทุน (Cost_Parameters)",
         "Emission_Factors": "🌿 ค่าการปล่อยคาร์บอน (Emission_Factors)"}
for key, title in names.items():
  st.markdown(f"#### {title}")
  st.dataframe(db.to_display(tables[key]), width="stretch", hide_index=True)
