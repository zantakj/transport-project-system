import streamlit as st

from common import get_data, sidebar_filters, to_display

st.title("📋 ข้อมูลเที่ยววิ่ง")
st.caption("รายละเอียดรายเที่ยว (1 แถว = 1 เที่ยววิ่ง) แสดงรหัสพนักงานขับรถและรหัสสาขาแทนชื่อจริง · "
           "ค่าต่อเที่ยวเป็นค่าเฉลี่ยที่แบ่งจากข้อมูลรายวัน ไม่ใช่ค่าที่วัดจริงในแต่ละเที่ยว")
t, o, p = get_data()
df, do, months, whole = sidebar_filters(t, o)

c = st.columns([2, 2, 2])
q = c[0].text_input("ค้นหารหัสเที่ยว / รหัสพนักงานขับรถ", placeholder="เช่น TR-2606-00001 หรือ DRV-0019")
dates = c[1].date_input("ช่วงวันที่", value=(df["Trip_Date"].min(), df["Trip_Date"].max()),
                        min_value=df["Trip_Date"].min(), max_value=df["Trip_Date"].max())
only = c[2].selectbox("แสดง", ["ทุกเที่ยว", "เที่ยวที่ขาดทุน", "เที่ยวที่มีปัญหาคุณภาพข้อมูล", "E-Billing ยังไม่อนุมัติ"])
if q:
  df = df[df["Trip_ID"].str.contains(q.strip(), case=False) | df["Driver_Code"].str.contains(q.strip(), case=False)]
if isinstance(dates, tuple) and len(dates) == 2:
  df = df[(df["Trip_Date"].dt.date >= dates[0]) & (df["Trip_Date"].dt.date <= dates[1])]
if only == "เที่ยวที่ขาดทุน":
  df = df[df["Profit_THB"] < 0]
elif only == "เที่ยวที่มีปัญหาคุณภาพข้อมูล":
  df = df[df["Flags"] != ""]
elif only == "E-Billing ยังไม่อนุมัติ":
  df = df[df["EBilling_Status"].fillna("").str.lower() != "approved"]

st.caption(f"พบ {len(df):,} เที่ยว")
cols = ["Trip_ID", "Trip_Date", "Driver_Code", "Branch_Code", "Zone", "Distance_km", "Planned_Distance_km", "Drops",
        "Revenue_THB", "Wage_THB", "OT_Approved_Hours", "OT_Cost_THB", "Fuel_L", "Fuel_Price", "Fuel_Cost_THB",
        "Maint_THB", "Profit_THB", "CO2_kg", "EBilling_Status", "Source_Sheet", "Source_Row"]
show = df[[c for c in cols if c in df]].sort_values(["Trip_Date", "Trip_ID"])
show = show.assign(Trip_Date=show["Trip_Date"].dt.strftime("%Y-%m-%d"))
st.dataframe(to_display(show).style.format(precision=2, thousands=","), hide_index=True, width="stretch",
             height=520)
st.download_button("⬇️ ดาวน์โหลดตารางนี้ (CSV)", to_display(show).to_csv(index=False).encode("utf-8-sig"),
                   "trips.csv", "text/csv")

with st.expander("วิธีคำนวณค่าต่อเที่ยว"):
  st.markdown(f"""
- **รายได้** = ยอด E-Billing ของพนักงานขับรถในวันนั้น ÷ จำนวนเที่ยวของวันนั้น
- **ค่าจ้าง** = {p['wage_day']:,.0f} บาท ÷ จำนวนเที่ยวของพนักงานขับรถคนนั้นในวันนั้น
- **ค่า OT** = ชั่วโมง OT ที่อนุมัติต่อเที่ยว × {p['ot_rate']:,.0f} บาท
- **น้ำมัน (ลิตร)** = ระยะทาง ÷ {p['km_per_l']:g} กม./ลิตร · **ค่าน้ำมัน** = ลิตร × ราคาดีเซลเฉลี่ยของเดือนนั้น
- **ค่าซ่อมบำรุง** = ค่าซ่อมบำรุงของกองรถต่อวัน ÷ จำนวนเที่ยวทั้งหมดในวันนั้น
- **กำไรสุทธิ** = รายได้ − ค่าจ้าง − ค่า OT − ค่าน้ำมัน − ค่าซ่อมบำรุง
- **CO₂e** = ลิตร × {p['ef_diesel']} กก./ลิตร
""")
