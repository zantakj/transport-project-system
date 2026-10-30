import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import importer as im
from common import COLORS, PLOT, get_data, num, sidebar_filters, to_display

st.title("🚚 ยานพาหนะ")
t, daily, p, imports = get_data()
df, d, month = sidebar_filters(t, daily, positions=False)
drv = df[df["Position"] == "Driver"]

c = st.columns(4)
c[0].metric("รถที่วิ่งเฉลี่ยต่อวัน", num(d["Active_Vehicles"].mean(), 0, " คัน"))
c[1].metric("รถทั้งหมดของบริษัท", num(d["Fleet_Total"].max(), 0, " คัน"),
            help="กรอกตอนนำเข้าข้อมูลแต่ละเดือน (ค่าสมมติ 173 คัน รอบริษัทยืนยัน)")
c[2].metric("อัตราการใช้รถเฉลี่ย", num(d["Utilization"].mean(), 1, "%"))
vd = drv["Vehicle_Day"].sum()
c[3].metric("ระยะทางเฉลี่ยต่อคันต่อวัน", num(drv["Distance_km"].sum() / vd if vd else None, 1, " กม."))

st.markdown("#### อัตราการใช้รถรายวัน")
fig = go.Figure()
fig.add_scatter(x=d["Work_Date"], y=d["Utilization"], mode="lines+markers", name="อัตราการใช้รถ",
                line_color=COLORS["primary"])
fig.add_hline(y=100, line_dash="dash", line_color=COLORS["bad"])
fig.update_layout(height=300, yaxis_title="%", yaxis_range=[0, 110], **PLOT)
st.plotly_chart(fig, width="stretch")
st.caption("วิธีนับ: รถที่วิ่งในวันนั้น = จำนวนคนขับ (Position = Driver) ที่ไม่ซ้ำกันในวันนั้น "
           "เพราะคนขับหมุนเวียนกันตลอดเดือน จึงนับเป็นรายวัน ไม่ใช่รายเดือน")

left, right = st.columns(2)
with left:
  st.markdown("#### ระยะทางต่อคันต่อวัน (การกระจาย)")
  fig = px.histogram(drv[drv["Distance_km"] > 0], x="Distance_km", nbins=40, color_discrete_sequence=[COLORS["primary"]])
  fig.update_layout(height=300, xaxis_title="กม./วัน", yaxis_title="จำนวนรถ-วัน", **PLOT)
  st.plotly_chart(fig, width="stretch")
with right:
  st.markdown("#### ตามประเภทตู้ (จาก Data Master)")
  b = drv.groupby("Box_Type").agg(รถ_วัน=("Vehicle_Day", "sum"), ระยะทาง=("Distance_km", "sum")).reset_index()
  b.columns = ["ประเภทตู้", "รถ-วัน", "ระยะทาง (กม.)"]
  st.dataframe(b, hide_index=True, width="stretch")
  st.caption(f"แถวคนขับที่พบทะเบียนรถใน Data Master: {drv['Plate'].notna().mean() * 100:.0f}% "
             "— แถวที่เหลือแสดงเป็น 'ไม่ทราบ' จนกว่าบริษัทจะส่งรายชื่อรถครบทุกคัน")

st.markdown("#### สรุปรายทะเบียนรถ (เฉพาะที่พบใน Data Master)")
pl = (drv[drv["Plate"].notna()].groupby("Plate")
      .agg(Vehicle_Days=("Vehicle_Day", "sum"), Trips=("Trips", "sum"), Drops=("Drops", "sum"),
           Distance_km=("Distance_km", "sum"), Fuel_L=("Fuel_L", "sum"), CO2_kg=("CO2_kg", "sum"))
      .reset_index().sort_values("Distance_km", ascending=False))
pl.insert(0, "Plate_Masked", pl.pop("Plate").map(im.mask_plate))
st.dataframe(to_display(pl).round(1), hide_index=True, width="stretch")
st.caption(f"พบทะเบียนรถไม่ซ้ำกัน {len(pl)} คัน จาก Data Master")
