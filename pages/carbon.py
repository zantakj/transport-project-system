import plotly.graph_objects as go
import streamlit as st

import calculations as calc
from common import COLORS, PLOT, baht, card, fuel_notice, get_data, num, sidebar_filters, th_month

st.title("🌿 น้ำมันและคาร์บอน")
t, o, p = get_data()
df, do, months, whole = sidebar_filters(t, o)
k = calc.summarize(df, do, p, months, whole)
fuel_notice(k)

st.markdown("##### เชื้อเพลิง (ค่าประมาณจากระยะทาง — บริษัทไม่มีบันทึกการเติมน้ำมันจริง)")
c = st.columns(3)
card(c[0], "ปริมาณการใช้เชื้อเพลิง", num(k["fuel_l"], 2, " ลิตร"),
     f"{num(k['km'], 0)} กม. ÷ {p['km_per_l']:g} กม./ลิตร")
card(c[1], "ค่าน้ำมัน", baht(k["fuel_cost"]), "ลิตร × ราคาดีเซลเฉลี่ยของเดือนนั้น", "warn")
card(c[2], "ค่าน้ำมันต่อกิโลเมตร", num((k["fuel_cost"] or 0) / k["km"], 2, " บาท/กม."), "")

st.markdown("##### ก๊าซเรือนกระจก (Carbon Footprint)")
c = st.columns(4)
card(c[0], "ปริมาณการปล่อยรวม", num(k["co2"] / 1000, 2, " ตัน CO₂e"), f"{num(k['co2'], 2)} กก.", "good")
card(c[1], "ต่อกิโลเมตร", num(k["co2_km"], 3, " กก. CO₂e"), "", "good")
card(c[2], "ต่อจุดส่ง", num(k["co2_drop"], 3, " กก. CO₂e"), "", "good")
card(c[3], "ต่อเที่ยว", num(k["co2_trip"], 2, " กก. CO₂e"), "", "good")

st.markdown("##### ศักยภาพลดการปล่อยจากระยะทางที่เกินแผน")
c = st.columns(3)
card(c[0], "ระยะทางที่เกินแผนรวม", num(k["excess_km"], 0, " กม."), "เฉพาะเที่ยวที่วิ่งเกินระยะตามแผน", "warn")
card(c[1], "ศักยภาพลดการปล่อย", num(k["reduction"] / 1000, 2, " ตัน CO₂e"),
     f"= {num(k['excess_km'], 0)} ÷ {p['km_per_l']:g} × {p['ef_diesel']}", "good")
card(c[2], "เที่ยวที่ไม่มีระยะตามแผน", num(k["no_plan"], 0, " เที่ยว"), "ไม่นำมาคำนวณศักยภาพลด", "muted")
st.info("ℹ️ ค่านี้เป็น **การประเมินเบื้องต้น** ของผลกระทบจากระยะทางที่เกินแผน **ไม่ใช่คาร์บอนเครดิต** ที่บริษัทได้รับหรือซื้อขายได้ "
        "เพราะยังไม่ได้ขึ้นทะเบียนโครงการ T-VER ไม่ได้ใช้ระเบียบวิธีที่ได้รับการรับรอง และไม่ได้ผ่านการทวนสอบโดยผู้ประเมินภายนอก")

st.markdown("#### แนวโน้มรายเดือน (ทั้งบริษัท)")
m = calc.monthly(t, o, p)
x = m["Year_Month"].map(th_month)
fig = go.Figure()
fig.add_bar(x=x, y=m["co2"] / 1000, name="CO₂e (ตัน)", marker_color=COLORS["good"])
fig.add_bar(x=x, y=m["reduction"] / 1000, name="ศักยภาพลด (ตัน)", marker_color=COLORS["muted"])
fig.add_scatter(x=x, y=m["fuel_l"], name="เชื้อเพลิง (ลิตร)", yaxis="y2", mode="lines+markers",
                line=dict(color=COLORS["warn"], width=3))
fig.update_layout(barmode="group", height=360, yaxis_title="ตัน CO₂e", legend=dict(orientation="h", y=1.15),
                  yaxis2=dict(overlaying="y", side="right", title="ลิตร"), **PLOT)
st.plotly_chart(fig, width="stretch")

with st.expander("วิธีคำนวณและแหล่งอ้างอิง"):
  st.markdown(f"""
**วิธีอิงปริมาณเชื้อเพลิง (Fuel-Based Method)** ตาม IPCC (2006) สำหรับการเผาไหม้เชื้อเพลิงจากแหล่งเคลื่อนที่

1. ปริมาณเชื้อเพลิง (ลิตร) = ระยะทาง (กม.) ÷ {p['km_per_l']:g} กม./ลิตร
2. ปริมาณการปล่อย (กก. CO₂e) = ปริมาณเชื้อเพลิง (ลิตร) × {p['ef_diesel']} กก. CO₂e/ลิตร
3. ศักยภาพลดการปล่อย (กก. CO₂e) = ผลรวมของ (ระยะทางจริง − ระยะทางตามแผน) เฉพาะเที่ยวที่เกินแผน ÷ {p['km_per_l']:g} × {p['ef_diesel']}

ค่า EF 2.7406 มาจากตารางค่าการปล่อยก๊าซเรือนกระจกสำหรับการคำนวณคาร์บอนฟุตพริ้นท์ขององค์กร
ฉบับปรับปรุงเดือนเมษายน พ.ศ. 2565 ขององค์การบริหารจัดการก๊าซเรือนกระจก (องค์การมหาชน) ซึ่งอ้างอิงค่าจาก IPCC
""")
