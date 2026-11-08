"""common.py — ส่วนที่ทุกหน้าใช้ร่วมกัน (โหลดข้อมูล ตัวกรอง การ์ดตัวเลข การจัดรูปแบบ)"""
import pandas as pd
import streamlit as st

import calculations as calc
import database as db

PLOT = dict(template="plotly_white", margin=dict(t=30, b=10, l=10, r=10))
COLORS = {"primary": "#2563EB", "good": "#16A34A", "warn": "#D97706", "bad": "#DC2626", "muted": "#94A3B8"}
CAT_COLORS = {"ค่าจ้างและค่าทำงานล่วงเวลา": "#2563EB", "ค่าน้ำมันเชื้อเพลิง": "#D97706",
              "ค่าซ่อมบำรุง (ค่าเสื่อม + ประกัน)": "#64748B"}
TH_MONTH = {"01": "ม.ค.", "02": "ก.พ.", "03": "มี.ค.", "04": "เม.ย.", "05": "พ.ค.", "06": "มิ.ย.", "07": "ก.ค.",
            "08": "ส.ค.", "09": "ก.ย.", "10": "ต.ค.", "11": "พ.ย.", "12": "ธ.ค."}

# ชื่อคอลัมน์สำหรับแสดงผล
LABELS = {
    "Trip_ID": "รหัสเที่ยว", "Trip_Date": "วันที่", "Year_Month": "เดือน", "Driver_Code": "รหัสพนักงานขับรถ",
    "Branch_Code": "รหัสสาขา", "Zone": "โซน", "Distance_km": "ระยะทาง (กม.)",
    "Planned_Distance_km": "ระยะตามแผน (กม.)", "Drops": "จุดส่ง", "Revenue_THB": "รายได้ (บาท)",
    "Trips_That_Day": "เที่ยวของคนขับวันนั้น", "Wage_THB": "ค่าจ้าง (บาท)", "OT_Approved_Hours": "OT อนุมัติ (ชม.)",
    "OT_Cost_THB": "ค่า OT (บาท)", "Fuel_L": "น้ำมัน (ลิตร)", "Fuel_Price": "ราคาน้ำมัน (บาท/ลิตร)",
    "Fuel_Cost_THB": "ค่าน้ำมัน (บาท)", "Maint_THB": "ค่าซ่อมบำรุง (บาท)", "Cost_THB": "ต้นทุนรวม (บาท)",
    "Profit_THB": "กำไรสุทธิ (บาท)", "CO2_kg": "CO₂e (กก.)", "Excess_km": "ระยะเกินแผน (กม.)",
    "EBilling_Status": "สถานะ E-Billing", "Distance_Source": "ที่มาระยะทาง", "Flags": "ปัญหาที่พบ",
    "Source_Sheet": "ชีตต้นฉบับ", "Source_Row": "แถวต้นฉบับ",
}


def to_display(df):
  return df.rename(columns={c: LABELS.get(c, c) for c in df.columns})


def th_month(ym):
  return "ทุกเดือน" if ym == "ทุกเดือน" else f"{TH_MONTH[ym[5:]]} {int(ym[:4]) + 543}"


def baht(x, d=0):
  return "—" if x is None or pd.isna(x) else f"{x:,.{d}f} บาท"


def num(x, d=0, unit=""):
  return "—" if x is None or pd.isna(x) else f"{x:,.{d}f}{unit}"


def delta(cur, prev, inverse=False):
  """ข้อความอัตราการเปลี่ยนแปลงเทียบเดือนก่อน"""
  ch = calc.pct_change(cur, prev)
  if ch is None:
    return ""
  arrow = "▲" if ch >= 0 else "▼"
  return f"{arrow} {abs(ch):.1f}% จากเดือนก่อน"


@st.cache_data(show_spinner="กำลังคำนวณ...")
def _compute(_version):
  trips = db.load_trips()
  p = db.param_values()
  if trips.empty:
    return trips, pd.DataFrame(), p
  t = calc.build(trips, p, db.fuel_dict())
  o = db.load_other()
  o = calc.other_costs(o, p) if len(o) else pd.DataFrame(
      columns=["Year_Month", "Branch_Code", "Zone", "Revenue_THB", "Wage_THB", "OT_Cost_THB", "OT_Approved_Hours"])
  return t, o, p


