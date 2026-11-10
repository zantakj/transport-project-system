import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import calculations as calc
from common import (CAT_COLORS, COLORS, PLOT, baht, fuel_notice, get_data, info, kpi, num, sidebar_filters,
                    th_month)

st.title("💰 ต้นทุนและกำไร")
t, o, p = get_data()
df, do, months, whole = sidebar_filters(t, o)
k = calc.summarize(df, do, p, months, whole)
fuel_notice(k)
fuel = k["fuel_cost"] if pd.notna(k["fuel_cost"]) else 0
day_cost = calc.fleet_day_cost(p)
maint_how = (f"{p['fleet_total']:.0f} คัน × ({p['dep_day']:,.2f} + {p['ins_year']:,.0f} ÷ 365) × {k['maint_days']} วัน"
             if whole else "ส่วนที่ปันส่วนให้เที่ยววิ่งของโซน/สาขาที่เลือก")
DEDUCT = f"""
| รายการ | วิธีคำนวณ | บาท |
|---|---|---:|
| รายได้ | ยอด E-Billing (ไม่รวม Helper) | {k['revenue']:,.2f} |
| − ค่าจ้างพนักงานขับรถ | {p['wage_day']:,.0f} บาท/คน/วัน | {k['wage']:,.2f} |
| − ค่าทำงานล่วงเวลา | {k['ot_hrs']:,.1f} ชม. × {p['ot_rate']:,.0f} บาท | {k['ot_cost']:,.2f} |
| − ค่าน้ำมันเชื้อเพลิง | {k['fuel_l']:,.2f} ลิตร × ราคาดีเซลรายเดือน | {fuel:,.2f} |
| − ค่าซ่อมบำรุง | {maint_how} | {k['maint']:,.2f} |
| **= กำไรสุทธิ** | | **{k['profit']:,.2f}** |

อัตรากำไรสุทธิ = {k['profit']:,.2f} ÷ {k['revenue']:,.2f} × 100 = **{k['margin']:,.1f}%**

เป็นกำไรระดับการดำเนินงานขนส่ง ยังไม่หักค่าใช้จ่ายบริหารส่วนกลาง ดอกเบี้ย และภาษี
"""

c = st.columns(4)
kpi(c[0], "rev", "💵 รายได้", baht(k["revenue"]), f"{baht(k['rev_trip'])}/เที่ยว", f"""
**รายได้ = ยอด E-Billing** ที่บริษัทเรียกเก็บจากลูกค้า (ไม่รวม Helper)

= รายได้จากเที่ยววิ่ง {df['Revenue_THB'].sum():,.2f} + รายการที่ไม่ผูกกับเที่ยว {do['Revenue_THB'].sum():,.2f}
= **{k['revenue']:,.2f} บาท**

รายได้ต่อเที่ยว = {k['revenue']:,.2f} ÷ {k['trips']:,} = {k['rev_trip']:,.2f} บาท
""")
kpi(c[1], "cost", "🧮 ต้นทุนรวม", baht(k["cost"]), f"{baht(k['cost_trip'])}/เที่ยว · {num(k['cost_km'], 2)} บาท/กม.",
    f"""
| หมวด | บาท | สัดส่วน |
|---|---:|---:|
| ค่าจ้าง + ค่าทำงานล่วงเวลา | {k['labor']:,.2f} | {k['labor'] / k['cost'] * 100:.1f}% |
| ค่าน้ำมันเชื้อเพลิง | {fuel:,.2f} | {fuel / k['cost'] * 100:.1f}% |
| ค่าซ่อมบำรุง (ค่าเสื่อม + ประกัน) | {k['maint']:,.2f} | {k['maint'] / k['cost'] * 100:.1f}% |
| **รวม** | **{k['cost']:,.2f}** | 100% |

- ต้นทุนต่อเที่ยว = {k['cost']:,.2f} ÷ {k['trips']:,} = {k['cost_trip']:,.2f} บาท
- ต้นทุนต่อกิโลเมตร = {k['cost']:,.2f} ÷ {k['km']:,.2f} = {k['cost_km']:,.2f} บาท
""", "warn")
kpi(c[2], "profit", "💰 กำไรสุทธิ", baht(k["profit"]), "รายได้ − ต้นทุน 3 หมวด", DEDUCT,
    "good" if k["profit"] >= 0 else "bad")
