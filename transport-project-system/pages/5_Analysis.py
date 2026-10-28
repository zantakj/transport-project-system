import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import calculations as calc
import database as db
from common import PLOT, get_data, sidebar_filters

st.title("📈 Advanced Route, Pricing & Carbon Analysis")
st.caption("วิเคราะห์ความคุ้มค่ารายเส้นทาง จุดคุ้มทุน ความสัมพันธ์ราคากับระยะทาง และการปล่อยคาร์บอนแยกประเภทรถ")

tables, trips, fixed = get_data()
df, vt = sidebar_filters(trips)
done = df[df["Job_Status"] == "Completed"]

tab1, tab2, tab3 = st.tabs(["📍 เส้นทาง & จุดคุ้มทุน", "💲 ราคา vs ระยะทาง", "🌿 คาร์บอน"])

with tab1:
  target = st.slider("อัตรากำไรเป้าหมาย (%) สำหรับคำนวณราคาแนะนำ", 0, 40, 15)
  r = calc.summarize(df, ["Route_Code", "Vehicle_Type"])
  r = r.merge(tables["Routes"][["Route_Code", "Destination_Province_TH", "One_Way_km"]], on="Route_Code", how="left")
  r["Avg_Price"] = r["Revenue_THB"] / r["Trips"]
  r["Break_Even_Price"] = r["Total_Cost_THB"] / r["Trips"]          # ราคาต่ำสุดที่ไม่ขาดทุน
  r["Recommended_Price"] = r["Break_Even_Price"] / (1 - target / 100)
  r["Price_Gap"] = r["Avg_Price"] - r["Recommended_Price"]
  show = r[["Route_Code", "Destination_Province_TH", "Vehicle_Type", "One_Way_km", "Trips", "Avg_Price",
            "Break_Even_Price", "Recommended_Price", "Price_Gap", "Profit_THB", "Profit_Margin"]]
  st.dataframe(db.to_display(show.round(2)).rename(columns={
      "Avg_Price": "ราคาเฉลี่ยปัจจุบัน/เที่ยว", "Break_Even_Price": "ราคาจุดคุ้มทุน/เที่ยว",
      "Recommended_Price": f"ราคาแนะนำ (Margin {target}%)", "Price_Gap": "ส่วนต่างจากราคาแนะนำ"}),
      width="stretch", hide_index=True)
  below = r[r["Price_Gap"] < 0]
  if len(below):
    st.warning(f"⚠️ {len(below)} คู่เส้นทาง/ประเภทรถ มีราคาต่ำกว่าราคาที่ให้ Margin {target}%: "
               + ", ".join(f"{a} ({b})" for a, b in zip(below["Route_Code"], below["Vehicle_Type"])))
  fig = px.bar(r, x="Route_Code", y="Profit_Margin", color="Vehicle_Type", barmode="group",
               title="อัตรากำไรสุทธิ (%) รายเส้นทาง แยกประเภทรถ", template=PLOT["template"])
  fig.add_hline(y=target, line_dash="dash", annotation_text=f"เป้าหมาย {target}%")
  st.plotly_chart(fig, width="stretch")
  st.caption("ราคาจุดคุ้มทุน = ต้นทุนรวมเฉลี่ยต่อเที่ยว · ราคาแนะนำ = จุดคุ้มทุน ÷ (1 − Margin เป้าหมาย)")

with tab2:
  reg = calc.price_regression(df)
  st.markdown("**สมการถดถอยเชิงเส้น (Linear Regression): ราคา = ค่าคงที่ + อัตรา × ระยะทางเที่ยวเดียว**")
  st.dataframe(reg.rename(columns={"Vehicle_Type": "ประเภทรถ", "Base_THB": "ค่าคงที่ (บาท/เที่ยว)",
               "THB_per_km": "อัตรา (บาท/กม.)", "R2": "R²", "n": "จำนวนเที่ยว"}).round(3),
               width="stretch", hide_index=True)
  fig = px.scatter(done, x="One_Way_km", y="Agreed_Price_THB", color="Vehicle_Type", opacity=0.5,
                   labels={"One_Way_km": "ระยะทางเที่ยวเดียว (กม.)", "Agreed_Price_THB": "ค่าขนส่ง (บาท)"},
                   title="ความสัมพันธ์ระหว่างราคาและระยะทาง", template=PLOT["template"])
  xs = np.linspace(0, done["One_Way_km"].max() * 1.05, 50)
  for _, row in reg.iterrows():
    fig.add_trace(go.Scatter(x=xs, y=row.Base_THB + row.THB_per_km * xs, mode="lines",
                             name=f"เส้นแนวโน้ม {row.Vehicle_Type}", line=dict(dash="dash")))
  st.plotly_chart(fig, width="stretch")
  st.caption("R² ใกล้ 1 แปลว่าราคาอธิบายได้ด้วยระยะทางเกือบทั้งหมด (ราคาสัมพันธ์กับระยะทาง)")

with tab3:
  s = calc.summarize(df, "Vehicle_Type")
  tk = done.groupby("Vehicle_Type")["Ton_km"].sum() if "Ton_km" in done.columns else None
  if tk is not None:
    s["gCO2_per_ton_km"] = s["CO2_kg"] * 1000 / s["Vehicle_Type"].map(tk)
  ef = tables["Emission_Factors"]
  st.markdown("**CO₂ (กก.) = ปริมาณน้ำมัน (ลิตร) × Emission Factor ของเชื้อเพลิง**")
  st.dataframe(ef, width="stretch", hide_index=True)
  cols = ["Vehicle_Type", "Trips", "Distance_km", "Fuel_Liters", "km_per_L", "CO2_kg", "CO2_kg_per_km"] + \
         (["gCO2_per_ton_km"] if tk is not None else [])
  st.dataframe(db.to_display(s[cols].round(3)).rename(columns={
      "CO2_kg_per_km": "CO₂ กก./กม.", "gCO2_per_ton_km": "CO₂ กรัม/ตัน-กม. (ความเข้มข้นการปล่อย)"}),
      width="stretch", hide_index=True)
  l, r2 = st.columns(2)
  with l:
    fig = px.bar(s, x="Vehicle_Type", y="CO2_kg_per_km", title="CO₂ ต่อกิโลเมตร (กก./กม.)", template=PLOT["template"])
    st.plotly_chart(fig, width="stretch")
  with r2:
    if tk is not None:
      fig = px.bar(s, x="Vehicle_Type", y="gCO2_per_ton_km", title="CO₂ ต่อการขนส่ง 1 ตัน-กม. (กรัม)",
                   template=PLOT["template"])
      st.plotly_chart(fig, width="stretch")
  st.caption("รถใหญ่ปล่อย CO₂ ต่อ กม. มากกว่า แต่ขนสินค้าได้มากกว่า จึงอาจปล่อยต่อ ตัน-กม. น้อยกว่า "
             "(ใช้ตัดสินใจเลือกขนาดรถให้เหมาะกับน้ำหนักสินค้า)")
  m = done.groupby(["Year_Month", "Vehicle_Type"])["CO2_kg"].sum().reset_index()
  fig = px.line(m, x="Year_Month", y="CO2_kg", color="Vehicle_Type", markers=True,
                title="CO₂ รายเดือน (กก.)", template=PLOT["template"])
  st.plotly_chart(fig, width="stretch")
