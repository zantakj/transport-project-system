import plotly.express as px
import streamlit as st

import calculations as calc
import database as db
from common import PLOT, baht, get_data, sidebar_filters

st.title("🚛 Vehicle Performance Analytics")
st.caption("ประสิทธิภาพรายคัน รวมรถที่จอด/สำรอง — ค่าเสื่อมราคาคิดกับรถทุกคันในกองรถ")

tables, trips, fixed = get_data()
df, vt = sidebar_filters(trips)
months = df["Year_Month"].unique()
fx = fixed[fixed["Year_Month"].isin(months)]
if vt != "ทั้งหมด":
  fx = fx[fx["Vehicle_Type"] == vt]

util, workdays = calc.fleet_utilization(df, tables["Vehicles"])
done = df[df["Job_Status"] == "Completed"]
per_v = done.groupby("Vehicle_Code").agg(
    Trips=("Trip_ID", "count"), Distance_km=("Distance_km", "sum"), Fuel_Liters=("Fuel_Liters", "sum"),
    Revenue_THB=("Revenue_THB", "sum"), Variable_Cost_THB=("Variable_Cost_THB", "sum"),
    CO2_kg=("CO2_kg", "sum"))
own_fixed = fx.groupby("Vehicle_Code")[["Depreciation_THB", "Insurance_THB", "Driver_Salary_THB", "Fixed_Cost_THB"]].sum()
v = util.set_index("Vehicle_Code").join(per_v).join(own_fixed).fillna(0).reset_index()
v = v[v["Vehicle_Code"].isin(fx["Vehicle_Code"].unique())]
v["km_per_L"] = (v["Distance_km"] / v["Fuel_Liters"]).where(v["Fuel_Liters"] > 0)
# กำไรรายคัน = รายได้ − ต้นทุนผันแปร − ต้นทุนคงที่ของคันนั้นเอง (รถจอดจะติดลบเท่าค่าเสื่อม+ประกัน)
v["Profit_THB"] = v["Revenue_THB"] - v["Variable_Cost_THB"] - v["Fixed_Cost_THB"]

c = st.columns(4)
c[0].metric("รถทั้งหมด", f"{len(v)} คัน", f"Active {(v['Status']=='Active').sum()} · Standby {(v['Status']!='Active').sum()}", delta_color="off")
c[1].metric("อัตราการใช้รถเฉลี่ย", f"{v['Utilization'].mean():.1f}%", f"จาก {workdays} วันทำงาน", delta_color="off")
c[2].metric("ค่าเสื่อมราคารวม (ทั้งกองรถ)", baht(v["Depreciation_THB"].sum()))
idle = v[v["Trips"] == 0]
c[3].metric("ต้นทุนของรถที่ไม่ได้วิ่ง", baht(idle["Fixed_Cost_THB"].sum()), f"{len(idle)} คัน", delta_color="off")

st.markdown("#### 📋 สรุปรายคัน")
cols = ["Vehicle_Code", "Vehicle_Type", "Status", "Trips", "Distance_km", "Days_Used", "Utilization",
        "km_per_L", "Rated_km_per_L", "Revenue_THB", "Variable_Cost_THB", "Depreciation_THB",
        "Fixed_Cost_THB", "Profit_THB", "CO2_kg"]
st.dataframe(db.to_display(v[cols].round(2)).rename(columns={"Days_Used": "วันที่มีงาน (Days_Used)",
             "Utilization": "อัตราการใช้รถ % (Utilization)", "Rated_km_per_L": "km/L มาตรฐาน (Rated)"}),
             width="stretch", hide_index=True)

l, r = st.columns(2)
with l:
  fig = px.bar(v, x="Vehicle_Code", y="Utilization", color="Status", title="อัตราการใช้รถรายคัน (%)",
               color_discrete_map={"Active": "#3B82F6", "Standby": "#EF4444"}, **{"template": PLOT["template"]})
  st.plotly_chart(fig, width="stretch")
with r:
  t = calc.summarize(df, "Vehicle_Type")
  fig = px.bar(t, x="Vehicle_Type", y="km_per_L", text=t["km_per_L"].round(2),
               title="อัตราสิ้นเปลืองจริงเฉลี่ย (กม./ลิตร) แยกประเภทรถ", template=PLOT["template"])
  st.plotly_chart(fig, width="stretch")

with st.expander("📐 วิธีคำนวณค่าเสื่อมราคา (Straight-line method)"):
  st.markdown("""
**ค่าเสื่อมราคาต่อเดือน = (ราคาซื้อ − มูลค่าซาก) ÷ (อายุการใช้งาน × 12)**

คิดกับรถทุกคันในกองรถ ไม่ว่าจะวิ่งหรือจอด เพราะรถเสื่อมมูลค่าตามเวลา
รถที่เกินอายุการใช้งานแล้วจะไม่มีค่าเสื่อมเพิ่ม · ข้อมูลราคาซื้อ อายุ และมูลค่าซากอยู่ในชีต Vehicles
""")