kpi(c[3], "margin", "📊 อัตรากำไรสุทธิ", num(k["margin"], 1, "%"), "กำไรสุทธิ ÷ รายได้", f"""
**สูตร:** อัตรากำไรสุทธิ = กำไรสุทธิ ÷ รายได้ × 100

= {k['profit']:,.2f} ÷ {k['revenue']:,.2f} × 100 = **{k['margin']:,.1f}%**

บอกว่ารายได้ทุก 100 บาท เหลือเป็นกำไรกี่บาท
""", "good" if k["profit"] >= 0 else "bad")

left, right = st.columns([3, 2])
with left:
  h = st.columns([3, 2])
  h[0].markdown("#### กำไรสุทธิหักอะไรบ้าง")
  info(h[1], "deduct", "กำไรสุทธิหักอะไรบ้าง", DEDUCT, "ⓘ ดูตัวเลขทีละบรรทัด")
  steps = [("รายได้", k["revenue"]), ("ค่าจ้าง", -k["wage"]), ("ค่า OT", -k["ot_cost"]), ("ค่าน้ำมัน", -fuel),
           ("ค่าซ่อมบำรุง", -k["maint"])]
  fig = go.Figure(go.Waterfall(
      x=[s[0] for s in steps] + ["กำไรสุทธิ"], y=[s[1] for s in steps] + [k["profit"]],
      measure=["relative"] * 5 + ["total"],
      text=[f"{abs(v) / 1e6:,.2f} ล." for _, v in steps] + [f"{k['profit'] / 1e6:,.2f} ล."], textposition="outside",
      increasing=dict(marker_color=COLORS["primary"]), decreasing=dict(marker_color=COLORS["bad"]),
      totals=dict(marker_color=COLORS["good"] if k["profit"] >= 0 else COLORS["bad"])))
  fig.update_layout(height=380, yaxis_title="บาท", showlegend=False, **PLOT)
  st.plotly_chart(fig, width="stretch")
with right:
  st.markdown("#### สัดส่วนต้นทุน 3 หมวด")
  cats = pd.DataFrame({"หมวด": list(CAT_COLORS), "บาท": [k["labor"], fuel, k["maint"]]})
  fig = px.pie(cats, names="หมวด", values="บาท", hole=.5, color="หมวด", color_discrete_map=CAT_COLORS)
  fig.update_layout(height=380, legend=dict(orientation="h", y=-0.15), **PLOT)
  st.plotly_chart(fig, width="stretch")

with st.expander("ดูต้นทุนและกำไรรายเดือน (ทั้งบริษัท)"):
  m = calc.monthly(t, o, p)
  mt = m[["Year_Month", "trips", "revenue", "wage", "ot_cost", "fuel_cost", "maint", "profit", "margin"]].copy()
  mt["Year_Month"] = mt["Year_Month"].map(th_month)
  st.dataframe(mt.rename(columns={
      "Year_Month": "เดือน", "trips": "เที่ยว", "revenue": "รายได้", "wage": "ค่าจ้าง", "ot_cost": "ค่า OT",
      "fuel_cost": "ค่าน้ำมัน", "maint": "ค่าซ่อมบำรุง", "profit": "กำไรสุทธิ", "margin": "อัตรากำไร (%)"})
      .style.format({c_: "{:,.0f}" for c_ in ["เที่ยว", "รายได้", "ค่าจ้าง", "ค่า OT", "ค่าน้ำมัน", "ค่าซ่อมบำรุง",
                                                "กำไรสุทธิ"]} | {"อัตรากำไร (%)": "{:.1f}"}), hide_index=True,
      width="stretch")
  st.caption(f"ค่าซ่อมบำรุงกองรถ {day_cost:,.2f} บาท/วัน")