def get_data():
  """โหลด + คำนวณ (ล้าง cache อัตโนมัติเมื่อข้อมูลหรือพารามิเตอร์เปลี่ยน) ถ้ายังไม่มีข้อมูลจะหยุดหน้า"""
  t, o, p = _compute(db.data_version())
  if t.empty:
    st.warning("ยังไม่มีข้อมูลในระบบ — ผู้ดูแลระบบต้องนำเข้าไฟล์ Excel รายเที่ยวที่หน้า **นำเข้าข้อมูล** ก่อน")
    st.stop()
  return t, o, p


def sidebar_filters(t, o):
  """ตัวกรอง: เดือน โซน สาขา (ใช้ร่วมกันทุกหน้า)
  คืน (เที่ยวที่กรองแล้ว, รายการที่ไม่ผูกกับเที่ยวที่กรองแล้ว, เดือนที่เลือก, ทั้งกองรถหรือไม่)"""
  st.sidebar.markdown("### ตัวกรองข้อมูล")
  months = sorted(t["Year_Month"].unique())
  month = st.sidebar.selectbox("เดือน", ["ทุกเดือน"] + months, index=len(months), key="f_month",
                               format_func=th_month)
  zones = st.sidebar.multiselect("โซน", sorted(t["Zone"].unique()), key="f_zone")
  branches = st.sidebar.multiselect("สาขา", sorted(t["Branch_Code"].unique()), key="f_branch")
  mt = pd.Series(True, index=t.index)
  mo = pd.Series(True, index=o.index)
  if month != "ทุกเดือน":
    mt &= t["Year_Month"].eq(month)
    mo &= o["Year_Month"].eq(month)
  if zones:
    mt &= t["Zone"].isin(zones)
    mo &= o["Zone"].isin(zones)
  if branches:
    mt &= t["Branch_Code"].isin(branches)
    mo &= o["Branch_Code"].isin(branches)
  whole = not (zones or branches)
  st.sidebar.caption(f"แสดง {mt.sum():,} จาก {len(t):,} เที่ยว")
  if not whole:
    st.sidebar.caption("กรองโซน/สาขาอยู่: ค่าซ่อมบำรุงใช้ส่วนที่ปันส่วนให้เที่ยววิ่งที่เลือก")
  sel_months = months if month == "ทุกเดือน" else [month]
  return t[mt], o[mo], sel_months, whole


def card(col, title, value, sub="", tone="primary"):
  col.markdown(
      f"""<div style="border:1px solid rgba(148,163,184,.35);border-left:4px solid {COLORS[tone]};
      border-radius:10px;padding:12px 14px;margin-bottom:10px">
      <div style="font-size:.8rem;opacity:.75">{title}</div>
      <div style="font-size:1.4rem;font-weight:700;line-height:1.3">{value}</div>
      <div style="font-size:.78rem;opacity:.7">{sub}</div></div>""", unsafe_allow_html=True)


def fuel_notice(k):
  if k.get("fuel_missing"):
    st.warning("⛽ ยังไม่มีราคาน้ำมันของเดือน " + ", ".join(th_month(m) for m in k["fuel_missing"]) +
               " — ค่าน้ำมันและกำไรของเดือนนั้นยังไม่ครบ ผู้ดูแลระบบกรอกได้ที่หน้า **ตั้งค่าพารามิเตอร์**")


def is_admin():
  return st.session_state.get("role") == "admin"


@st.dialog("ที่มาของตัวเลข", width="large")
def _explain(title, body):
  st.markdown(f"### {title}")
  st.markdown(body)


def info(where, key, title, body, label="ⓘ ดูที่มาของตัวเลข"):
  """ปุ่มเล็กที่เปิด pop-up อธิบายสูตรและที่มา"""
  if where.button(label, key=f"info_{key}", type="tertiary"):
    _explain(title, body)


def kpi(col, key, title, value, sub, body, tone="primary"):
  """การ์ดตัวเลข + ปุ่ม ⓘ ใต้การ์ด"""
  card(col, title, value, sub, tone)
  info(col, key, title, body)
