import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# ตรวจสอบสิทธิ์การเข้าถึง
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⛔ กรุณาเข้าสู่ระบบก่อนใช้งานหน้านี้")
    st.stop()

st.set_page_config(page_title="KPI & Cost Analytics", page_icon="🎯", layout="wide")

st.title("🎯 4. KPI & Cost Analysis — วิเคราะห์ตัวชี้วัดและต้นทุน")

# ดึงข้อมูลจากฐานข้อมูล
def load_data():
    conn = sqlite3.connect('transport.db')
    try:
        df = pd.read_sql("SELECT * FROM shipments", conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

df = load_data()

if not df.empty:
    # ------------------------------------
    # ⚙️ SIDEBAR: ตัวเลือกปรับค่าพารามิเตอร์การคำนวณต้นทุน
    # ------------------------------------
    st.sidebar.markdown("### ⚙️ ปรับเงื่อนไขการคำนวณต้นทุน")
    
    calc_mode = st.sidebar.radio(
        "รูปแบบการคิดค่าน้ำมัน:",
        ["ตามข้อมูลจริงในระบบ (Actual Data)", "กำหนดเกณฑ์ (3.98 บาท/กม. @ น้ำมัน 40 บ.)"]
    )
    
    fuel_rate_per_km = 3.98
    if calc_mode == "กำหนดเกณฑ์ (3.98 บาท/กม. @ น้ำมัน 40 บ.)":
        fuel_price_input = st.sidebar.number_input("ราคาน้ำมันปัจจุบัน (บาท/ลิตร):", value=40.0, step=0.5)
        # คำนวณอัตราค่าน้ำมันต่อ กม. ตามสัดส่วนราคาน้ำมัน
        fuel_rate_per_km = (fuel_price_input / 40.0) * 3.98
        st.sidebar.info(f"💡 อัตราค่าน้ำมันคำนวณได้: **{fuel_rate_per_km:.2f} บาท/กม.**")

    # ปรับค่าเสื่อมสภาพ
    apply_depreciation = st.sidebar.checkbox("รวมค่าเสื่อมสภาพ (Depreciation Cost)", value=True)
    depreciation_value = 0.0
    if apply_depreciation:
        dep_type = st.sidebar.selectbox("รูปแบบค่าเสื่อมสภาพ:", ["คิดเหมาต่อเที่ยววิ่ง (บาท/เที่ยว)", "คิดจากค่าเสื่อมสะสมรวมในระบบ"])
        if dep_type == "คิดเหมาต่อเที่ยววิ่ง (บาท/เที่ยว)":
            depreciation_per_trip = st.sidebar.number_input("ค่าเสื่อมสภาพต่อเที่ยว (บาท):", value=1900.0, step=100.0)
            depreciation_value = depreciation_per_trip * len(df)
        else:
            depreciation_value = df['Maintenance_Allocated_THB'].sum() if 'Maintenance_Allocated_THB' in df.columns else 1900.0 * len(df)

    st.sidebar.divider()

    # ------------------------------------
    # 📊 คำนวณค่า KPI & Costs ตามเงื่อนไข
    # ------------------------------------
    total_trips = len(df)
    total_distance = df['Distance_km'].sum() if 'Distance_km' in df.columns else 0
    total_revenue = df['Revenue_THB'].sum() if 'Revenue_THB' in df.columns else (df['Agreed_Price_THB'].sum() if 'Agreed_Price_THB' in df.columns else 0)

    # 1. คำนวณค่าน้ำมันรวม
    if calc_mode == "กำหนดเกณฑ์ (3.98 บาท/กม. @ น้ำมัน 40 บ.)":
        calculated_fuel_cost = total_distance * fuel_rate_per_km
    else:
        calculated_fuel_cost = df['Fuel_Cost_THB'].sum() if 'Fuel_Cost_THB' in df.columns else 0

    # 2. คำนวณต้นทุนอื่นๆ (ค่าเบี้ยเลี้ยง + ค่าทางด่วน + ค่าใช้จ่ายผันแปร)
    other_variable_costs = 0.0
    if 'Driver_Allowance_THB' in df.columns:
        other_variable_costs += df['Driver_Allowance_THB'].sum()
    if 'Toll_Cost_THB' in df.columns:
        other_variable_costs += df['Toll_Cost_THB'].sum()
    if 'Other_Variable_Cost_THB' in df.columns:
        other_variable_costs += df['Other_Variable_Cost_THB'].sum()

    # 3. รวมต้นทุนทั้งหมดและกำไร
    total_calculated_cost = calculated_fuel_cost + other_variable_costs + depreciation_value
    net_profit = total_revenue - total_calculated_cost
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

    # ------------------------------------
    # 📌 DISPLAY METRICS
    # ------------------------------------
    st.subheader("📌 สรุปผลการคำนวณต้นทุนและกำไร (Calculated Results)")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💵 รายได้รวม (Revenue)", f"฿{total_revenue:,.2f}")
    col2.metric("⛽ ค่าน้ำมันคำนวณรวม", f"฿{calculated_fuel_cost:,.2f}", delta=f"{fuel_rate_per_km:.2f} ฿/กม." if calc_mode != "ตามข้อมูลจริงในระบบ (Actual Data)" else None)
    col3.metric("🛠️ ค่าเสื่อมสภาพรวม", f"฿{depreciation_value:,.2f}")
    col4.metric("📈 กำไรสุทธิ (Net Profit)", f"฿{net_profit:,.2f}", delta=f"Margin {profit_margin:.1f}%")

    st.divider()

    # ------------------------------------
    # 📋 TABLE & BREAKDOWN
    # ------------------------------------
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown("#### 🧩 สัดส่วนโครงสร้างต้นทุน (Cost Structure Breakdown)")
        cost_data = pd.DataFrame({
            'หมวดหมู่ต้นทุน': ['ค่าน้ำมันเชื้อเพลิง', 'ค่าเสื่อมสภาพ/บำรุงรักษา', 'ค่าเบี้ยเลี้ยง/ทางด่วน/อื่นๆ'],
            'จำนวนเงิน (บาท)': [calculated_fuel_cost, depreciation_value, other_variable_costs]
        })
        fig_cost = px.pie(
            cost_data, 
            names='หมวดหมู่ต้นทุน', 
            values='จำนวนเงิน (บาท)',
            hole=0.4,
            color_discrete_sequence=['#F59E0B', '#EF4444', '#3B82F6'],
            template="plotly_dark"
        )
        st.plotly_chart(fig_cost, use_container_width=True)

    with c_right:
        st.markdown("#### 📝 ตารางเปรียบเทียบต้นทุนต่อเที่ยววิ่ง (Sample Trips)")
        # สร้าง DataFrame แสดงรายละเอียดเปรียบเทียบ
        display_df = df[['Trip_ID', 'Vehicle_Type', 'Distance_km', 'Revenue_THB', 'Fuel_Cost_THB']].copy()
        
        # คำนวณค่าน้ำมันตามเกณฑ์รายเที่ยว
        display_df['ค่าน้ำมันคำนวณ (3.98 บ./กม.)'] = (display_df['Distance_km'] * fuel_rate_per_km).round(2)
        display_df['ค่าเสื่อมสภาพ (บาท)'] = 1900.0 if apply_depreciation else 0.0
        
        st.dataframe(display_df.head(10), use_container_width=True, hide_index=True)

else:
    st.info("💡 ไม่พบข้อมูลในระบบ กรุณาอัปโหลดไฟล์ในหน้า Import Data")
