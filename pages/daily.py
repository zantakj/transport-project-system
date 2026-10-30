import streamlit as st

import importer as im
from common import get_data, sidebar_filters, to_display

st.title("📋 ข้อมูลการปฏิบัติงานรายวัน")
st.caption("1 แถว = พนักงาน 1 คน (คนขับหรือเด็กรถ) ทำงาน 1 วัน · ชื่อ-นามสกุลถูกปกปิด ใช้รหัสพนักงานแทน "
           "· ทะเบียนรถแสดงแบบปกปิด 2 หลักท้าย")

t, daily, p, imports = get_data()
df, d, month = sidebar_filters(t, daily)
q = st.text_input("ค้นหา (รหัสพนักงาน / เลข Booking / ทะเบียน)")
show = df.assign(Plate_Masked=df["Plate"].map(im.mask_plate))
if q:
  s = q.strip()
  show = show[show["Username"].str.contains(s, case=False, na=False)
              | show["Booking"].fillna("").str.contains(s, case=False)
              | show["Plate"].fillna("").str.contains(s, case=False)]
only_bad = st.checkbox("แสดงเฉพาะแถวที่มีปัญหาคุณภาพข้อมูล")
if only_bad:
  show = show[~show["Flags"].isin(["", "NOT_IN_MASTER"])]

cols = ["Work_Date", "Store", "Zone", "Username", "Position", "Plate_Masked", "Box_Type", "Booking", "Shift_In",
        "Punch_In", "Punch_Out", "Work_Hrs", "OT_Hrs", "Trips", "Drops", "Distance_km", "Vehicle_Fee", "Fuel_Fee",
        "OT_Fee", "Incentive", "Penalty", "Total_Payment", "Fuel_L", "CO2_kg", "Profit_THB", "EBilling_Status",
        "Flags"]
out = to_display(show[cols].sort_values(["Work_Date", "Store"]))
st.dataframe(out, hide_index=True, width="stretch", height=520,
             column_config={"วันที่": st.column_config.DateColumn(format="DD/MM/YYYY")})
st.caption(f"{len(show):,} แถว")
st.download_button("⬇️ ดาวน์โหลด CSV", out.to_csv(index=False).encode("utf-8-sig"),
                   file_name=f"daily_{month}.csv", mime="text/csv")
