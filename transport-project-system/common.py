import os

import streamlit as st

import calculations as calc
import database as db

PLOT = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")


@st.cache_data(show_spinner="กำลังคำนวณ...")
def _compute(db_mtime):
  tables = db.load_all()
  if tables is None:
    return None
  trips, fixed = calc.build_trip_costs(tables)
  return tables, trips, fixed


def get_data():
  """โหลด + คำนวณข้อมูล (cache ใหม่อัตโนมัติเมื่อนำเข้าไฟล์ใหม่) ถ้าไม่มีข้อมูลจะหยุดหน้า"""
  mtime = os.path.getmtime(db.DB_PATH) if os.path.exists(db.DB_PATH) else 0
  result = _compute(mtime)
  if result is None:
    st.warning("ยังไม่มีข้อมูลในระบบ กรุณาไปที่หน้า 'นำเข้าข้อมูล (Import Data)' เพื่ออัปโหลดไฟล์ Excel ก่อนครับ")
    st.stop()
  return result


def sidebar_filters(trips):
  """ตัวกรองช่วงเดือนและประเภทรถ ใช้ร่วมกันหลายหน้า"""
  st.sidebar.markdown("### 🎯 ตัวกรองข้อมูล")
  months = sorted(trips["Year_Month"].dropna().unique())
  m_from, m_to = st.sidebar.select_slider("ช่วงเดือน:", options=months, value=(months[0], months[-1]))
  types = ["ทั้งหมด"] + sorted(trips["Vehicle_Type"].dropna().unique())
  vt = st.sidebar.selectbox("ประเภทรถ:", types)
  df = trips[(trips["Year_Month"] >= m_from) & (trips["Year_Month"] <= m_to)]
  if vt != "ทั้งหมด":
    df = df[df["Vehicle_Type"] == vt]
  st.sidebar.caption(f"📌 แสดง {len(df):,} / {len(trips):,} เที่ยว")
  return df, vt


def baht(x):
  return f"฿{x:,.0f}"
