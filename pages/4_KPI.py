import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import requests

# 🚨 ตรวจสอบสิทธิ์การเข้าถึง
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⛔ กรุณาเข้าสู่ระบบก่อนใช้งานหน้านี้")
    st.stop()

st.set_page_config(page_title="KPI & Real-Time Fuel Cost", page_icon="⛽", layout="wide")

st.title("🎯 4. KPI & Real-Time Fuel Cost Analytics")
st.caption("ระบบคำนวณต้นทุนการขนส่งเปรียบเทียบราคาน้ำมัน Real-Time และเงื่อนไของค์กร")

# ------------------------------------
# 🌐 1. ฟังก์ชันดึงราคาน้ำมัน Real-Time
# ------------------------------------
@st.cache_data(ttl=1800)  # ดึงข้อมูลใหม่ทุก 30 นาที
def fetch_realtime_diesel_price():
    try:
        # API ราคาน้ำมันดีเซล B7 ปัจจุบัน (THB/Liter)
        res = requests.get("https://oil-price.bangchak.co.th/api/oilprice", timeout=4)
        if res.status_code == 200:
            data = res.json()
            # ดึงราคา Diesel
            for item in data[0]['type']:
                if 'diesel' in item['name'].lower() or 'ดีเซล' in item['name']:
                    return float(item['price']), "🟢 ดึงราคาน้ำมัน Real-Time สำเร็จ"
    except Exception:
        pass
    # ค่าเริ่มต้นสำรองหาก API ขัดข้อง
    return 32.94, "🟡 ใช้ราคาอ้างอิงฐานข้อมูลระบบ (32.94 บาท/ลิตร)"

realtime_price, price_status = fetch_realtime_diesel_price()

