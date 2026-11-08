import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import calculations as calc
from common import CAT_COLORS, COLORS, PLOT, baht, card, fuel_notice, get_data, num, sidebar_filters, th_month

st.title("💰 ต้นทุนและกำไร")
t, o, p = get_data()
df, do, months, whole = sidebar_filters(t, o)
k = calc.summarize(df, do, p, months, whole)
fuel_notice(k)

c = st.columns(4)
card(c[0], "รายได้ (ยอด E-Billing)", baht(k["revenue"]), f"{baht(k['rev_trip'])}/เที่ยว")
card(c[1], "ต้นทุนรวม 3 หมวด", baht(k["cost"]), f"{baht(k['cost_trip'])}/เที่ยว · {num(k['cost_km'], 2)} บาท/กม.",
     "warn")
card(c[2], "กำไรสุทธิ", baht(k["profit"]), f"เฉลี่ย {baht(k['profit'] / k['trips'])}/เที่ยว",
     "good" if k["profit"] >= 0 else "bad")
card(c[3], "อัตรากำไรสุทธิ", num(k["margin"], 1, "%"), "กำไรสุทธิ ÷ รายได้ × 100",
     "good" if k["profit"] >= 0 else "bad")

st.markdown("#### กำไรสุทธิหักอะไรบ้าง")
steps = [("รายได้ (ยอด E-Billing)", k["revenue"]), ("ค่าจ้างพนักงานขับรถ", -k["wage"]),
         ("ค่าทำงานล่วงเวลา", -k["ot_cost"]), ("ค่าน้ำมันเชื้อเพลิง", -(k["fuel_cost"] or 0)),
         ("ค่าซ่อมบำรุง (ค่าเสื่อม + ประกัน)", -k["maint"])]
fig = go.Figure(go.Waterfall(
    x=[s[0] for s in steps] + ["กำไรสุทธิ"], y=[s[1] for s in steps] + [k["profit"]],
    measure=["absolute"] + ["relative"] * 4 + ["total"], text=[f"{abs(v) / 1e6:,.2f} ล้าน" for _, v in steps] +
    [f"{k['profit'] / 1e6:,.2f} ล้าน"], textposition="outside",
    increasing=dict(marker_color=COLORS["primary"]), decreasing=dict(marker_color=COLORS["bad"]),
    totals=dict(marker_color=COLORS["good"] if k["profit"] >= 0 else COLORS["bad"])))
fig.update_layout(height=400, yaxis_title="บาท", showlegend=False, **PLOT)
st.plotly_chart(fig, width="stretch")

tbl = pd.DataFrame([
    ["รายได้", "ยอด E-Billing (เที่ยววิ่ง + รายการที่ไม่ผูกกับเที่ยว ไม่รวม Helper)", k["revenue"]],
    ["− ค่าจ้างพนักงานขับรถ", f"{p['wage_day']:,.0f} บาท/คน/วัน", -k["wage"]],
    ["− ค่าทำงานล่วงเวลา", f"{num(k['ot_hrs'], 1)} ชม. ที่อนุมัติ × {p['ot_rate']:,.0f} บาท", -k["ot_cost"]],
    ["− ค่าน้ำมันเชื้อเพลิง", f"{num(k['fuel_l'], 2)} ลิตร × ราคาดีเซลเฉลี่ยรายเดือน", -(k["fuel_cost"] or 0)],
    ["− ค่าซ่อมบำรุง", (f"{p['fleet_total']:.0f} คัน × ({p['dep_day']:,.2f} + {p['ins_year']:,.0f} ÷ 365) × "
                       f"{k['maint_days']} วัน" if whole else "ส่วนที่ปันส่วนให้เที่ยววิ่งที่เลือก"), -k["maint"]],
    ["= กำไรสุทธิ", f"อัตรากำไรสุทธิ {num(k['margin'], 1, '%')}", k["profit"]],
], columns=["รายการ", "วิธีคำนวณ", "บาท"])
st.dataframe(tbl.style.format({"บาท": "{:,.2f}"}), hide_index=True, width="stretch")
st.caption("กำไรสุทธิในระบบเป็นกำไรระดับการดำเนินงานขนส่ง ก่อนหักค่าใช้จ่ายบริหารส่วนกลาง ดอกเบี้ย และภาษีเงินได้นิติบุคคล "
           "และไม่รวมรายได้และค่าจ้างของพนักงานประจำรถ (Helper)")

