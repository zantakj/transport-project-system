import pandas as pd
import streamlit as st

import auth
import calculations as calc
import database as db
from common import baht, is_admin, th_month

st.title("⚙️ ตั้งค่าพารามิเตอร์")
st.caption("พารามิเตอร์ที่ระบบใช้คำนวณ พร้อมสถานะและแหล่งที่มา ตามตารางที่ 3.5 ของรายงาน")
admin = is_admin()

params = db.load_param_table()
view = params[["label", "value", "unit", "status", "source"]].copy()
view["value"] = view["value"].map(lambda v: "—" if pd.isna(v) else f"{v:,.4f}".rstrip("0").rstrip("."))
fuel = db.load_fuel_prices()
fuel_txt = " ".join(f"{th_month(m)[:-5]} {v:.2f}" for m, v in zip(fuel["year_month"], fuel["price"]))
view.loc[len(view)] = ["ราคาน้ำมันดีเซลเฉลี่ยรายเดือน", fuel_txt, "บาท/ลิตร", "ผู้ใช้กรอก",
                       ""]
st.dataframe(view.rename(columns={"label": "พารามิเตอร์", "value": "ค่า", "unit": "หน่วย", "status": "สถานะ",
                                  "source": "แหล่งที่มา"}), hide_index=True, width="stretch")

p = db.param_values()
st.info(f"**ค่าซ่อมบำรุงของกองรถที่ระบบคำนวณเอง:** {p['fleet_total']:.0f} คัน × ({p['dep_day']:,.2f} + "
        f"{p['ins_year']:,.0f} ÷ 365) = **{baht(calc.fleet_day_cost(p), 2)} ต่อวัน**")

if admin:
  with st.expander("✏️ แก้ไขพารามิเตอร์ (ผู้ดูแลระบบ)"):
    i = st.selectbox("เลือกพารามิเตอร์", params.index, format_func=lambda i: params.loc[i, "label"])
    r = params.loc[i]
    with st.form("param"):
      v = st.number_input(f"ค่า ({r['unit']})", value=float(r["value"]), min_value=0.0, format="%.4f")
      src = st.text_area("แหล่งที่มา", r["source"])
      if st.form_submit_button("บันทึก", type="primary"):
        db.update_param(r["table"], r["key"], v, src)
        st.cache_data.clear()
        st.rerun()

st.markdown("#### ⛽ ราคาน้ำมันดีเซลรายเดือน")
fc = st.columns([3, 2])
fc[0].caption("ราคาขายปลีกดีเซล B7 ของ ปตท. เขตกรุงเทพฯ เฉลี่ยรายเดือน (บริษัทเติมน้ำมันที่ ปตท.)")
fc[1].link_button("🔗 ดูราคาน้ำมัน ปตท.", db.FUEL_URL, width="stretch")
st.dataframe(fuel[["year_month", "price"]].assign(year_month=fuel["year_month"].map(th_month)).rename(
    columns={"year_month": "เดือน", "price": "บาท/ลิตร"}), hide_index=True, width="stretch")
if admin:
  with st.form("fuel"):
    c = st.columns([1, 1])
    months = sorted(set(db.load_imports()["year_month"]) | set(fuel["year_month"]))
    ym = c[0].selectbox("เดือน", months, format_func=th_month)
    cur = fuel.set_index("year_month")["price"].get(ym)
    pr = c[1].number_input("บาท/ลิตร", min_value=0.0, value=float(cur) if cur is not None else None, format="%.2f")
    if st.form_submit_button("บันทึกราคาน้ำมัน", type="primary") and pr:
      db.upsert_fuel_price(ym, pr, db.FUEL_SOURCE)
      st.cache_data.clear()
      st.rerun()
  st.caption("เพิ่มเดือนใหม่: นำเข้าข้อมูลเดือนนั้นก่อน แล้วเดือนจะขึ้นในรายการให้เลือก")
else:
  st.caption("ผู้ใช้งานทั่วไป (Viewer) ดูได้อย่างเดียว — การแก้ไขพารามิเตอร์และราคาน้ำมันทำได้เฉพาะผู้ดูแลระบบ")

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
