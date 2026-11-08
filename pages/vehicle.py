import plotly.graph_objects as go
import streamlit as st

import calculations as calc
from common import COLORS, PLOT, get_data, kpi, num, sidebar_filters

st.title("🚚 ยานพาหนะ")
st.caption("ข้อมูลไม่มีทะเบียนรถ จึงนับรถที่วิ่งต่อวันจากรหัสพนักงานขับรถที่ไม่ซ้ำกันในแต่ละวัน")
t, o, p = get_data()
df, do, months, whole = sidebar_filters(t, o)
d = calc.daily(df, p)
avg, util = d["Active"].mean(), d["Utilization"].mean()

c = st.columns(3)
kpi(c[0], "fleet", "🚛 รถทั้งหมด", f"{p['fleet_total']:.0f} คัน", "ตั้งค่าไว้ในระบบ", f"""
จำนวนรถทั้งหมด **{p['fleet_total']:.0f} คัน** เป็นค่าที่บริษัทกำหนดให้ใช้ในโครงงาน
ตั้งค่าไว้ในหน้า **ตั้งค่าพารามิเตอร์** ครั้งเดียว ไม่ต้องกรอกทุกครั้งที่นำเข้าข้อมูล

ใช้เป็นตัวหารของอัตราการใช้รถ และใช้คิดค่าซ่อมบำรุงของกองรถ
""", "muted")
kpi(c[1], "active", "🚚 รถที่วิ่งเฉลี่ยต่อวัน", num(avg, 1, " คัน"),
    f"ต่ำสุด {num(d['Active'].min())} · สูงสุด {num(d['Active'].max())} คัน", f"""
**วิธีนับ:** ข้อมูลไม่มีทะเบียนรถ จึงนับ **รหัสพนักงานขับรถที่ไม่ซ้ำกันในแต่ละวัน**
(ถือว่าคนขับ 1 คน = รถ 1 คันต่อวัน)

1. นับรถที่วิ่งของแต่ละวัน ({len(d)} วัน)
2. เฉลี่ยทุกวัน = **{avg:,.1f} คัน**
""")
kpi(c[2], "util", "📈 อัตราการใช้รถ", num(util, 1, "%"), "รถที่วิ่ง ÷ รถทั้งหมด", f"""
**สูตร:** อัตราการใช้รถ = รถที่วิ่งในวันนั้น ÷ รถทั้งหมด × 100 แล้วเฉลี่ยทุกวัน

= {avg:,.1f} ÷ {p['fleet_total']:.0f} × 100 ≈ **{util:,.1f}%**

ถ้าต่ำ แปลว่ามีรถจอดว่างมาก แต่ยังต้องจ่ายค่าเสื่อมและประกันของรถทุกคัน
""", "good")
if not whole:
  st.info("กรองโซน/สาขาอยู่ — อัตราการใช้รถยังเทียบกับรถทั้งหมดของบริษัท จึงต่ำกว่าภาพรวม")

st.markdown("#### จำนวนรถที่วิ่งต่อวัน เทียบกับรถทั้งหมด")
fig = go.Figure()
fig.add_bar(x=d["Trip_Date"], y=d["Active"], name="รถที่วิ่ง", marker_color=COLORS["primary"],
            customdata=d["Utilization"], hovertemplate="%{x|%d/%m/%Y}<br>%{y} คัน (%{customdata:.1f}%)<extra></extra>")
fig.add_hline(y=p["fleet_total"], line_dash="dash", line_color=COLORS["bad"],
              annotation_text=f"รถทั้งหมด {p['fleet_total']:.0f} คัน")
fig.update_layout(height=360, yaxis_title="คัน", **PLOT)
st.plotly_chart(fig, width="stretch")

with st.expander("ดูตารางรายวัน"):
  st.dataframe(d.assign(Trip_Date=d["Trip_Date"].dt.strftime("%Y-%m-%d")).rename(columns={
      "Trip_Date": "วันที่", "Trips": "เที่ยววิ่ง", "Active": "รถที่วิ่ง (คัน)", "km": "ระยะทาง (กม.)",
      "Utilization": "อัตราการใช้รถ (%)", "km_per_vehicle": "กม./คัน/วัน"}).style.format(precision=1, thousands=","),
      hide_index=True, width="stretch")
