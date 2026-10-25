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
  # --- Sidebar: สำหรับปรับแต่งค่าเสื่อม, ราคาน้ำมัน และตัวกรองประเภทรถ ---
  st.sidebar.header("🛠️ ตั้งค่าและการกรองข้อมูล")

  st.sidebar.markdown("🛢️ **กำหนดราคาน้ำมันเชื้อเพลิง:**")
  fuel_price_per_liter = st.sidebar.number_input(
      "ราคาน้ำมัน (บาท/ลิตร)", value=30.0, step=0.5
  )

  st.sidebar.markdown("---")
  st.sidebar.markdown(
      "🚗 **กำหนดค่าบำรุงรักษา/ค่าเสื่อมสภาพเหมาจ่ายต่อเที่ยว:**"
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

  st.sidebar.markdown("---")
  st.sidebar.markdown("🎯 **ตัวกรองการแสดงผล**")

  # สร้างตัวเลือกประเภทรถจากข้อมูลที่มีอยู่
  if "Vehicle_Type" in df.columns:
    v_types_list = ["ทั้งหมด"] + sorted(
        list(df["Vehicle_Type"].dropna().unique())
    )
    selected_v_filter = st.sidebar.selectbox(
        "เลือกประเภทรถที่ต้องการแสดงผล:", v_types_list
    )
  else:
    selected_v_filter = "ทั้งหมด"


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


  # อัปเดตข้อมูลการคำนวณทั้งหมด
  calc_df = df.copy()

  # 1. คำนวณค่าน้ำมันใหม่จาก (ปริมาณลิตร * ราคาน้ำมันที่กรอก) ทันที
  if "Fuel_Liters" in calc_df.columns:
    calc_df["Calculated_Fuel_Cost_THB"] = (
        calc_df["Fuel_Liters"] * fuel_price_per_liter
    )
  else:
    calc_df["Calculated_Fuel_Cost_THB"] = 0.0

  # 2. คำนวณค่าเสื่อมสภาพรายเที่ยว
  calc_df["Maintenance_Allocated_THB_Per_Trip"] = calc_df[
      "Vehicle_Type"
  ].apply(get_dynamic_depreciation)

  calc_df["Allocated_Cost_THB"] = (
      calc_df["Maintenance_Allocated_THB_Per_Trip"].fillna(0)
      + calc_df["Insurance_Allocated_THB"].fillna(0)
  )

  # 3. ต้นทุนรวมทั้งหมด = ค่าน้ำมันใหม่ + ค่าใช้จ่ายจัดสรร (ค่าเสื่อม/ประกัน) + ต้นทุนผันแปรอื่นๆ (ถ้ามี)
  other_variable_cost = (
      calc_df["Variable_Cost_THB"] - calc_df["Fuel_Cost_THB"]
      if "Fuel_Cost_THB" in calc_df.columns
      else 0
  )
  other_variable_cost = other_variable_cost.apply(lambda x: max(0, x))

  calc_df["Total_Recorded_Cost_THB"] = (
      calc_df["Calculated_Fuel_Cost_THB"]
      + other_variable_cost
      + calc_df["Allocated_Cost_THB"]
  )

  # 4. คำนวณกำไรใหม่
  calc_df["Profit_THB"] = (
      calc_df["Revenue_THB"] - calc_df["Total_Recorded_Cost_THB"]
  )
  calc_df["Profit_Margin"] = calc_df.apply(
      lambda r: (r["Profit_THB"] / r["Revenue_THB"])
      if r["Revenue_THB"] > 0
      else 0,
      axis=1,
  )

  # กรองข้อมูลตามที่ผู้ใช้เลือกใน Sidebar
  if selected_v_filter != "ทั้งหมด":
    display_df = calc_df[calc_df["Vehicle_Type"] == selected_v_filter]
    st.info(f"📌 กำลังแสดงผลข้อมูลเฉพาะประเภทรถ: **{selected_v_filter}**")
  else:
    display_df = calc_df

  # --- KPI Summary Metrics ---
  st.subheader(f"📊 สรุปผลการคำนวณต้นทุนและกำไร ({selected_v_filter})")

  total_revenue = display_df["Revenue_THB"].sum()
  total_cost = display_df["Total_Recorded_Cost_THB"].sum()
  total_fuel_cost_sum = display_df["Calculated_Fuel_Cost_THB"].sum()
  total_depreciation = display_df[
      "Maintenance_Allocated_THB_Per_Trip"
  ].sum()
  total_profit = display_df["Profit_THB"].sum()
  avg_margin = (
      (total_profit / total_revenue * 100) if total_revenue > 0 else 0
  )

  c1, c2, c3, c4 = st.columns(4)
  c1.metric("รายได้รวม", f"฿{total_revenue:,.2f}")
  c2.metric(
      "ต้นทุนรวมทั้งหมด",
      f"฿{total_cost:,.2f}",
      delta=f"ค่าน้ำมัน ฿{total_fuel_cost_sum:,.2f}",
      delta_color="off",
  )
  c3.metric(
      "ค่าเสื่อมสภาพรวม",
      f"฿{total_depreciation:,.2f}",
      delta="ตามเงื่อนไขที่เลือก",
  )
  c4.metric(
      "กำไรสุทธิรวม",
      f"฿{total_profit:,.2f}",
      delta=f"Margin {avg_margin:.1f}%",
  )

  st.markdown("---")

  # --- Charts ---
  col_l, col_r = st.columns(2)

  with col_l:
    chart_data = (
        display_df.groupby("Vehicle_Type")[
            ["Revenue_THB", "Total_Recorded_Cost_THB", "Profit_THB"]
        ]
        .sum()
        .reset_index()
    )
    fig_bar = px.bar(
        chart_data,
        x="Vehicle_Type",
        y=["Revenue_THB", "Total_Recorded_Cost_THB", "Profit_THB"],
        barmode="group",
        title="เปรียบเทียบรายได้ ต้นทุน และกำไร แยกตามประเภทรถ",
        labels={"value": "บาท", "Vehicle_Type": "ประเภทรถ"},
    )
    st.plotly_chart(fig_bar, use_container_width=True)

  with col_r:
    dep_summary = (
        display_df.groupby("Vehicle_Type")[
            "Maintenance_Allocated_THB_Per_Trip"
        ]
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
      display_df[[
          "Trip_ID",
          "Trip_Date",
          "Vehicle_Type",
          "Route_Code",
          "Distance_km",
          "Fuel_Liters",
          "Calculated_Fuel_Cost_THB",
          "Revenue_THB",
          "Maintenance_Allocated_THB_Per_Trip",
          "Total_Recorded_Cost_THB",
          "Profit_THB",
          "Profit_Margin",
      ]],
      use_container_width=True,
  )
