import plotly.express as px
import streamlit as st

import calculations as calc
from common import PLOT, get_data, sidebar_filters

st.title("🏬 วิเคราะห์ตามสาขา")
st.caption("ข้อมูลไม่มีเส้นทาง จึงเปรียบเทียบตามสาขาต้นทางและโซนพื้นที่แทน · "
           "ค่าซ่อมบำรุงในหน้านี้เป็นส่วนที่ปันส่วนให้เที่ยววิ่งของแต่ละสาขา/โซน")
t, o, p = get_data()
df, do, months, whole = sidebar_filters(t, o)

by = st.radio("เปรียบเทียบตาม", ["Branch_Code", "Zone"], horizontal=True,
              format_func={"Branch_Code": "สาขา", "Zone": "โซน"}.get)
g = calc.group_summary(df, do, p, by).sort_values("Trips", ascending=False)
name = "สาขา" if by == "Branch_Code" else "โซน"
metric = st.selectbox("ตัวชี้วัด", ["Trips", "km", "km_trip", "Drops", "Revenue", "Cost", "Profit", "Margin", "Cost_km",
                                    "CO2", "CO2_km"],
                      format_func={"Trips": "จำนวนเที่ยว", "km": "ระยะทางรวม (กม.)", "km_trip": "ระยะทางเฉลี่ย (กม./เที่ยว)",
                                   "Drops": "จำนวนจุดส่ง", "Revenue": "รายได้ (บาท)", "Cost": "ต้นทุนรวม (บาท)",
                                   "Profit": "กำไรสุทธิ (บาท)", "Margin": "อัตรากำไรสุทธิ (%)",
                                   "Cost_km": "ต้นทุนต่อ กม. (บาท)", "CO2": "CO₂e (กก.)", "CO2_km": "CO₂e ต่อ กม. (กก.)"}.get)
top = g.sort_values(metric, ascending=False).head(20)
fig = px.bar(top, x=by, y=metric, color="Profit" if metric != "Profit" else None,
             color_continuous_scale="RdYlGn", text_auto=".3s")
fig.update_layout(height=380, xaxis_title=name, yaxis_title="", coloraxis_colorbar_title="กำไร", **PLOT)
st.plotly_chart(fig, width="stretch")
if len(g) > 20:
  st.caption(f"แสดง 20 อันดับแรกจาก {len(g)} {name}")

st.dataframe(g.rename(columns={
    by: name, "Trips": "เที่ยว", "km": "ระยะทาง (กม.)", "Drops": "จุดส่ง", "Revenue": "รายได้", "Labor": "ค่าจ้าง+OT",
    "Fuel": "ค่าน้ำมัน", "Maint": "ค่าซ่อมบำรุง", "CO2": "CO₂e (กก.)", "Excess": "ระยะเกินแผน (กม.)", "Cost": "ต้นทุนรวม",
    "Profit": "กำไรสุทธิ", "Margin": "อัตรากำไร (%)", "km_trip": "กม./เที่ยว", "Cost_km": "ต้นทุน/กม.",
    "CO2_km": "CO₂e/กม."}).style.format(precision=1, thousands=","), hide_index=True, width="stretch")
