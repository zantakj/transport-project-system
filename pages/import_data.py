import pandas as pd
import streamlit as st

import database as db
import importer as im
from common import is_admin, to_display

st.title("📥 นำเข้าข้อมูล")
if not is_admin():
  st.error("หน้านี้สำหรับผู้ดูแลระบบเท่านั้น")
  st.stop()

st.markdown("อัปโหลดไฟล์ Excel ของบริษัท (ชีต **Data Master** และชีตรายเดือน เช่น `jun26`) "
            "แล้วเลือกเดือนที่ต้องการนำเข้า ระบบจะปรับรูปแบบ ตรวจคุณภาพ และปกปิดข้อมูลส่วนบุคคลให้อัตโนมัติ")

imports = db.load_imports()
if not imports.empty:
  st.markdown("#### เดือนที่อยู่ในระบบแล้ว")
  st.dataframe(imports.rename(columns={
      "year_month": "เดือน", "sheet": "ชีต", "file_name": "ไฟล์", "rows": "จำนวนแถว",
      "fleet_total": "รถทั้งหมด (คัน)", "imported_at": "นำเข้าเมื่อ", "imported_by": "โดย"}).drop(columns="fingerprint"),
      hide_index=True, width="stretch")
  c1, c2 = st.columns([2, 1])
  rm = c1.selectbox("ลบข้อมูลเดือน", imports["year_month"], index=None, placeholder="เลือกเดือนที่ต้องการลบ")
  if c2.button("ลบเดือนนี้", disabled=rm is None):
    db.delete_month(rm)
    st.cache_data.clear()
    st.rerun()

st.markdown("---")
up = st.file_uploader("เลือกไฟล์ Excel (.xlsx)", type=["xlsx"])
if up is None:
  st.stop()


@st.cache_data(show_spinner="กำลังอ่านไฟล์ (ไฟล์ใหญ่อาจใช้เวลาประมาณ 30 วินาที)...")
def read_book(data, name):
  import io
  return pd.read_excel(io.BytesIO(data), sheet_name=None, engine="openpyxl")


sheets = read_book(up.getvalue(), up.name)
months = im.list_month_sheets(sheets)
if not months:
  st.error("ไม่พบชีตรายเดือนในไฟล์ (ชื่อชีตต้องเป็นรูปแบบ เช่น jun26, Aug26)")
  st.stop()

known = dict(zip(imports["fingerprint"], imports["year_month"])) if not imports.empty else {}
summary = pd.DataFrame([{
    "ชีต": m["sheet"], "เดือน": m["year_month"], "จำนวนแถว": m["rows"],
    "สถานะ": (f"⚠️ ซ้ำกับชีต {m['duplicate_of']} ทุกแถว" if m["duplicate_of"]
              else f"⚠️ ซ้ำกับข้อมูลเดือน {known[m['fingerprint']]} ในระบบ" if m["fingerprint"] in known
              and known[m["fingerprint"]] != m["year_month"] else "✅ พร้อมนำเข้า")} for m in months])
st.markdown("#### ชีตรายเดือนในไฟล์")
st.dataframe(summary, hide_index=True, width="stretch")

options = [m["sheet"] for m in months]
choice = st.selectbox("เลือกชีตที่จะนำเข้า", options,
                      index=next((i for i, m in enumerate(months) if not m["duplicate_of"]), 0))
meta = next(m for m in months if m["sheet"] == choice)
if meta["duplicate_of"]:
  st.error(f"ชีต **{choice}** มีข้อมูลเหมือนชีต **{meta['duplicate_of']}** ทุกแถว — ไม่ควรนำเข้า "
           "เพราะจะทำให้นับข้อมูลซ้ำ ควรสอบถามบริษัทก่อน")
  force = st.checkbox("ยืนยันว่าต้องการนำเข้าชีตนี้จริง")
  if not force:
    st.stop()

master = im.parse_master(sheets.get("Data Master"))
try:
  df = im.clean_month(sheets[choice], meta["year_month"], master)
except ValueError as e:
  st.error(f"โครงสร้างชีตไม่ถูกต้อง: {e}")
  st.stop()

drivers = df[df["Position"] == "Driver"]
per_day = drivers.groupby("Work_Date")["Username"].nunique()
c = st.columns(4)
c[0].metric("จำนวนแถว", f"{len(df):,}")
c[1].metric("วันที่มีข้อมูล", f"{df['Work_Date'].nunique()} วัน")
c[2].metric("รถที่วิ่งต่อวัน (เฉลี่ย / สูงสุด)", f"{per_day.mean():,.0f} / {per_day.max():,.0f} คัน",
            help="นับจากจำนวนคนขับ (Position = Driver) ที่ไม่ซ้ำกันในแต่ละวัน — คนขับ 1 คน = รถ 1 คันในวันนั้น")
c[3].metric("แถวคนขับที่พบทะเบียนรถ", f"{drivers['Plate'].notna().mean() * 100:.0f}%",
            help="ทะเบียนรถเติมจากชีต Data Master เท่าที่จับคู่ได้ด้วยรหัสพนักงานหรือเลข Booking")

fleet = st.number_input("จำนวนรถทั้งหมดของบริษัทในเดือนนี้ (คัน)", min_value=1, step=1,
                        value=int(db.param_values().get("fleet_total") or 173),
                        help="ใช้คำนวณอัตราการใช้รถและต้นทุนรถว่าง (ค่าเสื่อมของรถที่ไม่ได้วิ่ง)")
if per_day.max() > fleet:
  st.warning(f"รถที่วิ่งสูงสุดต่อวัน ({per_day.max()} คัน) มากกว่าจำนวนรถทั้งหมดที่กรอก ({fleet} คัน)")

q = im.quality_summary(df)
st.markdown("#### ผลตรวจคุณภาพข้อมูล (ทำเครื่องหมายไว้ ไม่ลบทิ้ง)")
st.dataframe(q[q["จำนวนแถว"] > 0], hide_index=True, width="stretch")

with st.expander("ดูตัวอย่างข้อมูลหลังจัดเตรียม (10 แถวแรก)"):
  show = df.assign(Plate_Masked=df["Plate"].map(im.mask_plate))[
      ["Work_Date", "Store", "Zone", "Username", "Position", "Plate_Masked", "Shift_In", "Trips", "Drops",
       "Distance_km", "Fuel_Fee", "Total_Payment", "Flags"]].head(10)
  st.dataframe(to_display(show), hide_index=True, width="stretch")
  st.caption("ชื่อ-นามสกุลถูกตัดออกก่อนบันทึก (PDPA) — ใช้รหัสพนักงานแทน และแสดงทะเบียนรถแบบปกปิด")

if st.button(f"🚀 นำเข้าข้อมูลเดือน {meta['year_month']}", type="primary"):
  db.save_master(master)
  db.save_month(df, meta["year_month"], choice, up.name, fleet, meta["fingerprint"], st.session_state["user"])
  st.cache_data.clear()
  st.success(f"นำเข้าข้อมูลเดือน {meta['year_month']} สำเร็จ ({len(df):,} แถว)")
