import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import calculations as calc
import database as db
from common import COLORS, PLOT, baht, fuel_notice, get_data, kpi, num, sidebar_filters, th_month

st.title("🌿 น้ำมันและคาร์บอน")
t, o, p = get_data()
df, do, months, whole = sidebar_filters(t, o)
k = calc.summarize(df, do, p, months, whole)
fuel_notice(k)
fuel = k["fuel_cost"] if pd.notna(k["fuel_cost"]) else 0
prices = df.groupby("Year_Month")["Fuel_Price"].first()
rows = "\n".join(f"| {th_month(m_)} | {g['Fuel_L'].sum():,.2f} | {prices[m_]:.2f} | {g['Fuel_Cost_THB'].sum():,.2f} |"
                 for m_, g in df.groupby("Year_Month"))

st.markdown("##### เชื้อเพลิง (ค่าประมาณจากระยะทาง)")
c = st.columns(2)
kpi(c[0], "liters", "⛽ ปริมาณการใช้เชื้อเพลิง", num(k["fuel_l"], 0, " ลิตร"), f"ระยะทาง ÷ {p['km_per_l']:g} กม./ลิตร", f"""
**ทำไมเป็นค่าประมาณ:** บริษัทไม่มีบันทึกการเติมน้ำมันจริง จึงประมาณจากระยะทาง

**สูตร:** ปริมาณเชื้อเพลิง = ระยะทาง ÷ {p['km_per_l']:g} กม./ลิตร
= {k['km']:,.2f} ÷ {p['km_per_l']:g} = **{k['fuel_l']:,.2f} ลิตร**

อัตรา {p['km_per_l']:g} กม./ลิตร บริษัทกำหนด สอดคล้องกับกรมการขนส่งทางบก (2560) ที่ 10.5–11.73 กม./ลิตร
""")
kpi(c[1], "fuelcost", "💸 ค่าน้ำมัน", baht(k["fuel_cost"]), "ลิตร × ราคาดีเซลเฉลี่ยรายเดือน", f"""
**สูตร:** ค่าน้ำมัน = ปริมาณเชื้อเพลิง × ราคาดีเซลเฉลี่ยของเดือนนั้น

| เดือน | ลิตร | บาท/ลิตร | บาท |
|---|---:|---:|---:|
{rows}

**รวม {fuel:,.2f} บาท** · ราคาดีเซล B7 ของ ปตท. เขตกรุงเทพฯ ([🔗 ดูราคาน้ำมัน ปตท.]({db.FUEL_URL})) แก้ไขได้ที่หน้าตั้งค่าพารามิเตอร์
""", "warn")

st.markdown("##### ก๊าซเรือนกระจก (Carbon Footprint)")
c = st.columns(3)
kpi(c[0], "co2", "🌿 ปริมาณการปล่อยรวม", num(k["co2"] / 1000, 2, " ตัน CO₂e"), f"{num(k['co2_trip'], 2)} กก./เที่ยว", f"""
**วิธี:** Fuel-Based Method ตาม IPCC (2006)

**สูตร:** CO₂e = ปริมาณเชื้อเพลิง × ค่าการปล่อย (EF)
= {k['fuel_l']:,.2f} × {p['ef_diesel']} = **{k['co2']:,.2f} กก. ({k['co2'] / 1000:,.2f} ตัน)**

**ค่า EF 2.7406 kgCO₂e/ลิตร** จาก อบก. (ฉบับปรับปรุง เม.ย. 2565) อ้างอิง IPCC
""", "good")
kpi(c[1], "co2km", "📏 ต่อกิโลเมตร", num(k["co2_km"], 3, " กก. CO₂e"), "ใช้เทียบประสิทธิภาพ", f"""
**สูตร:** CO₂e ต่อกิโลเมตร = CO₂e รวม ÷ ระยะทางรวม
= {k['co2']:,.2f} ÷ {k['km']:,.2f} = **{k['co2_km']:,.3f} กก./กม.**

ค่านี้เท่ากับ {p['ef_diesel']} ÷ {p['km_per_l']:g} ทุกเดือน เพราะใช้อัตราสิ้นเปลืองคงที่
""", "good")
kpi(c[2], "reduce", "🎯 ศักยภาพลดการปล่อย", num(k["reduction"] / 1000, 2, " ตัน CO₂e"), "จากระยะทางที่เกินแผน", f"""
**ความหมาย:** ถ้ารถวิ่งตามระยะทางที่วางแผนไว้ จะลดการปล่อยได้ประมาณเท่าไหร่

1. ระยะเกินแผน = ระยะทางจริง − ระยะทางตามแผน (เฉพาะเที่ยวที่เกิน) รวม **{k['excess_km']:,.2f} กม.**
2. ศักยภาพลด = {k['excess_km']:,.2f} ÷ {p['km_per_l']:g} × {p['ef_diesel']} = **{k['reduction']:,.2f} กก.**

ไม่นับ {k['no_plan']:,} เที่ยวที่ไม่มีระยะตามแผน
""", "good")
st.info("ℹ️ ศักยภาพลดการปล่อยเป็น **การประเมินเบื้องต้น ไม่ใช่คาร์บอนเครดิต** เพราะไม่ได้ขึ้นทะเบียนโครงการ T-VER "
        "ไม่ได้ใช้ระเบียบวิธีที่ได้รับการรับรอง และไม่ผ่านการทวนสอบจากผู้ประเมินภายนอก")

with st.expander("ดูแนวโน้มรายเดือน (ทั้งบริษัท)"):
  m = calc.monthly(t, o, p)
  x = m["Year_Month"].map(th_month)
  fig = go.Figure()
  fig.add_bar(x=x, y=m["co2"] / 1000, name="CO₂e (ตัน)", marker_color=COLORS["good"])
  fig.add_bar(x=x, y=m["reduction"] / 1000, name="ศักยภาพลด (ตัน)", marker_color=COLORS["muted"])
  fig.update_layout(barmode="group", height=320, yaxis_title="ตัน CO₂e", legend=dict(orientation="h", y=1.15), **PLOT)
  st.plotly_chart(fig, width="stretch")
