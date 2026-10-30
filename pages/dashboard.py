import plotly.graph_objects as go
import streamlit as st

import calculations as calc
from common import COLORS, PLOT, baht, card, get_data, num, pending_notice, sidebar_filters

st.title("📊 ภาพรวมการดำเนินงาน")
t, daily, p, imports = get_data()
df, d, month = sidebar_filters(t, daily)
k = calc.kpis(df, d, p)
st.caption(f"ข้อมูล: {'ทุกเดือน' if month == 'ทุกเดือน' else month} · {k['days']} วัน · {k['rows']:,} แถว "
           "(1 แถว = พนักงาน 1 คน ทำงาน 1 วัน)")

c = st.columns(4)
card(c[0], "🚚 รถที่วิ่งเฉลี่ยต่อวัน", f"{k['active_avg']:,.0f} / {k['fleet']:,.0f} คัน",
     f"สูงสุด {k['active_max']:,.0f} คัน/วัน")
card(c[1], "📈 อัตราการใช้รถ", num(k["util"], 1, "%"), "รถที่วิ่ง ÷ รถทั้งหมดของบริษัท", "good")
card(c[2], "🛣️ ระยะทางรวม", num(k["km"], 0, " กม."), f"{k['trips']:,.0f} เที่ยว · {k['drops']:,.0f} จุดส่ง")
card(c[3], "🌿 การปล่อย CO₂e", num(k["co2"] / 1000 if k["co2"] else None, 1, " ตัน"),
     f"น้ำมัน {num(k['fuel_l'], 0, ' ลิตร')}", "good")
c = st.columns(4)
card(c[0], "💵 รายได้ (ค่าสมมติ)", baht(k["revenue"]),
     "ค่าเที่ยว × จำนวนเที่ยว" if p.get("trip_price") else "ยังไม่ได้กำหนดค่าเที่ยว", "muted")
card(c[1], "🧾 ต้นทุนรวม", baht(k["cost"]), f"ตาม E-Billing {baht(k['payment'])}", "warn")
card(c[2], "💰 กำไรสุทธิ", baht(k["profit"]), "หลังหักต้นทุนรถว่าง " + baht(k["idle"]),
     "good" if (k["profit"] or 0) >= 0 else "bad")
card(c[3], "⏱️ OT รวม", num(k["ot"], 0, " ชม."), f"อนุมัติ {num(k['ot_appr'], 0, ' ชม.')}", "warn")
pending_notice(p)

left, right = st.columns(2)
with left:
  st.markdown("#### รถที่วิ่งต่อวัน เทียบกับรถทั้งหมด")
  fig = go.Figure()
  fig.add_bar(x=d["Work_Date"], y=d["Active_Vehicles"], name="รถที่วิ่ง", marker_color=COLORS["primary"])
  fig.add_scatter(x=d["Work_Date"], y=d["Fleet_Total"], name="รถทั้งหมด", mode="lines",
                  line=dict(color=COLORS["bad"], dash="dash"))
  fig.update_layout(height=320, yaxis_title="คัน", legend=dict(orientation="h", y=1.12), **PLOT)
  st.plotly_chart(fig, width="stretch")
with right:
  st.markdown("#### ค่าใช้จ่ายตาม E-Billing รายวัน")
  g = df.groupby("Work_Date")[["Vehicle_Fee", "Fuel_Fee", "OT_Fee", "Incentive"]].sum().reset_index()
  fig = go.Figure()
  for col, name, color in [("Vehicle_Fee", "ค่ารถ", "#2563EB"), ("Fuel_Fee", "ค่าน้ำมัน", "#D97706"),
                           ("OT_Fee", "ค่าโอที", "#DC2626"), ("Incentive", "Incentive", "#16A34A")]:
    fig.add_bar(x=g["Work_Date"], y=g[col], name=name, marker_color=color)
  fig.update_layout(barmode="stack", height=320, yaxis_title="บาท", legend=dict(orientation="h", y=1.12), **PLOT)
  st.plotly_chart(fig, width="stretch")

st.markdown("#### การทำงานตามช่วงกะ")
s = df.groupby("Shift_Group").agg(n=("Username", "size"), ot=("OT_Hrs", "mean"),
                                  hrs=("Work_Hrs", "mean")).reset_index()
s.columns = ["ช่วงกะ", "พนักงาน-วัน", "OT เฉลี่ย (ชม./วัน)", "ชั่วโมงทำงานเฉลี่ย (ชม./วัน)"]
st.dataframe(s.round(2), hide_index=True, width="stretch")
