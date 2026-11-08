import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import calculations as calc
from common import COLORS, PLOT, card, get_data, num, sidebar_filters

st.title("🚚 ยานพาหนะ")
st.caption("ข้อมูลไม่มีทะเบียนรถ จึงนับจำนวนรถที่วิ่งต่อวันจากรหัสพนักงานขับรถที่ไม่ซ้ำกันในแต่ละวัน "
           "(ถือว่าพนักงานขับรถ 1 คนขับรถ 1 คันต่อวัน)")
t, o, p = get_data()
df, do, months, whole = sidebar_filters(t, o)
d = calc.daily(df, p)

c = st.columns(4)
card(c[0], "รถทั้งหมด", f"{p['fleet_total']:.0f} คัน", "ตั้งค่าไว้ในระบบ (ไม่ต้องกรอกทุกครั้ง)", "muted")
card(c[1], "รถที่วิ่งเฉลี่ยต่อวัน", num(d["Active"].mean(), 1, " คัน"),
     f"ต่ำสุด {num(d['Active'].min())} · สูงสุด {num(d['Active'].max())} คัน")
card(c[2], "อัตราการใช้รถเฉลี่ย", num(d["Utilization"].mean(), 1, "%"), "รถที่วิ่ง ÷ รถทั้งหมด × 100", "good")
card(c[3], "ระยะทางต่อคันต่อวัน", num(d["km_per_vehicle"].mean(), 1, " กม."), "ระยะทางรวม ÷ รถที่วิ่ง")
if not whole:
  st.info("กรองโซน/สาขาอยู่ — อัตราการใช้รถยังเทียบกับรถทั้งหมดของบริษัท จึงต่ำกว่าภาพรวม")

st.markdown("#### จำนวนรถที่วิ่งต่อวัน เทียบกับรถทั้งหมด")
fig = go.Figure()
fig.add_bar(x=d["Trip_Date"], y=d["Active"], name="รถที่วิ่ง", marker_color=COLORS["primary"])
fig.add_hline(y=p["fleet_total"], line_dash="dash", line_color=COLORS["bad"],
              annotation_text=f"รถทั้งหมด {p['fleet_total']:.0f} คัน")
fig.update_layout(height=340, yaxis_title="คัน", **PLOT)
st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
  st.markdown("#### อัตราการใช้รถรายวัน (%)")
  fig = px.line(d, x="Trip_Date", y="Utilization", markers=True)
  fig.update_layout(height=300, xaxis_title="", yaxis_title="%", **PLOT)
  st.plotly_chart(fig, width="stretch")
with right:
  st.markdown("#### เฉลี่ยตามวันในสัปดาห์")
  names = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
  w = d.assign(wd=d["Trip_Date"].dt.dayofweek).groupby("wd")[["Active", "Trips"]].mean().reindex(range(7))
  w.index = names
  fig = go.Figure()
  fig.add_bar(x=w.index, y=w["Active"], name="รถที่วิ่ง (คัน)", marker_color=COLORS["primary"])
  fig.add_bar(x=w.index, y=w["Trips"], name="เที่ยววิ่ง", marker_color=COLORS["muted"])
  fig.update_layout(barmode="group", height=300, legend=dict(orientation="h", y=1.15), **PLOT)
  st.plotly_chart(fig, width="stretch")

st.markdown("#### สรุปรายวัน")
st.dataframe(d.assign(Trip_Date=d["Trip_Date"].dt.strftime("%Y-%m-%d")).rename(columns={
    "Trip_Date": "วันที่", "Trips": "เที่ยววิ่ง", "Active": "รถที่วิ่ง (คัน)", "km": "ระยะทาง (กม.)",
    "Utilization": "อัตราการใช้รถ (%)", "km_per_vehicle": "กม./คัน/วัน"}).style.format(precision=1, thousands=","),
    hide_index=True, width="stretch")
