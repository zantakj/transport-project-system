import io

import pandas as pd
import streamlit as st

import database as db
import importer as im
from common import is_admin, th_month, to_display

st.title("📥 นำเข้าข้อมูล")
if not is_admin():
  st.error("หน้านี้สำหรับผู้ดูแลระบบเท่านั้น")
  st.stop()

st.markdown("อัปโหลดไฟล์ Excel **รายเที่ยว** ตามโครงสร้างในตารางที่ 3.3 (ชีต `Trips` และ `Other_Billing` ถ้ามี) "
            "แล้วเลือกเดือนของข้อมูลที่ต้องการนำเข้า ระบบจะตรวจโครงสร้างไฟล์และคุณภาพข้อมูลก่อนบันทึก")
with st.expander("คอลัมน์ที่ต้องมีในชีต Trips"):
  st.code(", ".join(im.REQUIRED))
  st.caption("ไม่บังคับ: " + ", ".join(im.OPTIONAL) + " — ข้อมูลของ Helper ในชีต Other_Billing จะถูกตัดออกอัตโนมัติ")

imports = db.load_imports()
if not imports.empty:
  st.markdown("#### ประวัติการนำเข้า")
  st.dataframe(imports.assign(year_month=imports["year_month"].map(th_month)).rename(columns={
      "year_month": "เดือนของข้อมูล", "file_name": "ไฟล์", "trips": "จำนวนเที่ยว",
      "other_rows": "รายการไม่ผูกกับเที่ยว", "imported_at": "นำเข้าเมื่อ", "imported_by": "โดย"}),
      hide_index=True, width="stretch")
  c1, c2 = st.columns([2, 1])
  rm = c1.selectbox("ลบข้อมูลเดือน", imports["year_month"], index=None, format_func=th_month,
                    placeholder="เลือกเดือนที่ต้องการลบ")
  if c2.button("ลบเดือนนี้", disabled=rm is None):
    db.delete_month(rm)
    st.cache_data.clear()
    st.rerun()

st.markdown("---")
up = st.file_uploader("เลือกไฟล์ Excel (.xlsx)", type=["xlsx"])
if up is None:
  st.stop()


@st.cache_data(show_spinner="กำลังอ่านไฟล์...")
def read_book(data, name):
  sheets = pd.read_excel(io.BytesIO(data), sheet_name=None, engine="openpyxl")
  return im.read_trips(sheets)


trips, other, qlog, missing = read_book(up.getvalue(), up.name)
if missing:
  st.error("โครงสร้างไฟล์ไม่ถูกต้อง — ไม่พบ: " + ", ".join(missing))
  st.stop()

found = sorted(trips["Year_Month"].unique())
st.markdown("#### เดือนที่พบในไฟล์")
s = trips.groupby("Year_Month").agg(เที่ยว=("Trip_ID", "size"), วัน=("Trip_Date", "nunique"),
                                   รายได้=("Revenue_THB", "sum")).reset_index()
s["รายการไม่ผูกกับเที่ยว"] = s["Year_Month"].map(other.groupby("Year_Month").size()).fillna(0).astype(int)
s["สถานะ"] = s["Year_Month"].map(lambda m: "⚠️ มีในระบบแล้ว (จะแทนที่)" if m in set(imports["year_month"])
                                 else "✅ ใหม่")
s["Year_Month"] = s["Year_Month"].map(th_month)
st.dataframe(s.rename(columns={"Year_Month": "เดือน"}).style.format({"รายได้": "{:,.0f}", "เที่ยว": "{:,}"}),
             hide_index=True, width="stretch")
months = st.multiselect("ระบุเดือนของข้อมูลที่จะนำเข้า", found, default=found, format_func=th_month)

dropped = trips.attrs.get("dropped", {})
if any(dropped.values()):
  st.warning(f"ไม่นำเข้า {dropped.get('MISSING_KEY', 0)} เที่ยวที่ไม่มีวันที่/รหัสคนขับ/รหัสสาขา และ "
             f"{dropped.get('DUP_TRIP', 0)} เที่ยวที่รหัสซ้ำ")
active = trips.groupby("Trip_Date")["Driver_Code"].nunique()
fleet = db.param_values().get("fleet_total", 173)
if active.max() > fleet:
  st.warning(f"วันที่มีรถวิ่งมากที่สุด {active.max()} คัน มากกว่าจำนวนรถทั้งหมดที่ตั้งไว้ ({fleet:.0f} คัน)")

q = im.quality_summary(trips)
st.markdown("#### ผลตรวจคุณภาพข้อมูลเบื้องต้น (ตามตารางที่ 3.2)")
st.dataframe(q[q["จำนวนเที่ยว"] > 0].drop(columns="รหัส"), hide_index=True, width="stretch")
with st.expander("ดูตัวอย่างข้อมูล (10 เที่ยวแรก)"):
  st.dataframe(to_display(trips.drop(columns=["Flags"]).head(10)), hide_index=True, width="stretch")

if st.button(f"🚀 นำเข้าข้อมูล {len(months)} เดือน", type="primary", disabled=not months):
  db.save_months(trips, other, qlog, months, up.name, st.session_state["user"])
  st.cache_data.clear()
  st.success("นำเข้าข้อมูลเดือน " + ", ".join(th_month(m) for m in months) + " สำเร็จ")
