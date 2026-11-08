import streamlit as st

from common import get_data, info, sidebar_filters, to_display

st.title("📋 ข้อมูลเที่ยววิ่ง")
st.caption("รายละเอียดรายเที่ยว (1 แถว = 1 เที่ยววิ่ง) แสดงรหัสแทนชื่อจริงของพนักงานขับรถและสาขา")
t, o, p = get_data()
df, do, months, whole = sidebar_filters(t, o)

c = st.columns([2, 2, 2])
q = c[0].text_input("ค้นหารหัสเที่ยว / รหัสพนักงานขับรถ", placeholder="เช่น TR-2606-00001 หรือ DRV-0019")
dates = c[1].date_input("ช่วงวันที่", value=(df["Trip_Date"].min(), df["Trip_Date"].max()),
                        min_value=df["Trip_Date"].min(), max_value=df["Trip_Date"].max())
only = c[2].selectbox("แสดง", ["ทุกเที่ยว", "เที่ยวที่ขาดทุน", "เที่ยวที่มีปัญหาคุณภาพข้อมูล"])
if q:
  df = df[df["Trip_ID"].str.contains(q.strip(), case=False) | df["Driver_Code"].str.contains(q.strip(), case=False)]
if isinstance(dates, tuple) and len(dates) == 2:
  df = df[(df["Trip_Date"].dt.date >= dates[0]) & (df["Trip_Date"].dt.date <= dates[1])]
if only == "เที่ยวที่ขาดทุน":
  df = df[df["Profit_THB"] < 0]
elif only == "เที่ยวที่มีปัญหาคุณภาพข้อมูล":
  df = df[df["Flags"] != ""]

detail = st.toggle("แสดงรายละเอียดต้นทุนแยกหมวด")
main = ["Trip_ID", "Trip_Date", "Driver_Code", "Branch_Code", "Distance_km", "Drops", "Revenue_THB", "Cost_THB",
        "Profit_THB", "CO2_kg"]
more = ["Trip_ID", "Trip_Date", "Driver_Code", "Branch_Code", "Zone", "Distance_km", "Planned_Distance_km", "Drops",
        "Revenue_THB", "Wage_THB", "OT_Approved_Hours", "OT_Cost_THB", "Fuel_L", "Fuel_Price", "Fuel_Cost_THB",
        "Maint_THB", "Cost_THB", "Profit_THB", "CO2_kg", "EBilling_Status", "Source_Sheet", "Source_Row"]
cols = more if detail else main
show = df[[c for c in cols if c in df]].sort_values(["Trip_Date", "Trip_ID"])
show = show.assign(Trip_Date=show["Trip_Date"].dt.strftime("%Y-%m-%d"))

h = st.columns([3, 2])
h[0].caption(f"พบ {len(df):,} เที่ยว")
info(h[1], "trip_calc", "วิธีคำนวณค่าต่อเที่ยว", f"""
ข้อมูลบริษัทบันทึกเป็น **รายวัน** (พนักงาน 1 คน 1 วัน) จึงแบ่งค่าของวันนั้นเท่ากันให้แต่ละเที่ยว

| ค่า | วิธีคำนวณ |
|---|---|
| รายได้ | ยอด E-Billing ของพนักงานขับรถวันนั้น ÷ จำนวนเที่ยวของวันนั้น |
| ค่าจ้าง | {p['wage_day']:,.0f} บาท ÷ จำนวนเที่ยวของคนขับคนนั้นในวันนั้น |
| ค่า OT | ชั่วโมง OT ที่อนุมัติต่อเที่ยว × {p['ot_rate']:,.0f} บาท |
| ค่าน้ำมัน | ระยะทาง ÷ {p['km_per_l']:g} กม./ลิตร × ราคาดีเซลของเดือนนั้น |
| ค่าซ่อมบำรุง | ค่าซ่อมบำรุงกองรถต่อวัน ÷ จำนวนเที่ยวทั้งหมดในวันนั้น |
| ต้นทุนรวม | ค่าจ้าง + ค่า OT + ค่าน้ำมัน + ค่าซ่อมบำรุง |
| กำไรสุทธิ | รายได้ − ต้นทุนรวม |
| CO₂e | ระยะทาง ÷ {p['km_per_l']:g} × {p['ef_diesel']} |

ค่าต่อเที่ยวจึงเป็น **ค่าเฉลี่ย** ไม่ใช่ค่าที่วัดจริงในแต่ละเที่ยว
""", "ⓘ วิธีคำนวณค่าต่อเที่ยว")
st.dataframe(to_display(show).style.format(precision=2, thousands=","), hide_index=True, width="stretch",
             height=520)
st.download_button("⬇️ ดาวน์โหลดตารางนี้ (CSV)", to_display(show).to_csv(index=False).encode("utf-8-sig"),
                   "trips.csv", "text/csv")
