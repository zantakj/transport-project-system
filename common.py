"""common.py — ส่วนที่ทุกหน้าใช้ร่วมกัน (โหลดข้อมูล ตัวกรอง การ์ดตัวเลข การจัดรูปแบบ)"""
import numpy as np
import pandas as pd
import streamlit as st

import calculations as calc
import database as db

PLOT = dict(template="plotly_white", margin=dict(t=30, b=10, l=10, r=10))
COLORS = {"primary": "#2563EB", "good": "#16A34A", "warn": "#D97706", "bad": "#DC2626", "muted": "#94A3B8"}

# ชื่อคอลัมน์สำหรับแสดงผล: ชื่อไทย (ชื่อในระบบ)
LABELS = {
    "Work_Date": "วันที่", "Year_Month": "เดือน", "Store": "สาขา", "Zone": "โซน", "Username": "รหัสพนักงาน",
    "Position": "ตำแหน่ง", "Plate_Masked": "ทะเบียนรถ", "Box_Type": "ประเภทตู้", "Booking": "เลข Booking",
    "Rate_Card": "เรทค่าจ้าง", "Shift_In": "เข้ากะ", "Shift_Out": "ออกกะ", "Punch_In": "ลงเวลาเข้า",
    "Punch_Out": "ลงเวลาออก", "Work_Hrs": "ชั่วโมงทำงาน", "Shift_Group": "ช่วงกะ",
    "OT_Hrs": "OT (ชม.)", "OT_Request_Hrs": "OT ที่ขอ (ชม.)", "OT_Approved_Hrs": "OT ที่อนุมัติ (ชม.)",
    "Trips": "จำนวนเที่ยว", "Drops": "จุดส่ง", "Distance_km": "ระยะทาง (กม.)", "Planned_km": "ระยะตามแผน (กม.)",
    "Odometer_km": "ระยะตามเลขไมล์ (กม.)", "Excess_km": "ระยะเกินแผน (กม.)",
    "Vehicle_Fee": "ค่ารถ", "Fuel_Fee": "ค่าน้ำมัน", "OT_Fee": "ค่าโอที", "Incentive": "Incentive",
    "Penalty": "ค่าปรับ", "Total_Payment": "ยอดรวมทั้งหมด", "EBilling_Status": "E-Billing",
    "Fuel_Price": "ราคาน้ำมัน (บาท/ลิตร)", "Fuel_L": "น้ำมัน (ลิตร)", "km_per_L": "กม./ลิตร", "CO2_kg": "CO₂e (กก.)",
    "Revenue_THB": "รายได้ (สมมติ)", "Payment_THB": "ค่าใช้จ่ายตาม E-Billing", "Maintenance_THB": "ค่าซ่อมบำรุง/ยาง",
    "Depreciation_THB": "ค่าเสื่อมราคา", "Insurance_THB": "ประกัน/ภาษีรถ", "Total_Cost_THB": "ต้นทุนรวม",
    "Profit_THB": "กำไรสุทธิ", "Flags": "ปัญหาที่พบ", "Remark": "หมายเหตุ",
    "Person_Days": "พนักงาน-วัน", "Vehicle_Days": "รถ-วัน", "Payment": "ค่าใช้จ่ายตาม E-Billing",
    "Cost_per_km": "ต้นทุน/กม.", "Cost_per_Drop": "ต้นทุน/จุดส่ง", "CO2_per_km": "CO₂e/กม. (กก.)",
    "Active_Vehicles": "รถที่วิ่ง (คัน)", "Fleet_Total": "รถทั้งหมด (คัน)", "Idle_Vehicles": "รถว่าง (คัน)",
    "Utilization": "อัตราการใช้รถ (%)", "Idle_Cost_THB": "ต้นทุนรถว่าง",
}


def to_display(df):
  return df.rename(columns={c: LABELS.get(c, c) for c in df.columns})


def baht(x):
  return "—" if x is None or pd.isna(x) else f"฿{x:,.0f}"


def num(x, d=0, unit=""):
  return "—" if x is None or pd.isna(x) else f"{x:,.{d}f}{unit}"


