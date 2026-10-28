import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import calculations as calc
from common import PLOT, baht, get_data, sidebar_filters

st.markdown("""
<style>
.kpi-card{background:#1E293B;border:1px solid #334155;border-radius:12px;padding:16px;margin-bottom:12px}
.kpi-title{font-size:.8rem;font-weight:600;color:#94A3B8;margin-bottom:6px}
.kpi-value{font-size:1.6rem;font-weight:700;color:#F8FAFC}
.kpi-sub{font-size:.8rem;color:#34D399;margin-top:4px}
</style>""", unsafe_allow_html=True)


def card(col, title, value, sub=""):
  col.markdown(f'<div class="kpi-card"><div class="kpi-title">{title}</div>'
               f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>',
               unsafe_allow_html=True)


st.title("📊 Executive Transportation Dashboard")
st.caption("ภาพรวมรายได้ ต้นทุนเต็มรูปแบบ (ผันแปร + คงที่ + รถว่าง) กำไรสุทธิ การใช้รถ และการปล่อยคาร์บอน")

tables, trips, fixed = get_data()
df, vt = sidebar_filters(trips)
done = df[df["Job_Status"] == "Completed"]

rev, cost = done["Revenue_THB"].sum(), done["Total_Cost_THB"].sum()
profit, km = rev - cost, done["Distance_km"].sum()
fuel_only_margin = (rev - done["Fuel_Cost_THB"].sum()) / rev * 100 if rev else 0
margin = profit / rev * 100 if rev else 0
util, workdays = calc.fleet_utilization(df, tables["Vehicles"])
if vt != "ทั้งหมด":
  util = util[util["Vehicle_Type"] == vt]
cancel_rate = (df["Job_Status"] == "Cancelled").mean() * 100

c = st.columns(4)
card(c[0], "💰 รายได้รวม", baht(rev), f"{len(done):,} เที่ยว · {km:,.0f} กม.")
card(c[1], "🧾 ต้นทุนรวม (เต็มรูปแบบ)", baht(cost),
     f"ผันแปร {baht(done['Variable_Cost_THB'].sum())} · คงที่ {baht(done['Fixed_Cost_THB'].sum())}")
card(c[2], "📈 กำไรสุทธิ", baht(profit), f"Margin {margin:.1f}%")
card(c[3], "🛣️ ต้นทุน / รายได้ ต่อ กม.", f"{cost/km:,.2f} / {rev/km:,.2f}" if km else "-", "บาท/กม.")
c = st.columns(4)
card(c[0], "⏱️ ส่งตรงเวลา (OTD)", f"{done['On_Time'].mean()*100:.1f}%", f"ยกเลิก {cancel_rate:.1f}%")
card(c[1], "🚚 อัตราการใช้รถ (Utilization)", f"{util['Utilization'].mean():.1f}%",
     f"รถทั้งหมด {len(util)} คัน · จอด/สำรอง {(util['Status'] != 'Active').sum()} คัน")
card(c[2], "🌿 การปล่อย CO₂", f"{done['CO2_kg'].sum()/1000:,.2f} ตัน",
     f"{done['CO2_kg'].sum()/km:,.3f} กก./กม." if km else "")
card(c[3], "⚠️ ต้นทุนรถว่าง/จอด", baht(done["Idle_Cost_THB"].sum()), "ค่าเสื่อม+ประกันของรถที่ไม่ได้วิ่ง")

st.info(f"💡 ถ้าคิดกำไรแบบ **รายได้ − ค่าน้ำมัน** อย่างเดียว จะได้ Margin **{fuel_only_margin:.1f}%** "
        f"แต่เมื่อคิดต้นทุนดำเนินงานครบ Margin จริงคือ **{margin:.1f}%**")

left, right = st.columns(2)
with left:
  st.markdown("#### 📈 รายได้ ต้นทุน และกำไรรายเดือน")
  m = done.groupby("Year_Month")[["Revenue_THB", "Variable_Cost_THB", "Fixed_Cost_THB", "Profit_THB"]].sum().reset_index()
  fig = go.Figure()
  fig.add_bar(x=m["Year_Month"], y=m["Variable_Cost_THB"], name="ต้นทุนผันแปร", marker_color="#F59E0B")
  fig.add_bar(x=m["Year_Month"], y=m["Fixed_Cost_THB"], name="ต้นทุนคงที่", marker_color="#EF4444")
  fig.add_scatter(x=m["Year_Month"], y=m["Revenue_THB"], name="รายได้", mode="lines+markers", line_color="#3B82F6")
  fig.add_scatter(x=m["Year_Month"], y=m["Profit_THB"], name="กำไรสุทธิ", mode="lines+markers", line_color="#10B981")
  fig.update_layout(barmode="stack", height=340, margin=dict(t=10, b=10, l=10, r=10),
                    legend=dict(orientation="h", y=1.1), yaxis_title="บาท", **PLOT)
  st.plotly_chart(fig, width="stretch")
with right:
  st.markdown("#### 🧾 โครงสร้างต้นทุน")
  parts = {"ค่าน้ำมัน": "Fuel_Cost_THB", "ค่ายาง": "Tire_Cost_THB", "ค่าน้ำมันเครื่อง": "Oil_Cost_THB",
           "ค่าซ่อมบำรุง": "Repair_Cost_THB", "ค่าทางด่วน": "Toll_THB", "เบี้ยเลี้ยงคนขับ": "Driver_Allowance_THB",
           "เงินเดือนคนขับ": "Driver_Salary_THB", "ค่าเสื่อมราคา": "Depreciation_THB",
           "ประกัน/ภาษี": "Insurance_THB", "ต้นทุนรถว่าง": "Idle_Cost_THB"}
  s = {k: done[v].sum() for k, v in parts.items()}
  fig = px.pie(names=list(s), values=list(s.values()), hole=0.5)
  fig.update_layout(height=340, margin=dict(t=10, b=10, l=10, r=10), **PLOT)
  st.plotly_chart(fig, width="stretch")
