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
      "#### 📍การวิเคราะห์รายได้และกำไรแยกตามเส้นทางขนส่ง (Route Code)"
  )

  # ตรวจสอบคอลัมน์ที่จำเป็นสำหรับการคำนวณ
  if "Route_Code" in df.columns:
    route_df = (
        df.groupby("Route_Code")
        .agg(
            Trips=("Trip_ID", "count"),
            Total_Distance=("Distance_km", "sum"),
            Total_Revenue=("Revenue_THB", "sum"),
            Total_Cost=(
                "Total_Recorded_Cost_THB"
                if "Total_Recorded_Cost_THB" in df.columns
                else "Fuel_Cost_THB"
            ),
        )
        .reset_index()
    )

    if "Profit_THB" in df.columns:
      route_profit = (
          df.groupby("Route_Code")["Profit_THB"].sum().reset_index()
      )
      route_df["Net_Profit"] = route_profit["Profit_THB"]
    else:
      route_df["Net_Profit"] = (
          route_df["Total_Revenue"] - route_df["Total_Cost"]
      )

    route_df = route_df.sort_values(by="Total_Revenue", ascending=False)

    st.dataframe(route_df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
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
