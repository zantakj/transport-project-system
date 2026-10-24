import database as db
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Advanced Route & Profit Analysis",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Advanced Route & Profit Analysis")
st.caption(
    "วิเคราะห์เจาะลึกประสิทธิภาพเส้นทางขนส่ง กำไรขั้นต้น"
    " และจุดคุ้มทุนรายเที่ยววิ่ง"
)

# ดึงข้อมูลจากฐานข้อมูลกลาง database.py
df = db.load_data_from_db()

if df.empty:
  st.warning(
      "ยังไม่มีข้อมูลในระบบ กรุณาไปที่หน้า 'นำเข้าข้อมูล (Import Data)'"
      " เพื่ออัปโหลดไฟล์ Excel ก่อนครับ"
  )
else:
  st.markdown(
      "#### 📍 การวิเคราะห์รายได้และกำไรแยกตามเส้นทางขนส่ง (Route Code)"
  )

  if "Route_Code" in df.columns:
    # เลือกใช้คอลัมน์ที่มีอยู่จริงเพื่อป้องกัน Error
    rev_col = "Revenue_THB" if "Revenue_THB" in df.columns else "Agreed_Price_THB"
    dist_col = "Distance_km" if "Distance_km" in df.columns else None
    trip_id_col = "Trip_ID" if "Trip_ID" in df.columns else df.columns[0]

    agg_dict = {trip_id_col: "count"}
    if dist_col:
      agg_dict[dist_col] = "sum"
    if rev_col in df.columns:
      agg_dict[rev_col] = "sum"
    if "Fuel_Cost_THB" in df.columns:
      agg_dict["Fuel_Cost_THB"] = "sum"

    route_df = df.groupby("Route_Code").agg(agg_dict).reset_index()

    # ปรับชื่อคอลัมน์ให้เป็นมาตรฐาน
    rename_cols = {trip_id_col: "Trips"}
    if dist_col:
      rename_cols[dist_col] = "Total_Distance"
    if rev_col in df.columns:
      rename_cols[rev_col] = "Total_Revenue"
    if "Fuel_Cost_THB" in df.columns:
      rename_cols["Fuel_Cost_THB"] = "Total_Fuel_Cost"
    route_df = route_df.rename(columns=rename_cols)

    # คำนวณกำไรสุทธิ
    if "Profit_THB" in df.columns:
      route_profit = (
          df.groupby("Route_Code")["Profit_THB"].sum().reset_index()
      )
      route_df["Net_Profit"] = route_profit["Profit_THB"]
    else:
      rev_val = (
          route_df["Total_Revenue"] if "Total_Revenue" in route_df.columns else 0
      )
      cost_val = (
          route_df["Total_Fuel_Cost"]
          if "Total_Fuel_Cost" in route_df.columns
          else 0
      )
      route_df["Net_Profit"] = rev_val - cost_val

    sort_col = (
        "Total_Revenue" if "Total_Revenue" in route_df.columns else "Trips"
    )
    route_df = route_df.sort_values(by=sort_col, ascending=False)

    st.dataframe(route_df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
      if "Total_Revenue" in route_df.columns:
        fig_rev = px.bar(
            route_df.head(10),
            x="Route_Code",
            y="Total_Revenue",
            title="Top 10 เส้นทางที่สร้างรายได้สูงสุด (บาท)",
            template="plotly_dark",
            color="Total_Revenue",
        )
        st.plotly_chart(fig_rev, use_container_width=True)
    with col2:
      if "Net_Profit" in route_df.columns:
        fig_profit = px.bar(
            route_df.head(10),
            x="Route_Code",
            y="Net_Profit",
            title="Top 10 เส้นทางที่มีกำไรสุทธิสูงสุด (บาท)",
            template="plotly_dark",
            color="Net_Profit",
            color_continuous_scale="Greens",
        )
        st.plotly_chart(fig_profit, use_container_width=True)
  else:
    st.error(
        "❌ ไม่พบคอลัมน์ 'Route_Code' ในชุดข้อมูล กรุณาตรวจสอบไฟล์ Excel อีกครั้ง"
    )
