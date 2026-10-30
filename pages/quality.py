import plotly.express as px
import streamlit as st

import importer as im
from common import PLOT, get_data, to_display

st.title("🧪 ตรวจคุณภาพข้อมูล")
st.caption("ผลตรวจตามมิติคุณภาพข้อมูล (ความครบถ้วน ความถูกต้อง ความสอดคล้อง ความสมเหตุสมผล ความไม่ซ้ำซ้อน ค่าผิดปกติ) "
           "— แถวที่มีปัญหาถูกทำเครื่องหมายไว้ ไม่ได้ลบทิ้ง")

t, daily, p, imports = get_data()
months = sorted(t["Year_Month"].unique())
month = st.selectbox("เดือน", months, index=len(months) - 1)
df = t[t["Year_Month"] == month]

q = im.quality_summary(df)
clean = (df["Flags"].isin(["", "NOT_IN_MASTER"])).mean() * 100
c = st.columns(3)
c[0].metric("จำนวนแถวทั้งหมด", f"{len(df):,}")
c[1].metric("แถวที่ไม่พบปัญหา", f"{clean:.1f}%", help="ไม่นับกรณีคนขับไม่อยู่ใน Data Master ซึ่งเป็นข้อจำกัดของชีต Master")
c[2].metric("ประเภทปัญหาที่พบ", f"{(q['จำนวนแถว'] > 0).sum()} ประเภท")

found = q[q["จำนวนแถว"] > 0].sort_values("จำนวนแถว")
fig = px.bar(found, x="จำนวนแถว", y="ปัญหา", color="มิติคุณภาพ", orientation="h", text="จำนวนแถว")
fig.update_layout(height=60 + 32 * len(found), yaxis_title="", legend_title="", **PLOT)
fig.update_yaxes(categoryorder="total ascending")
st.plotly_chart(fig, width="stretch")
st.dataframe(q, hide_index=True, width="stretch")

st.markdown("#### ดูแถวที่มีปัญหา")
code = st.selectbox("ประเภทปัญหา", found["รหัส"][::-1],
                    format_func=lambda c: f"{im.FLAGS[c][0]} ({c})") if len(found) else None
if code:
  rows = df[df["Flags"].str.contains(rf"\b{code}\b")]
  st.dataframe(to_display(rows[["Work_Date", "Store", "Zone", "Username", "Position", "Booking", "Shift_In",
                                "Distance_km", "Total_Payment", "EBilling_Status", "Remark", "Flags"]]),
               hide_index=True, width="stretch")
