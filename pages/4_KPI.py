import database as db
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="KPI & Cost Analytics", page_icon="🎯", layout="wide"
)

st.title("🎯 KPI & Cost Analytics")
st.markdown(
    "ระบบวิเคราะห์ต้นทุน กำไร และตัวชี้วัดประสิทธิภาพการขนส่ง (แยกตามประเภทรถ)"
)

# โหลดข้อมูลจากฐานข้อมูลกลาง
df = db.load_data_from_db()

if df.empty:
  st.warning(
      "ยังไม่มีข้อมูลในระบบ กรุณาไปที่หน้า 'นำเข้าข้อมูล (Import Data)'"
      " เพื่ออัปโหลดไฟล์ Excel ก่อนครับ"
  )
else:
  # --- Sidebar: สำหรับปรับแต่งค่าเสื่อมและตัวกรอง ---
  st.sidebar.header("🛠️ ตั้งค่าค่าเสื่อมสภาพ (Depreciation)")
  st.sidebar.markdown(
      "กำหนดค่าบำรุงรักษา/ค่าเสื่อมสภาพเหมาจ่ายต่อเที่ยว แยกตามประเภทรถ:"
  )

  depreciation_4w = st.sidebar.number_input(
      "รถ 4W (บาท/เที่ยว)", value=250.0, step=50.0
  )
  depreciation_6w = st.sidebar.number_input(
      "รถ 6W (บาท/เที่ยว)", value=500.0, step=50.0
  )
  depreciation_10w = st.sidebar.number_input(
      "รถ 10W (บาท/เที่ยว)", value=800.0, step=50.0
  )


  # ฟังก์ชันคำนวณค่าเสื่อมตามประเภทรถจริง
  def get_dynamic_depreciation(vehicle_type):
    v_type = str(vehicle_type).upper()
    if "4W" in v_type:
      return depreciation_4w
    elif "6W" in v_type:
      return depreciation_6w
    elif "10W" in v_type:
      return depreciation_10w
    return 500.0


  # อัปเดตค่าเสื่อมในข้อมูล
  calc_df = df.copy()
  calc_df["Maintenance_Allocated_THB_Per_Trip"] = calc_df[
      "Vehicle_Type"
  ].apply(get_dynamic_depreciation)

  # คำนวณต้นทุนรวมและกำไรใหม่ตามค่าเสื่อมที่ปรับ
  calc_df["Allocated_Cost_THB"] = (
      calc_df["Maintenance_Allocated_THB_Per_Trip"].fillna(0)
      + calc_df["Insurance_Allocated_THB"].fillna(0)
  )
  calc_df["Total_Recorded_Cost_THB"] = (
      calc_df["Variable_Cost_THB"] + calc_df["Allocated_Cost_THB"]
  )
  calc_df["Profit_THB"] = (
      calc_df["Revenue_THB"] - calc_df["Total_Recorded_Cost_THB"]
  )
  calc_df["Profit_Margin"] = calc_df.apply(
      lambda r: (r["Profit_THB"] / r["Revenue_THB"])
      if r["Revenue_THB"] > 0
      else 0,
      axis=1,
  )

  # --- KPI Summary Metrics ---
  st.subheader("📊 สรุปผลการคำนวณต้นทุนและกำไร (ภาพรวม)")

  total_revenue = calc_df["Revenue_THB"].sum()
  total_cost = calc_df["Total_Recorded_Cost_THB"].sum()
  total_depreciation = calc_df[
      "Maintenance_Allocated_THB_Per_Trip"
  ].sum()
  total_profit = calc_df["Profit_THB"].sum()
  avg_margin = (
      (total_profit / total_revenue * 100) if total_revenue > 0 else 0
  )

  c1, c2, c3, c4 = st.columns(4)
  c1.metric("รายได้รวม", f"฿{total_revenue:,.2f}")
  c2.metric("ต้นทุนรวมทั้งหมด", f"฿{total_cost:,.2f}")
  c3.metric(
      "ค่าเสื่อมสภาพรวม (ทุกคัน)",
      f"฿{total_depreciation:,.2f}",
      delta="แยกตาม 4W/6W/10W",
  )
  c4.metric(
      "กำไรสุทธิสุทธิ",
      f"฿{total_profit:,.2f}",
      delta=f"Margin {avg_margin:.1f}%",
  )

  st.markdown("---")

  # --- Charts ---
  col_l, col_r = st.columns(2)

  with col_l:
    fig_bar = px.bar(
        calc_df.groupby("Vehicle_Type")[
            ["Revenue_THB", "Total_Recorded_Cost_THB", "Profit_THB"]
        ]
        .sum()
        .reset_index(),
        x="Vehicle_Type",
        y=["Revenue_THB", "Total_Recorded_Cost_THB", "Profit_THB"],
        barmode="group",
        title="เปรียบเทียบรายได้ ต้นทุน และกำไร แยกตามประเภทรถ",
        labels={"value": "บาท", "Vehicle_Type": "ประเภทรถ"},
    )
    st.plotly_chart(fig_bar, use_container_width=True)

  with col_r:
    dep_summary = (
        calc_df.groupby("Vehicle_Type")["Maintenance_Allocated_THB_Per_Trip"]
        .sum()
        .reset_index()
    )
    fig_pie = px.pie(
        dep_summary,
        names="Vehicle_Type",
        values="Maintenance_Allocated_THB_Per_Trip",
        title="สัดส่วนค่าเสื่อมสภาพรวม แยกตามประเภทรถ",
        hole=0.3,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

  # --- Data Table ---
  st.subheader("📋 ตารางรายละเอียดคำนวณรายเที่ยววิ่ง")
  st.dataframe(
      calc_df[[
          "Trip_ID",
          "Trip_Date",
          "Vehicle_Type",
          "Route_Code",
          "Distance_km",
          "Revenue_THB",
          "Variable_Cost_THB",
          "Maintenance_Allocated_THB_Per_Trip",
          "Total_Recorded_Cost_THB",
          "Profit_THB",
          "Profit_Margin",
      ]],
      use_container_width=True,
  )
