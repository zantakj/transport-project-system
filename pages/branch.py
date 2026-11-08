import plotly.express as px
import streamlit as st

import calculations as calc
from common import PLOT, get_data, info, sidebar_filters

st.title("🏬 วิเคราะห์ตามสาขา")
st.caption("ข้อมูลไม่มีเส้นทาง จึงเปรียบเทียบตามสาขาต้นทางและโซนแทน")
t, o, p = get_data()
df, do, months, whole = sidebar_filters(t, o)

c = st.columns([1, 2, 1])
by = c[0].radio("เปรียบเทียบตาม", ["Branch_Code", "Zone"], horizontal=True,
                format_func={"Branch_Code": "สาขา", "Zone": "โซน"}.get)
METRICS = {"Trips": "จำนวนเที่ยว", "Revenue": "รายได้ (บาท)", "Profit": "กำไรสุทธิ (บาท)", "CO2": "CO₂e (กก.)"}
metric = c[1].selectbox("ตัวชี้วัด", list(METRICS), format_func=METRICS.get)
info(c[2], "branch", "การคำนวณรายสาขา", f"""
แต่ละสาขา/โซนรวมค่าจากเที่ยววิ่งของสาขานั้น

- **รายได้** = ยอด E-Billing ของเที่ยวในสาขา (+ รายการที่ไม่ผูกกับเที่ยวที่ระบุสาขา)
- **ต้นทุน** = ค่าจ้าง + OT + ค่าน้ำมัน + **ค่าซ่อมบำรุงที่ปันส่วนให้เที่ยวของสาขานั้น**
  (ค่าซ่อมบำรุงกองรถต่อวัน ÷ จำนวนเที่ยวทั้งหมดในวันนั้น แล้วรวมเฉพาะเที่ยวของสาขา)
- **กำไรสุทธิ** = รายได้ − ต้นทุน · **อัตรากำไร** = กำไร ÷ รายได้ × 100
- **CO₂e** = ระยะทาง ÷ {p['km_per_l']:g} × {p['ef_diesel']}

ผลรวมทุกสาขาจึงใกล้เคียงกับภาพรวม แต่อาจต่างเล็กน้อย เพราะภาพรวมคิดค่าซ่อมบำรุงทุกวันในเดือน
(รวมวันที่ไม่มีเที่ยววิ่ง)
""", "ⓘ วิธีคำนวณ")

g = calc.group_summary(df, do, p, by)
name = "สาขา" if by == "Branch_Code" else "โซน"
top = g.sort_values(metric, ascending=False).head(15)
fig = px.bar(top, x=by, y=metric, text_auto=".3s",
             color=top[metric].map(lambda v: "กำไร" if v >= 0 else "ขาดทุน") if metric == "Profit" else None,
             color_discrete_map={"กำไร": "#16A34A", "ขาดทุน": "#DC2626"},
             color_discrete_sequence=["#2563EB"])
fig.update_layout(height=380, xaxis_title=name, yaxis_title=METRICS[metric], showlegend=False, **PLOT)
st.plotly_chart(fig, width="stretch")
if len(g) > 15:
  st.caption(f"แสดง 15 อันดับแรกจาก {len(g)} {name}")

tbl = g[[by, "Trips", "km", "Revenue", "Cost", "Profit", "Margin"]].sort_values("Trips", ascending=False)
st.dataframe(tbl.rename(columns={by: name, "Trips": "เที่ยว", "km": "ระยะทาง (กม.)", "Revenue": "รายได้",
                                 "Cost": "ต้นทุนรวม", "Profit": "กำไรสุทธิ", "Margin": "อัตรากำไร (%)"})
             .style.format({"เที่ยว": "{:,.0f}", "ระยะทาง (กม.)": "{:,.0f}", "รายได้": "{:,.0f}", "ต้นทุนรวม": "{:,.0f}",
                            "กำไรสุทธิ": "{:,.0f}", "อัตรากำไร (%)": "{:.1f}"}),
             hide_index=True, width="stretch")
