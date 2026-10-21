import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import requests

# ตรวจสอบสิทธิ์การเข้าถึง
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⛔ กรุณาเข้าสู่ระบบก่อนใช้งานหน้านี้")
    st.stop()

st.set_page_config(page_title="KPI & Real-Time Cost Analytics", page_icon="⛽", layout="wide")

st.title("🎯 4. KPI & Real-Time Fuel Cost Analytics")
st.caption("ระบบเชื่อมโยงข้อมูลราคาน้ำมัน Real-Time และคำนวณต้นทุนการขนส่ง")

# ------------------------------------
# 🌐 ฟังก์ชันดึงราคาน้ำมัน Real-Time จาก API
# ------------------------------------
@st.cache_data(ttl=3600)  # ดึงข้อมูลใหม่ทุก 1 ชั่วโมง
def get_realtime_oil_price():
    try:
        # API ดึงราคาน้ำมันขายปลีกในไทย (ตัวอย่าง Open API ราคาน้ำมัน)
        url = "https://oil-price.bangchak.co.th/api/oilprice" # หรือ API ราคาน้ำมันกลาง
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # ดึงราคาดีเซลเป็นหลักสำหรับงานขนส่ง
            diesel_price = float(data.get('Diesel', 32.94))
            return diesel_price, "ดึงข้อมูล Real-Time สำเร็จ"
    except Exception:
        pass
    # หาก API ขัดข้อง ให้ใช้ราคาอ้างอิงมาตรฐาน
    return 33.00, "ใช้ราคาอ้างอิงฐานข้อมูลระบบ (33.00 บาท/ลิตร)"

realtime_price, price_status = get_realtime_oil_price()

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
    # ⚙️ SIDEBAR: ตัวเลือกระบบการคำนวณ
    # ------------------------------------
    st.sidebar.markdown("### ⛽ เลือกแหล่งข้อมูลราคาน้ำมัน")
    
    price_mode = st.sidebar.radio(
        "โหมดการคิดราคาน้ำมัน:",
        ["🌐 ราคาน้ำมันดีเซล Real-Time วันนี้", "สูตรเกณฑ์ 3.98 บ./กม. (@ น้ำมัน 40 บ.)", "ตามค่าจริงที่บันทึกในเอกสาร"]
    )

    if price_mode == "🌐 ราคาน้ำมันดีเซล Real-Time วันนี้":
        current_fuel_price = st.sidebar.number_input("ราคาน้ำมันดีเซลหน้าปั๊มวันนี้ (บาท/ลิตร):", value=realtime_price)
        st.sidebar.caption(f"Status: {price_status}")
    elif price_mode == "สูตรเกณฑ์ 3.98 บ./กม. (@ น้ำมัน 40 บ.)":
        current_fuel_price = 40.0
    else:
        current_fuel_price = None

    # การคิดค่าเสื่อมสภาพ
    st.sidebar.divider()
    st.sidebar.markdown("### 🛠️ เงื่อนไขค่าเสื่อมสภาพ")
    apply_dep = st.sidebar.checkbox("รวมค่าเสื่อมสภาพ (Depreciation)", value=True)
    dep_per_trip = 1900.0 if apply_dep else 0.0

    # ------------------------------------
    # 📊 คำนวณต้นทุน Real-Time
    # ------------------------------------
    total_trips = len(df)
    total_distance = df['Distance_km'].sum() if 'Distance_km' in df.columns else 0
    total_fuel_liters = df['Fuel_Liters'].sum() if 'Fuel_Liters' in df.columns else 0
    total_revenue = df['Revenue_THB'].sum() if 'Revenue_THB' in df.columns else 0

    # คำนวณค่าน้ำมัน
    if price_mode == "🌐 ราคาน้ำมันดีเซล Real-Time วันนี้":
        calculated_fuel_cost = total_fuel_liters * current_fuel_price
    elif price_mode == "สูตรเกณฑ์ 3.98 บ./กม. (@ น้ำมัน 40 บ.)":
        calculated_fuel_cost = total_distance * 3.98
    else:
        calculated_fuel_cost = df['Fuel_Cost_THB'].sum() if 'Fuel_Cost_THB' in df.columns else 0

    total_depreciation = dep_per_trip * total_trips
    total_calculated_cost = calculated_fuel_cost + total_depreciation
    net_profit = total_revenue - total_calculated_cost
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

    # ------------------------------------
    # 📌 DISPLAY METRICS
    # ------------------------------------
    st.subheader("📌 สรุปต้นทุนและผลตอบแทน (Real-Time Calculated)")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💵 รายได้รวม", f"฿{total_revenue:,.2f}")
    m2.metric("⛽ ค่าน้ำมันคำนวณรวม", f"฿{calculated_fuel_cost:,.2f}", delta=f"@{current_fuel_price} บ./ลิตร" if current_fuel_price else "ข้อมูลเอกสาร")
    m3.metric("🛠️ ค่าเสื่อมสภาพรวม", f"฿{total_depreciation:,.2f}", delta=f"{dep_per_trip:,.0f} บ./เที่ยว")
    m4.metric("📈 กำไรสุทธิ (Net Profit)", f"฿{net_profit:,.2f}", delta=f"Margin {profit_margin:.1f}%")

    st.divider()

    # แสดงผลตารางเปรียบเทียบ
    st.markdown("#### 📋 รายละเอียดต้นทุนต่อเที่ยววิ่ง (คำนวณตามราคาน้ำมัน Real-Time)")
    sample_df = df[['Trip_ID', 'Vehicle_Type', 'Distance_km', 'Fuel_Liters', 'Revenue_THB']].copy()
    
    if current_fuel_price:
        sample_df['ค่าน้ำมัน Real-time (บาท)'] = (sample_df['Fuel_Liters'] * current_fuel_price).round(2)
    else:
        sample_df['ค่าน้ำมัน Real-time (บาท)'] = (sample_df['Distance_km'] * 3.98).round(2)
        
    sample_df['ค่าเสื่อมสภาพ (บาท)'] = dep_per_trip
    st.dataframe(sample_df.head(15), use_container_width=True, hide_index=True)

else:
    st.info("💡 ไม่พบข้อมูลในระบบ กรุณาอัปโหลดไฟล์ในหน้า Import Data")
