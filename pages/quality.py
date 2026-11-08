import plotly.graph_objects as go
import streamlit as st

import database as db
import importer as im
from common import PLOT, get_data, th_month, to_display

st.title("🧪 ตรวจคุณภาพข้อมูล")
st.caption("ผลตรวจตามเกณฑ์ในตารางที่ 3.2 — รายการที่พบปัญหาถูกทำเครื่องหมายไว้ ไม่ได้ลบทิ้ง "
           "และไม่นำไปคำนวณเฉพาะตัวชี้วัดที่ได้รับผลกระทบ")

t, o, p = get_data()
months = sorted(t["Year_Month"].unique())
month = st.selectbox("เดือน", ["ทุกเดือน"] + months, index=0, format_func=th_month)
df = t if month == "ทุกเดือน" else t[t["Year_Month"] == month]

q = im.quality_summary(df)
q = q[~q["รหัส"].isin(["MISSING_KEY", "DUP_TRIP"])]  # ไม่มีวันที่/รหัสซ้ำ ถูกคัดออกตั้งแต่ตอนนำเข้า
clean = (df["Flags"] == "").mean() * 100
c = st.columns(3)
c[0].metric("จำนวนเที่ยวทั้งหมด", f"{len(df):,}")
c[1].metric("เที่ยวที่ไม่พบปัญหา", f"{clean:.1f}%")
c[2].metric("ประเภทปัญหาที่พบ", f"{(q['จำนวนเที่ยว'] > 0).sum()} ประเภท")

found = q[q["จำนวนเที่ยว"] > 0].sort_values("จำนวนเที่ยว", ascending=False)
if len(found):
  # แผนภูมิพาเรโต: เรียงจากมากไปน้อย + ร้อยละสะสม
  found = found.assign(สะสม=found["จำนวนเที่ยว"].cumsum() / found["จำนวนเที่ยว"].sum() * 100)
  st.markdown("#### แผนภูมิพาเรโตของปัญหาคุณภาพข้อมูล")
  labels = found["ปัญหา"].str.replace(r"\s*\(.*\)", "", regex=True)
  fig = go.Figure()
  fig.add_bar(x=labels, y=found["จำนวนเที่ยว"], name="จำนวนเที่ยว", marker_color="#2563EB",
              text=found["จำนวนเที่ยว"], customdata=found["มิติคุณภาพ"],
              hovertemplate="%{x}<br>%{y:,} เที่ยว<br>มิติ: %{customdata}<extra></extra>")
  fig.add_scatter(x=labels, y=found["สะสม"], yaxis="y2", mode="lines+markers", name="ร้อยละสะสม",
                  line=dict(color="#DC2626"))
  fig.update_layout(height=440, xaxis_title="", yaxis_title="จำนวนเที่ยว", legend=dict(orientation="h", y=1.12),
                    yaxis2=dict(overlaying="y", side="right", range=[0, 105], title="ร้อยละสะสม", ticksuffix="%"),
                    **PLOT)
  st.plotly_chart(fig, width="stretch")
st.dataframe(q.drop(columns="รหัส"), hide_index=True, width="stretch")

st.markdown("#### ดูเที่ยวที่มีปัญหา")
code = st.selectbox("ประเภทปัญหา", found["รหัส"], format_func=lambda c: im.FLAGS[c][0]) if len(found) else None
if code:
  rows = df[df["Flags"].str.contains(rf"\b{code}\b")]
  cols = ["Trip_ID", "Trip_Date", "Driver_Code", "Branch_Code", "Zone", "Distance_km", "Planned_Distance_km",
          "Revenue_THB", "EBilling_Status", "Distance_Source", "Source_Sheet", "Source_Row"]
  st.dataframe(to_display(rows[[c for c in cols if c in rows]]), hide_index=True, width="stretch")

log = db.load_quality_log()
if len(log):
  st.markdown("#### บันทึกการจัดการข้อมูลตอนแปลงเป็นรายเที่ยว")
  st.caption("จากชีต Data_Quality_Log ของไฟล์ที่นำเข้า — ระบุแถวต้นฉบับ ปัญหา และวิธีจัดการ")
  lg = log if month == "ทุกเดือน" else log[log["Year_Month"] == month]
  s = lg.groupby(["Issue", "Action"]).size().reset_index(name="จำนวนรายการ").sort_values("จำนวนรายการ",
                                                                                     ascending=False)
  st.dataframe(s.rename(columns={"Issue": "ปัญหา", "Action": "การจัดการ"}), hide_index=True, width="stretch")
