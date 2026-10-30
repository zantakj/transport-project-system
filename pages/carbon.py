import plotly.graph_objects as go
import streamlit as st

import calculations as calc
import database as db
from common import COLORS, PLOT, baht, card, get_data, num, sidebar_filters

st.title("🌿 น้ำมันและคาร์บอน")
t, daily, p, imports = get_data()
df, d, month = sidebar_filters(t, daily)
k = calc.kpis(df, d, p)
fuel = db.load_fuel_prices()
missing = sorted(set(df["Year_Month"]) - set(fuel["year_month"]))
if missing:
  st.warning("⏳ ยังไม่ได้กรอกราคาน้ำมันของเดือน " + ", ".join(missing) + " — กรอกได้ที่หน้า **ตั้งค่าพารามิเตอร์**")

c = st.columns(4)
card(c[0], "⛽ น้ำมันที่ใช้", num(k["fuel_l"], 0, " ลิตร"), "ค่าน้ำมัน ÷ ราคาน้ำมันต่อลิตร")
card(c[1], "📏 อัตราสิ้นเปลือง", num(k["km_per_L"], 2, " กม./ลิตร"), "อัตราตามสัญญาคิดเงิน (ดูหมายเหตุ)", "warn")
card(c[2], "🌿 CO₂e รวม", num(k["co2"] / 1000 if k["co2"] else None, 2, " ตัน"),
     f"{num(k['co2'] / k['km'] if k['co2'] and k['km'] else None, 3)} กก./กม. · "
     f"{num(k['co2'] / k['drops'] if k['co2'] and k['drops'] else None, 2)} กก./จุดส่ง", "good")
tver = p.get("tver_price")
red_t = (k["co2_red"] or 0) / 1000
card(c[3], "♻️ ศักยภาพลดคาร์บอน", num(red_t, 2, " ตัน"),
     f"มูลค่าประมาณการ {baht(red_t * tver) if tver else 'รอราคา T-VER'}", "primary")

st.markdown("#### CO₂e รายวัน")
g = df.groupby("Work_Date").agg(CO2=("CO2_kg", "sum"), km=("Distance_km", "sum")).reset_index()
fig = go.Figure()
fig.add_bar(x=g["Work_Date"], y=g["CO2"] / 1000, name="CO₂e (ตัน)", marker_color=COLORS["good"])
fig.add_scatter(x=g["Work_Date"], y=g["km"], name="ระยะทาง (กม.)", yaxis="y2", mode="lines",
                line_color=COLORS["primary"])
fig.update_layout(height=320, yaxis_title="ตัน CO₂e", legend=dict(orientation="h", y=1.12),
                  yaxis2=dict(overlaying="y", side="right", title="กม.", showgrid=False), **PLOT)
st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
  st.markdown("#### วิธีคำนวณ")
  st.markdown(f"""
**1) ปริมาณน้ำมัน** = ค่าน้ำมัน (บาท) ÷ ราคาน้ำมัน (บาท/ลิตร)

**2) CO₂e** = ลิตร × EF = ลิตร × **{p.get('ef_diesel')} kgCO₂e/ลิตร**
วิธี Fuel-based ตาม IPCC 2006 Guidelines Vol.2 บทที่ 3 (Mobile Combustion)
ค่า EF จากตารางค่าการปล่อยสำหรับ CFO ของ อบก. (น้ำมันดีเซล การเผาไหม้เคลื่อนที่)

**3) ศักยภาพลดคาร์บอน** = ระยะที่วิ่งเกินแผน ÷ กม./ลิตร × EF
ระยะเกินแผน = actual − planned (นับเฉพาะค่าบวก) รวม **{num(k['excess_km'], 0, ' กม.')}**
""")
with right:
  st.markdown("#### ข้อควรระวัง (สำหรับการนำเสนอ)")
  st.markdown("""
- **ค่าน้ำมันในไฟล์บริษัทคิดจาก ระยะทางที่จ่ายเงิน × อัตราบาท/กม. ตามสัญญา** (เช่น 4.18 บาท/กม. ใน มิ.ย.)
  ดังนั้น กม./ลิตร ที่ได้คือ "อัตราสิ้นเปลืองตามสัญญา" ไม่ใช่อัตราที่วัดจากการเติมน้ำมันจริง
  ถ้าบริษัทมีบันทึกการเติมน้ำมัน (ลิตร) จะคำนวณ CO₂e ได้แม่นยำขึ้น
- **ศักยภาพลดคาร์บอน ≠ คาร์บอนเครดิต** — การขายเป็นคาร์บอนเครดิตต้องขึ้นทะเบียนโครงการ T-VER กับ อบก.
  มีค่าฐาน (Baseline) และผ่านการตรวจสอบ (Verification) มูลค่าที่แสดงจึงเป็นเพียงประมาณการ
- แถวเด็กรถ (Helper) ไม่มีค่าน้ำมัน จึงไม่ถูกนับซ้ำ
""")

st.markdown("#### ตามช่วงกะ")
s = calc.group_summary(df, "Shift_Group")[["Shift_Group", "Vehicle_Days", "Distance_km", "Fuel_L", "CO2_kg", "CO2_per_km"]]
s.columns = ["ช่วงกะ", "รถ-วัน", "ระยะทาง (กม.)", "น้ำมัน (ลิตร)", "CO₂e (กก.)", "CO₂e/กม. (กก.)"]
st.dataframe(s.round(3), hide_index=True, width="stretch")
