import pandas as pd
import plotly.express as px
import streamlit as st

import calculations as calc
import database as db
from common import PLOT, baht, get_data, sidebar_filters

st.title("🎯 KPI & Cost Analytics")
st.caption("ต้นทุนดำเนินงานเต็มรูปแบบแยกตามประเภทรถ: ต้นทุนผันแปร (น้ำมัน ยาง น้ำมันเครื่อง ซ่อมบำรุง ทางด่วน เบี้ยเลี้ยง) "
           "+ ต้นทุนคงที่ (ค่าเสื่อม ประกัน เงินเดือนคนขับ ต้นทุนรถว่าง)")

tables, trips, fixed = get_data()
df, vt = sidebar_filters(trips)
done = df[df["Job_Status"] == "Completed"]

COST_ITEMS = {
    "Fuel_Cost_THB": "ค่าน้ำมัน", "Tire_Cost_THB": "ค่ายาง", "Oil_Cost_THB": "ค่าน้ำมันเครื่อง",
    "Repair_Cost_THB": "ค่าซ่อมบำรุง", "Toll_THB": "ค่าทางด่วน", "Driver_Allowance_THB": "เบี้ยเลี้ยงคนขับ",
    "Driver_Salary_THB": "เงินเดือนคนขับ", "Depreciation_THB": "ค่าเสื่อมราคา",
    "Insurance_THB": "ประกัน/ภาษี", "Idle_Cost_THB": "ต้นทุนรถว่าง/จอด",
}

# ---------- สรุป ----------
s = calc.summarize(df, "Vehicle_Type")
rev, cost = done["Revenue_THB"].sum(), done["Total_Cost_THB"].sum()
c = st.columns(4)
c[0].metric("รายได้รวม", baht(rev))
c[1].metric("ต้นทุนรวม", baht(cost))
c[2].metric("กำไรสุทธิ", baht(rev - cost), f"Margin {(rev-cost)/rev*100:.1f}%" if rev else None)
cm = rev - done["Variable_Cost_THB"].sum()
c[3].metric("กำไรส่วนเกิน (Contribution Margin)", baht(cm), f"{cm/rev*100:.1f}% ของรายได้" if rev else None, delta_color="off")

# ---------- ต้นทุนต่อ กม. ----------
st.markdown("#### 🛣️ ต้นทุนต่อกิโลเมตร แยกประเภทรถ")
per_km = done.groupby("Vehicle_Type")[list(COST_ITEMS) + ["Distance_km", "Revenue_THB"]].sum()
table = per_km[list(COST_ITEMS)].div(per_km["Distance_km"], axis=0)
table["ต้นทุนรวม/กม."] = table.sum(axis=1)
table["รายได้/กม."] = per_km["Revenue_THB"] / per_km["Distance_km"]
table["กำไร/กม."] = table["รายได้/กม."] - table["ต้นทุนรวม/กม."]
st.dataframe(table.rename(columns=COST_ITEMS).round(2), width="stretch")

l, r = st.columns(2)
with l:
  melted = (per_km[list(COST_ITEMS)].div(per_km["Distance_km"], axis=0)
            .rename(columns=COST_ITEMS).reset_index()
            .melt(id_vars="Vehicle_Type", var_name="รายการ", value_name="บาท/กม."))
  fig = px.bar(melted, x="Vehicle_Type", y="บาท/กม.", color="รายการ", title="โครงสร้างต้นทุนต่อ กม.",
               template=PLOT["template"])
  st.plotly_chart(fig, width="stretch")
with r:
  fig = px.bar(s, x="Vehicle_Type", y=["Revenue_THB", "Total_Cost_THB", "Profit_THB"], barmode="group",
               title="รายได้ ต้นทุน กำไร แยกประเภทรถ", template=PLOT["template"],
               labels={"value": "บาท", "variable": ""})
  st.plotly_chart(fig, width="stretch")

# ---------- Sensitivity analysis ----------
st.markdown("#### 🔬 วิเคราะห์ความอ่อนไหว (Sensitivity Analysis)")
st.caption("ถ้าราคาน้ำมันหรือค่าขนส่งเปลี่ยน กำไรจะเปลี่ยนเท่าไร — ต้นทุนส่วนอื่นคงเดิม")
a, b = st.columns(2)
fuel_chg = a.slider("ราคาน้ำมันเปลี่ยน (%)", -30, 50, 10, 5)
price_chg = b.slider("ค่าขนส่งเปลี่ยน (%)", -20, 20, 0, 1)
rows = []
for t, g in done.groupby("Vehicle_Type"):
  base = g["Profit_THB"].sum()
  new = g["Revenue_THB"].sum() * (1 + price_chg / 100) - g["Total_Cost_THB"].sum() - g["Fuel_Cost_THB"].sum() * fuel_chg / 100
  new_rev = g["Revenue_THB"].sum() * (1 + price_chg / 100)
  rows.append({"ประเภทรถ": t, "กำไรเดิม": base, "กำไรใหม่": new, "เปลี่ยนแปลง": new - base,
               "Margin เดิม %": base / g["Revenue_THB"].sum() * 100, "Margin ใหม่ %": new / new_rev * 100})
st.dataframe(pd.DataFrame(rows).round(2), width="stretch", hide_index=True)

# ---------- รายเที่ยว ----------
with st.expander("📋 ตารางคำนวณรายเที่ยว"):
  cols = ["Trip_ID", "Trip_Date", "Vehicle_Code", "Vehicle_Type", "Route_Code", "Distance_km"] + list(COST_ITEMS) + \
         ["Total_Cost_THB", "Revenue_THB", "Profit_THB", "Profit_Margin"]
  st.dataframe(db.to_display(done[cols].round(2).assign(Trip_Date=done["Trip_Date"].dt.date)), width="stretch", hide_index=True)

with st.expander("📐 สูตรที่ใช้คำนวณ"):
  st.markdown("""
- **ค่าน้ำมัน** = ลิตร × ราคาน้ำมัน ณ วันที่วิ่ง
- **ค่ายาง** = ระยะทาง × (จำนวนยาง × ราคายาง ÷ อายุยาง กม.)
- **ค่าน้ำมันเครื่อง** = ระยะทาง × (ค่าเปลี่ยน ÷ ระยะเปลี่ยน กม.)
- **ค่าซ่อมบำรุง** = ระยะทาง × บาท/กม.
- **ค่าเสื่อมราคา** = (ราคาซื้อ − มูลค่าซาก) ÷ อายุใช้งาน (เดือน) → ปันส่วนให้เที่ยวของรถคันนั้นตามสัดส่วนระยะทางในเดือน
- **ต้นทุนรถว่าง** = ต้นทุนคงที่ของรถที่ไม่มีเที่ยววิ่งในเดือนนั้น → ปันส่วนให้รถประเภทเดียวกันตามระยะทาง
- **Contribution Margin** = รายได้ − ต้นทุนผันแปร (เงินที่เหลือไว้จ่ายต้นทุนคงที่)
- **กำไรสุทธิ** = รายได้ − ต้นทุนผันแปร − ต้นทุนคงที่
""")
