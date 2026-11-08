import plotly.graph_objects as go
import streamlit as st

import calculations as calc
from common import COLORS, PLOT, baht, card, delta, fuel_notice, get_data, num, sidebar_filters, th_month

st.title("📊 ภาพรวมการดำเนินงาน")
t, o, p = get_data()
df, do, months, whole = sidebar_filters(t, o)
k = calc.summarize(df, do, p, months, whole)
m = calc.monthly(t, o, p)
prev = None
if len(months) == 1:
  i = list(m["Year_Month"]).index(months[0])
  prev = m.iloc[i - 1] if i > 0 else None
pv = (lambda key: prev[key]) if prev is not None else (lambda key: None)

st.caption(f"ข้อมูล: {th_month(months[0]) if len(months) == 1 else 'ทุกเดือน'} · {k['days']} วัน · "
           f"{k['trips']:,} เที่ยว")

st.markdown("##### ด้านการดำเนินงาน")
c = st.columns(4)
card(c[0], "🧾 จำนวนเที่ยววิ่ง", num(k["trips"], 0, " เที่ยว"), delta(k["trips"], pv("trips")))
card(c[1], "🛣️ ระยะทางรวม", num(k["km"], 0, " กม."), f"เฉลี่ย {num(k['km_avg'], 2)} กม./เที่ยว")
card(c[2], "📦 จำนวนจุดส่ง", num(k["drops"], 0, " จุด"), delta(k["drops"], pv("drops")))
card(c[3], "🚚 รถที่วิ่งเฉลี่ยต่อวัน", f"{num(k['active_avg'], 0)} / {k['fleet']:.0f} คัน",
     f"อัตราการใช้รถ {num(k['util'], 1, '%')}", "good")

st.markdown("##### ด้านต้นทุนและกำไร")
c = st.columns(4)
card(c[0], "💵 รายได้ (ยอด E-Billing)", baht(k["revenue"]), delta(k["revenue"], pv("revenue")))
card(c[1], "🧮 ต้นทุนรวม 3 หมวด", baht(k["cost"]), f"{baht(k['cost_trip'])}/เที่ยว · {num(k['cost_km'], 2)} บาท/กม.",
     "warn")
card(c[2], "💰 กำไรสุทธิ", baht(k["profit"]), f"อัตรากำไรสุทธิ {num(k['margin'], 1, '%')}",
     "good" if k["profit"] >= 0 else "bad")
card(c[3], "⏱️ ชั่วโมงทำงานล่วงเวลา", num(k["ot_hrs"], 0, " ชม."), "ชั่วโมงที่อนุมัติ", "warn")

st.markdown("##### ด้านเชื้อเพลิงและสิ่งแวดล้อม")
c = st.columns(4)
card(c[0], "⛽ ปริมาณเชื้อเพลิง (ประมาณ)", num(k["fuel_l"], 0, " ลิตร"), f"ระยะทาง ÷ {p['km_per_l']:g} กม./ลิตร")
card(c[1], "💸 ค่าน้ำมัน", baht(k["fuel_cost"]), "ลิตร × ราคาดีเซลเฉลี่ยรายเดือน", "warn")
card(c[2], "🌿 ก๊าซเรือนกระจก", num(k["co2"] / 1000, 1, " ตัน CO₂e"), f"{num(k['co2_trip'], 2)} กก./เที่ยว", "good")
card(c[3], "🎯 ศักยภาพลดการปล่อย", num(k["reduction"] / 1000, 2, " ตัน CO₂e"), "จากระยะทางที่เกินแผน", "good")
fuel_notice(k)

st.markdown("#### แนวโน้มรายเดือน")
fig = go.Figure()
fig.add_bar(x=m["Year_Month"].map(th_month), y=m["revenue"], name="รายได้", marker_color=COLORS["primary"])
fig.add_bar(x=m["Year_Month"].map(th_month), y=m["cost"], name="ต้นทุนรวม", marker_color=COLORS["muted"])
fig.add_scatter(x=m["Year_Month"].map(th_month), y=m["profit"], name="กำไรสุทธิ", mode="lines+markers",
                line=dict(color=COLORS["good"], width=3))
fig.update_layout(barmode="group", height=360, yaxis_title="บาท", legend=dict(orientation="h", y=1.12), **PLOT)
st.plotly_chart(fig, width="stretch")

tb = m[["Year_Month", "trips", "km", "active_avg", "util", "revenue", "cost", "profit", "margin", "co2"]].copy()
for col in ["trips", "revenue", "profit"]:
  v = list(tb[col])
  tb[f"{col}_chg"] = [None] + [calc.pct_change(a, b) for a, b in zip(v[1:], v[:-1])]
tb["Year_Month"] = tb["Year_Month"].map(th_month)
tb["co2"] = tb["co2"] / 1000
st.dataframe(tb.rename(columns={
    "Year_Month": "เดือน", "trips": "เที่ยว", "km": "ระยะทาง (กม.)", "active_avg": "รถที่วิ่ง/วัน",
    "util": "อัตราการใช้รถ (%)", "revenue": "รายได้", "cost": "ต้นทุนรวม", "profit": "กำไรสุทธิ",
    "margin": "อัตรากำไร (%)", "co2": "CO₂e (ตัน)", "trips_chg": "เที่ยว เปลี่ยนแปลง (%)",
    "revenue_chg": "รายได้ เปลี่ยนแปลง (%)", "profit_chg": "กำไร เปลี่ยนแปลง (%)"}).style.format(precision=1,
                                                                                         thousands=","),
    hide_index=True, width="stretch")
st.caption("อัตราการเปลี่ยนแปลง (%) = (ค่าเดือนนี้ − ค่าเดือนก่อน) ÷ ค่าเดือนก่อน × 100 · "
           "ตารางนี้ใช้ข้อมูลทั้งบริษัท ไม่ขึ้นกับตัวกรองโซน/สาขา")