@st.cache_data(show_spinner="กำลังคำนวณ...")
def _compute(_version):
  ops = db.load_ops()
  p = db.param_values()
  imports = db.load_imports()
  t, daily = calc.build(ops, p, db.load_fuel_prices(), imports)
  return t, daily, p, imports


def get_data():
  """โหลด + คำนวณ (ล้าง cache อัตโนมัติเมื่อข้อมูลหรือพารามิเตอร์เปลี่ยน) ถ้ายังไม่มีข้อมูลจะหยุดหน้า"""
  t, daily, p, imports = _compute(db.data_version())
  if t.empty:
    st.warning("ยังไม่มีข้อมูลในระบบ — ผู้ดูแลระบบต้องนำเข้าไฟล์ Excel ที่หน้า **นำเข้าข้อมูล** ก่อน")
    st.stop()
  return t, daily, p, imports


def sidebar_filters(t, daily, positions=True):
  """ตัวกรอง: เดือน สาขา โซน ตำแหน่ง (ใช้ร่วมกันทุกหน้า)"""
  st.sidebar.markdown("### ตัวกรองข้อมูล")
  months = sorted(t["Year_Month"].unique())
  month = st.sidebar.selectbox("เดือน", ["ทุกเดือน"] + months, index=len(months), key="f_month")
  zones = st.sidebar.multiselect("โซน", sorted(t["Zone"].unique()), key="f_zone")
  stores = st.sidebar.multiselect("สาขา", sorted(t["Store"].unique()), key="f_store")
  pos = st.sidebar.multiselect("ตำแหน่ง", sorted(t["Position"].unique()), key="f_pos") if positions else []
  m = pd.Series(True, index=t.index)
  if month != "ทุกเดือน":
    m &= t["Year_Month"].eq(month)
  if zones:
    m &= t["Zone"].isin(zones)
  if stores:
    m &= t["Store"].isin(stores)
  if pos:
    m &= t["Position"].isin(pos)
  df = t[m]
  d = daily if month == "ทุกเดือน" else daily[daily["Year_Month"] == month]
  if zones or stores:
    # จำนวนรถที่วิ่งต้องนับใหม่ตามตัวกรอง (รถทั้งหมดของบริษัทเทียบได้เฉพาะเมื่อไม่กรองสาขา/โซน)
    act = df[df["Vehicle_Day"] == 1].groupby("Work_Date")["Username"].nunique()
    d = d.assign(Active_Vehicles=d["Work_Date"].map(act).fillna(0))
  st.sidebar.caption(f"แสดง {len(df):,} จาก {len(t):,} แถว")
  return df, d, month


def card(col, title, value, sub="", tone="primary"):
  col.markdown(
      f"""<div style="border:1px solid rgba(148,163,184,.35);border-left:4px solid {COLORS[tone]};
      border-radius:10px;padding:12px 14px;margin-bottom:10px">
      <div style="font-size:.8rem;opacity:.75">{title}</div>
      <div style="font-size:1.45rem;font-weight:700;line-height:1.3">{value}</div>
      <div style="font-size:.78rem;opacity:.7">{sub}</div></div>""", unsafe_allow_html=True)


def pending_notice(p, what="กำไรสุทธิ"):
  """แจ้งรายการที่ยังไม่ได้หักเพราะยังไม่มีพารามิเตอร์"""
  miss = calc.missing_deductions(p)
  if p.get("trip_price") is None:
    st.warning(f"⏳ ยังคำนวณ **{what}** ไม่ได้ เพราะยังไม่ได้กำหนด **ค่าเที่ยวที่ลูกค้าจ่าย** (ค่าสมมติ) — "
               "ผู้ดูแลระบบกำหนดได้ที่หน้า **ตั้งค่าพารามิเตอร์**")
  if miss:
    st.info("ℹ️ ต้นทุนที่ **ยังไม่ได้หัก** เพราะรอข้อมูลบริษัท: " + ", ".join(miss) +
            " — ตัวเลขต้นทุนและกำไรในหน้านี้จึงยังไม่ใช่ต้นทุนเต็มรูปแบบ")
  return miss


def is_admin():
  return st.session_state.get("role") == "admin"
