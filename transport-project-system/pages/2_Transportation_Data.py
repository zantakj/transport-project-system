import streamlit as st

import calculations as calc
import database as db
from common import get_data

st.title("🚚 Transportation Data Management")
st.caption("ตารางข้อมูลเที่ยววิ่งทั้งหมด พร้อมต้นทุนและกำไรที่ระบบคำนวณ — ค้นหาได้จากทุกคอลัมน์")

tables, trips, _ = get_data()

bad = calc.check_route_distances(tables["Trips"], tables["Routes"])
if len(bad):
  st.error(f"⚠️ พบ {len(bad):,} เที่ยวที่ระยะทางต่างจากระยะมาตรฐานของเส้นทางเกิน 5% (Route_Code เดียวกันควรมีระยะเท่ากัน)")
  with st.expander("ดูรายการที่ผิดปกติ"):
    st.dataframe(db.to_display(bad[["Trip_ID", "Route_Code", "Distance_km", "Round_Trip_km"]]), hide_index=True)
else:
  st.success("✅ ระยะทางทุกเที่ยวตรงกับระยะมาตรฐานของเส้นทาง (Route master)")

show_cols = ["Trip_ID", "Trip_Date", "Customer_Code", "Vehicle_Code", "Vehicle_Type", "Route_Code",
             "Destination_Province_TH", "Distance_km", "Load_kg", "Fuel_Liters", "Job_Status",
             "Revenue_THB", "Variable_Cost_THB", "Fixed_Cost_THB", "Total_Cost_THB",
             "Profit_THB", "Profit_Margin", "CO2_kg"]
df = trips[[c for c in show_cols if c in trips.columns]].copy()
df["Trip_Date"] = df["Trip_Date"].dt.date

search = st.text_input("🔍 ค้นหา (ทุกคอลัมน์ เช่น รหัสเที่ยว, ทะเบียน/รหัสรถ, จังหวัด, ลูกค้า, สถานะ):")
if search:
  mask = df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False, regex=False)).any(axis=1)
  df = df[mask]

st.dataframe(db.to_display(df.round(2)), width="stretch", hide_index=True)
st.caption(f"📌 แสดงผล {len(df):,} รายการ")
st.download_button("⬇️ ดาวน์โหลดผลลัพธ์ (CSV)", df.to_csv(index=False).encode("utf-8-sig"),
                   "transport_data.csv", "text/csv")