left, right = st.columns(2)
with left:
  st.markdown("#### โครงสร้างต้นทุน 3 หมวด")
  cats = pd.DataFrame({"หมวด": list(CAT_COLORS), "บาท": [k["labor"], k["fuel_cost"] or 0, k["maint"]]})
  fig = px.pie(cats, names="หมวด", values="บาท", hole=.5, color="หมวด", color_discrete_map=CAT_COLORS)
  fig.update_layout(height=340, legend=dict(orientation="h", y=-0.1), **PLOT)
  st.plotly_chart(fig, width="stretch")
with right:
  st.markdown("#### ต้นทุนต่อเที่ยวและต่อกิโลเมตร แยกหมวด")
  per = pd.DataFrame({"หมวด": list(CAT_COLORS),
                      "บาท/เที่ยว": [k["labor"] / k["trips"], (k["fuel_cost"] or 0) / k["trips"], k["maint"] / k["trips"]],
                      "บาท/กม.": [k["labor"] / k["km"], (k["fuel_cost"] or 0) / k["km"], k["maint"] / k["km"]]})
  per.loc[len(per)] = ["รวม", k["cost_trip"], k["cost_km"]]
  st.dataframe(per.style.format(precision=2, thousands=","), hide_index=True, width="stretch")
  st.markdown(f"**ค่าซ่อมบำรุงของกองรถต่อวัน** = {p['fleet_total']:.0f} × ({p['dep_day']:,.2f} + "
              f"{p['ins_year']:,.0f} ÷ 365) = **{baht(calc.fleet_day_cost(p), 2)}**")

st.markdown("#### แนวโน้มรายเดือน (ทั้งบริษัท)")
m = calc.monthly(t, o, p)
mm = m.melt(id_vars="Year_Month", value_vars=["labor", "fuel_cost", "maint"], var_name="หมวด", value_name="บาท")
mm["หมวด"] = mm["หมวด"].map(dict(zip(["labor", "fuel_cost", "maint"], CAT_COLORS)))
mm["Year_Month"] = mm["Year_Month"].map(th_month)
fig = px.bar(mm, x="Year_Month", y="บาท", color="หมวด", color_discrete_map=CAT_COLORS)
fig.add_scatter(x=m["Year_Month"].map(th_month), y=m["revenue"], name="รายได้", mode="lines+markers",
                line=dict(color=COLORS["primary"], width=3))
fig.update_layout(height=360, xaxis_title="", legend=dict(orientation="h", y=1.15), **PLOT)
st.plotly_chart(fig, width="stretch")
mt = m[["Year_Month", "trips", "revenue", "wage", "ot_cost", "fuel_cost", "maint", "profit", "margin",
        "cost_trip", "cost_km"]].copy()
mt["Year_Month"] = mt["Year_Month"].map(th_month)
st.dataframe(mt.rename(columns={
    "Year_Month": "เดือน", "trips": "เที่ยว", "revenue": "รายได้", "wage": "ค่าจ้าง", "ot_cost": "ค่า OT",
    "fuel_cost": "ค่าน้ำมัน", "maint": "ค่าซ่อมบำรุง", "profit": "กำไรสุทธิ", "margin": "อัตรากำไร (%)",
    "cost_trip": "ต้นทุน/เที่ยว", "cost_km": "ต้นทุน/กม."}).style.format(precision=2, thousands=","),
    hide_index=True, width="stretch")
