import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import calculations as calc
from common import PLOT, baht, card, get_data, num, pending_notice, sidebar_filters

st.title("💰 ต้นทุนและกำไร")
t, daily, p, imports = get_data()
df, d, month = sidebar_filters(t, daily)
k = calc.kpis(df, d, p)
miss = pending_notice(p)

with st.expander("📐 สูตรกำไรสุทธิที่ระบบใช้", expanded=False):
  st.markdown("""
| รายการ | วิธีคำนวณ | ที่มา |
|---|---|---|
| **รายได้** | ค่าเที่ยว × จำนวนเที่ยว (เฉพาะแถวคนขับ) | ค่าเที่ยวเป็น **ค่าสมมติ** |
| − ค่าใช้จ่ายตาม E-Billing | ยอดรวมทั้งหมด = ค่ารถ + ค่าน้ำมัน + ค่าโอที + Incentive + อื่น ๆ − ค่าปรับ | ข้อมูลจริงจากไฟล์บริษัท |
| − ค่าซ่อมบำรุง/ยาง | ระยะทาง × บาท/กม. | พารามิเตอร์ |
| − ค่าเสื่อมราคา | (ราคาทุน − ซาก) ÷ (อายุ × 12) ÷ วันในเดือน ต่อรถ 1 คัน-วัน | ระบบคำนวณ |
| − ประกัน/ภาษีรถ | ต่อปี ÷ 365 ต่อรถ 1 คัน-วัน | พารามิเตอร์ |
| − ต้นทุนรถว่าง | (รถทั้งหมด − รถที่วิ่ง) × (ค่าเสื่อม + ประกัน) ต่อวัน | ระบบคำนวณ |
| **= กำไรสุทธิ** | ก่อนภาษีเงินได้นิติบุคคล | |

ค่าน้ำมันรวมอยู่ในยอดรวมทั้งหมดแล้ว จึงไม่หักซ้ำ
""")

c = st.columns(4)
card(c[0], "รายได้ (ค่าสมมติ)", baht(k["revenue"]), "", "muted")
card(c[1], "ต้นทุนรวม (รถที่วิ่ง)", baht(k["cost"]), f"{num(k['cost'] / k['km'] if k['km'] else None, 2)} บาท/กม.", "warn")
card(c[2], "ต้นทุนรถว่าง", baht(k["idle"]), "ค่าเสื่อม + ประกันของรถที่ไม่ได้วิ่ง", "warn")
card(c[3], "กำไรสุทธิ", baht(k["profit"]), "ยังไม่หัก: " + ", ".join(miss) if miss else "หักครบทุกรายการ",
     "good" if (k["profit"] or 0) >= 0 else "bad")

parts = {"ค่ารถ": df["Vehicle_Fee"].sum(), "ค่าน้ำมัน": df["Fuel_Fee"].sum(), "ค่าโอที": df["OT_Fee"].sum(),
         "Incentive": df["Incentive"].sum(),
         "อื่น ๆ (Night load, ค่าใช้จ่ายอื่น, กะเช้าตรู่, Incentive รายเดือน)":
             df[["Night_Load", "Other_Exp_VAT", "Other_Exp_NonVAT", "Exp_VAT", "Exp_NonVAT", "Early_Shift_Fee",
                 "Incentive_Monthly"]].sum().sum(),
         "ค่าปรับ (หัก)": df["Penalty"].sum(),
         "ค่าซ่อมบำรุง/ยาง": df["Maintenance_THB"].sum(min_count=1), "ค่าเสื่อมราคา": df["Depreciation_THB"].sum(min_count=1),
         "ประกัน/ภาษีรถ": df["Insurance_THB"].sum(min_count=1), "ต้นทุนรถว่าง": k["idle"]}
tbl = pd.DataFrame({"รายการ": parts.keys(), "บาท": parts.values()})
tbl["สถานะ"] = tbl["บาท"].map(lambda v: "รอข้อมูลบริษัท" if pd.isna(v) else "")

left, right = st.columns([1.2, 1])
with left:
  st.markdown("#### จากรายได้สู่กำไรสุทธิ (Waterfall)")
  if pd.notna(k["revenue"]):
    items = [(n, -v) for n, v in parts.items() if pd.notna(v) and v != 0]
    fig = go.Figure(go.Waterfall(
        x=["รายได้"] + [n.split(" (")[0] for n, _ in items] + ["กำไรสุทธิ"],
        y=[k["revenue"]] + [v for _, v in items] + [0],
        measure=["absolute"] + ["relative"] * len(items) + ["total"]))
    fig.update_layout(height=380, yaxis_title="บาท", **PLOT)
    st.plotly_chart(fig, width="stretch")
  else:
    st.info("กราฟนี้จะแสดงเมื่อกำหนดค่าเที่ยวที่ลูกค้าจ่ายแล้ว")
with right:
  st.markdown("#### โครงสร้างต้นทุน")
  st.dataframe(tbl.assign(บาท=tbl["บาท"].map(baht)), hide_index=True, width="stretch")

st.markdown("#### ต้นทุนต่อหน่วย")
drv = df[df["Position"] == "Driver"]
u = st.columns(4)
u[0].metric("ต้นทุน/กม.", num(k["cost"] / k["km"] if k["km"] else None, 2, " บาท"))
u[1].metric("ต้นทุน/เที่ยว", num(k["cost"] / k["trips"] if k["trips"] else None, 0, " บาท"))
u[2].metric("ต้นทุน/จุดส่ง", num(k["cost"] / k["drops"] if k["drops"] else None, 1, " บาท"))
u[3].metric("ต้นทุน/รถ-วัน", num(k["cost"] / drv["Vehicle_Day"].sum() if drv["Vehicle_Day"].sum() else None, 0, " บาท"))

st.markdown("#### OT: ชั่วโมงที่ขอ เทียบกับที่อนุมัติ (รายสาขา 15 อันดับแรก)")
ot = df.groupby("Store")[["OT_Hrs", "OT_Request_Hrs", "OT_Approved_Hrs"]].sum().nlargest(15, "OT_Hrs").reset_index()
fig = px.bar(ot.melt(id_vars="Store", var_name="ประเภท", value_name="ชั่วโมง").replace(
    {"OT_Hrs": "OT ที่เกิดขึ้น", "OT_Request_Hrs": "OT ที่ขอ", "OT_Approved_Hrs": "OT ที่อนุมัติ"}),
    x="Store", y="ชั่วโมง", color="ประเภท", barmode="group")
fig.update_layout(height=340, xaxis_title="", legend_title="", **PLOT)
st.plotly_chart(fig, width="stretch")
