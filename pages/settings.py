import pandas as pd
import streamlit as st

import auth
import calculations as calc
import database as db
from common import baht, is_admin

st.title("⚙️ ตั้งค่าพารามิเตอร์")
st.caption("ทุกค่าที่ระบบใช้คำนวณ พร้อมแหล่งที่มาและสถานะ — ตารางนี้ต้องตรงกับตารางพารามิเตอร์ในรายงาน")
admin = is_admin()
STATUSES = [db.REAL, db.REF, db.ASSUMED, db.PENDING]

params = db.load_params()
view = params[["grp", "label", "value", "unit", "status", "source"]].rename(columns={
    "grp": "กลุ่ม", "label": "พารามิเตอร์", "value": "ค่า", "unit": "หน่วย", "status": "สถานะ", "source": "แหล่งที่มา"})
st.dataframe(view.assign(ค่า=view["ค่า"].map(lambda v: "—" if pd.isna(v) else f"{v:,.4g}")),
             hide_index=True, width="stretch")

p = db.param_values()
dep = calc.depreciation_per_month(p)
st.info(f"**ค่าเสื่อมราคาที่ระบบคำนวณ (วิธีเส้นตรง):** "
        + (f"({baht(p['vehicle_price'])} − {baht(p.get('salvage_value') or 0)}) ÷ ({p['useful_life']:.0f} ปี × 12) "
           f"= **{baht(dep)} ต่อคันต่อเดือน**" if dep is not None else "รอราคาทุนรถจากบริษัท"))

if admin:
  with st.expander("✏️ แก้ไขพารามิเตอร์"):
    row = st.selectbox("เลือกพารามิเตอร์", params.index, format_func=lambda i: params.loc[i, "label"])
    r = params.loc[row]
    with st.form("param"):
      v = st.number_input(f"ค่า ({r['unit']})", value=None if pd.isna(r["value"]) else float(r["value"]),
                          min_value=0.0, format="%.4f", placeholder="ยังไม่มีค่า")
      stt = st.selectbox("สถานะ", STATUSES, index=STATUSES.index(r["status"]) if r["status"] in STATUSES else 0)
      src = st.text_area("แหล่งที่มา", r["source"])
      if st.form_submit_button("บันทึก", type="primary"):
        db.update_param(r["key"], v, stt, src)
        st.cache_data.clear()
        st.rerun()

st.markdown("#### ⛽ ราคาน้ำมันดีเซลรายเดือน (ผู้ใช้กรอก)")
fuel = db.load_fuel_prices()
st.dataframe(fuel.rename(columns={"year_month": "เดือน", "price": "บาท/ลิตร", "source": "แหล่งที่มา"}),
             hide_index=True, width="stretch")
if admin:
  with st.form("fuel"):
    c = st.columns([1, 1, 3])
    months = sorted(set(db.load_imports()["year_month"]) | set(fuel["year_month"])) or ["2026-06"]
    ym = c[0].selectbox("เดือน", months)
    cur = fuel.set_index("year_month")["price"].get(ym)
    pr = c[1].number_input("บาท/ลิตร", min_value=0.0, value=float(cur) if cur is not None else None, format="%.2f")
    src = c[2].text_input("แหล่งที่มา", fuel.set_index("year_month")["source"].get(ym, ""))
    if st.form_submit_button("บันทึกราคาน้ำมัน", type="primary") and pr:
      db.upsert_fuel_price(ym, pr, src)
      st.cache_data.clear()
      st.rerun()

st.markdown("#### 🚚 จำนวนรถทั้งหมดของบริษัทรายเดือน")
imp = db.load_imports()
st.dataframe(imp[["year_month", "fleet_total"]].rename(columns={"year_month": "เดือน", "fleet_total": "รถทั้งหมด (คัน)"}),
             hide_index=True)
if admin and not imp.empty:
  with st.form("fleet"):
    c = st.columns(2)
    ym = c[0].selectbox("เดือน", imp["year_month"])
    n = c[1].number_input("รถทั้งหมด (คัน)", min_value=1, step=1, value=int(imp.set_index("year_month")["fleet_total"][ym]))
    if st.form_submit_button("บันทึก"):
      db.update_fleet_total(ym, n)
      st.cache_data.clear()
      st.rerun()

st.markdown("---")
st.markdown("#### 👤 บัญชีผู้ใช้")
with st.expander("เปลี่ยนรหัสผ่านของฉัน"):
  with st.form("pw"):
    old = st.text_input("รหัสผ่านเดิม", type="password")
    new = st.text_input("รหัสผ่านใหม่ (อย่างน้อย 8 ตัวอักษร)", type="password")
    if st.form_submit_button("เปลี่ยนรหัสผ่าน"):
      try:
        auth.change_password(st.session_state["user"], old, new)
        st.success("เปลี่ยนรหัสผ่านแล้ว")
      except ValueError as e:
        st.error(str(e))
if admin:
  st.dataframe(auth.list_users().rename(columns={"username": "ชื่อผู้ใช้", "role": "สิทธิ์", "created_at": "สร้างเมื่อ"}),
               hide_index=True)
  with st.expander("เพิ่มผู้ใช้"):
    with st.form("adduser"):
      u = st.text_input("ชื่อผู้ใช้")
      pw = st.text_input("รหัสผ่าน (อย่างน้อย 8 ตัวอักษร)", type="password")
      role = st.selectbox("สิทธิ์", list(auth.ROLES), format_func=auth.ROLES.get)
      if st.form_submit_button("เพิ่ม"):
        try:
          auth.add_user(u, pw, role)
          st.success(f"เพิ่มผู้ใช้ {u} แล้ว")
        except ValueError as e:
          st.error(str(e))