# ดึงข้อมูลจากฐานข้อมูล SQLite
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
    # ⚙️ 2. SIDEBAR CONFIGURATION
    # ------------------------------------
    st.sidebar.markdown("### ⛽ เลือกโหมดคำนวณราคาน้ำมัน")
    
    price_mode = st.sidebar.radio(
        "ตัวเลือกราคาน้ำมัน:",
        [
            "🌐 ราคาน้ำมันดีเซล Real-Time วันนี้", 
            "สูตรเกณฑ์องค์กร (3.98 บ./กม. @ น้ำมัน 40 บ.)", 
            "ตามค่าน้ำมันจริงในเอกสาร/ระบบ"
        ]
    )

    # กำหนดราคาน้ำมันต่อลิตร (บาท/ลิตร)
    if price_mode == "🌐 ราคาน้ำมันดีเซล Real-Time วันนี้":
        active_fuel_price = st.sidebar.number_input("ราคาน้ำมันดีเซลวันนี้ (บาท/ลิตร):", value=realtime_price, step=0.10)
        st.sidebar.caption(price_status)
    elif price_mode == "สูตรเกณฑ์องค์กร (3.98 บ./กม. @ น้ำมัน 40 บ.)":
        active_fuel_price = 40.0
        st.sidebar.info("💡 คำนวณตามเกณฑ์ 3.98 บาท/กม.")
    else:
        active_fuel_price = None
        st.sidebar.info("💡 คำนวณตามค่าน้ำมันจริงที่บันทึกในตาราง")

    st.sidebar.divider()
    st.sidebar.markdown("### 🛠️ ค่าเสื่อมสภาพยานพาหนะ")
    apply_dep = st.sidebar.checkbox("รวมค่าเสื่อมสภาพ (Depreciation Cost)", value=True)
    dep_per_trip = 1900.0 if apply_dep else 0.0

    # ------------------------------------
    # 📊 3. คำนวณต้นทุน REAL-TIME
    # ------------------------------------
    total_trips = len(df)
    total_distance = df['Distance_km'].sum() if 'Distance_km' in df.columns else 0
    total_fuel_liters = df['Fuel_Liters'].sum() if 'Fuel_Liters' in df.columns else 0
    total_revenue = df['Revenue_THB'].sum() if 'Revenue_THB' in df.columns else 0

    # คำนวณตารางใหม่ตามเงื่อนไข
    calc_df = df.copy()

    if price_mode == "🌐 ราคาน้ำมันดีเซล Real-Time วันนี้":
        # ค่าน้ำมัน = ปริมาณน้ำมัน (ลิตร) x ราคาน้ำมัน Real-Time (บาท/ลิตร)
        calc_df['Calculated_Fuel_Cost'] = calc_df['Fuel_Liters'] * active_fuel_price
    elif price_mode == "สูตรเกณฑ์องค์กร (3.98 บ./กม. @ น้ำมัน 40 บ.)":
        # ค่าน้ำมัน = ระยะทาง (กม.) x 3.98 บาท/กม.
        calc_df['Calculated_Fuel_Cost'] = calc_df['Distance_km'] * 3.98
    else:
        # ค่าน้ำมันตามเอกสารเดิม
        calc_df['Calculated_Fuel_Cost'] = calc_df['Fuel_Cost_THB']

    calc_df['Depreciation_Cost'] = dep_per_trip
    calc_df['Total_Trip_Cost'] = calc_df['Calculated_Fuel_Cost'] + calc_df['Depreciation_Cost']
    calc_df['Calculated_Profit'] = calc_df['Revenue_THB'] - calc_df['Total_Trip_Cost']

    # สรุปรวมทั้งสิ้น
    total_calculated_fuel_cost = calc_df['Calculated_Fuel_Cost'].sum()
    total_depreciation = calc_df['Depreciation_Cost'].sum()
    total_cost_sum = calc_df['Total_Trip_Cost'].sum()
    net_profit_sum = calc_df['Calculated_Profit'].sum()
    profit_margin = (net_profit_sum / total_revenue * 100) if total_revenue > 0 else 0

    # ------------------------------------
    # 📌 4. DISPLAY METRICS
    # ------------------------------------
    st.subheader("📌 สรุปผลการคำนวณต้นทุนและกำไร (Real-Time Output)")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💵 รายได้รวม", f"฿{total_revenue:,.2f}")
    
    if price_mode == "🌐 ราคาน้ำมันดีเซล Real-Time วันนี้":
        m2.metric("⛽ ค่าน้ำมันรวม (Real-Time)", f"฿{total_calculated_fuel_cost:,.2f}", delta=f"@{active_fuel_price:.2f} บ./ลิตร")
    elif price_mode == "สูตรเกณฑ์องค์กร (3.98 บ./กม. @ น้ำมัน 40 บ.)":
        m2.metric("⛽ ค่าน้ำมันรวม (เกณฑ์องค์กร)", f"฿{total_calculated_fuel_cost:,.2f}", delta="3.98 บ./กม.")
    else:
        m2.metric("⛽ ค่าน้ำมันรวม (ตามระบบ)", f"฿{total_calculated_fuel_cost:,.2f}")

    m3.metric("🛠️ ค่าเสื่อมสภาพรวม", f"฿{total_depreciation:,.2f}", delta=f"{dep_per_trip:,.0f} บ./เที่ยว")
    m4.metric("📈 กำไรสุทธิใหม่ (Calculated)", f"฿{net_profit_sum:,.2f}", delta=f"Margin {profit_margin:.1f}%")

    st.divider()

    # ------------------------------------
    # 📋 5. DISPLAY TABLE
    # ------------------------------------
    st.markdown("#### 📋 ตารางเปรียบเทียบต้นทุนรายเที่ยววิ่ง (คำนวณตามโหมดที่เลือก)")
    
    display_table = calc_df[['Trip_ID', 'Vehicle_Type', 'Distance_km', 'Fuel_Liters', 'Revenue_THB', 'Calculated_Fuel_Cost', 'Depreciation_Cost', 'Calculated_Profit']].copy()
    display_table.columns = ['รหัสเที่ยว', 'ประเภทรถ', 'ระยะทาง (กม.)', 'น้ำมัน (ลิตร)', 'รายได้ (บาท)', 'ค่าน้ำมันคำนวณ (บาท)', 'ค่าเสื่อมสภาพ (บาท)', 'กำไรสุทธิคำนวณ (บาท)']
    
    st.dataframe(display_table, use_container_width=True, hide_index=True)

else:
    st.info("💡 ไม่พบข้อมูลในระบบ กรุณาอัปโหลดไฟล์ในหน้า Import Data")
