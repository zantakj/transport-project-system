import plotly.graph_objects as go
import streamlit as st

import importer as im
from common import PLOT, get_data, info, th_month, to_display

st.title("🧪 ตรวจคุณภาพข้อมูล")
st.caption("ตามตารางที่ 3.2 · ทำเครื่องหมายไว้ ไม่ลบทิ้ง")

t, o, p = get_data()
months = sorted(t["Year_Month"].unique())
month = st.selectbox("เดือน", ["ทุกเดือน"] + months, index=0, format_func=th_month)
df = t if month == "ทุกเดือน" else t[t["Year_Month"] == month]

q = im.quality_summary(df)
q = q[~q["รหัส"].isin(["MISSING_KEY", "DUP_TRIP"])]  # ไม่มีวันที่/รหัสซ้ำ ถูกคัดออกตั้งแต่ตอนนำเข้า
clean = (df["Flags"] == "").mean() * 100

c = st.columns([1, 1, 1])
c[0].metric("จำนวนเที่ยวทั้งหมด", f"{len(df):,}")
c[1].metric("เที่ยวที่ไม่พบปัญหา", f"{clean:.1f}%")
info(c[2], "rules", "เกณฑ์ตรวจคุณภาพข้อมูล (ตารางที่ 3.2)", "\n".join(
    ["| มิติ | สิ่งที่ตรวจ | การจัดการ |", "|---|---|---|"] +
    [f"| {d} | {l} | {a} |" for l, d, a in im.FLAGS.values()]) +
    "\n\nเที่ยวที่ไม่มีวันที่/รหัสคนขับ/รหัสสาขา และรหัสเที่ยวซ้ำ จะถูกคัดออกตั้งแต่ตอนนำเข้า",
    "ⓘ ดูเกณฑ์ตรวจทั้งหมด")

# รวมตามมิติคุณภาพ แล้วเรียงแบบพาเรโต
dim = q.groupby("มิติคุณภาพ")["จำนวนเที่ยว"].sum().sort_values(ascending=False)
dim = dim[dim > 0]
if len(dim):
  st.markdown("#### ปัญหาตามมิติคุณภาพ (พาเรโต)")
  cum = dim.cumsum() / dim.sum() * 100
  fig = go.Figure()
  fig.add_bar(x=dim.index, y=dim.values, text=dim.values, name="จำนวนเที่ยว", marker_color="#2563EB")
  fig.add_scatter(x=dim.index, y=cum.values, yaxis="y2", mode="lines+markers", name="ร้อยละสะสม",
                  line=dict(color="#DC2626"))
  fig.update_layout(height=380, yaxis_title="จำนวนเที่ยว", legend=dict(orientation="h", y=1.12),
                    yaxis2=dict(overlaying="y", side="right", range=[0, 105], title="ร้อยละสะสม", ticksuffix="%"),
                    **PLOT)
  st.plotly_chart(fig, width="stretch")

with st.expander("ดูรายละเอียดแยกตามประเภทปัญหา"):
  found = q[q["จำนวนเที่ยว"] > 0].sort_values("จำนวนเที่ยว", ascending=False)
  st.dataframe(found.drop(columns="รหัส"), hide_index=True, width="stretch")
  code = st.selectbox("ดูเที่ยวที่มีปัญหา", found["รหัส"], format_func=lambda c: im.FLAGS[c][0]) if len(found) else None
  if code:
    rows = df[df["Flags"].str.contains(rf"\b{code}\b")]
    cols = ["Trip_ID", "Trip_Date", "Driver_Code", "Branch_Code", "Distance_km", "Planned_Distance_km", "Drops_Raw",
            "Revenue_THB"]
    rows = rows[[c for c in cols if c in rows]]
    rows = rows.assign(Trip_Date=rows["Trip_Date"].dt.strftime("%Y-%m-%d"))
    st.dataframe(to_display(rows).rename(columns={"Drops_Raw": "จุดส่ง"}), hide_index=True, width="stretch")
