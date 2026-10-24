import sqlite3
import pandas as pd
import streamlit as st
import requests
import db  # เรียกใช้ไฟล์ db.py ที่เราสร้างขึ้นใหม่

# ดึงข้อมูลมาแสดงผล
df = db.load_data_from_db()

# 🚨 ดักสิทธิ์เข้าถึงชั้นที่ 2
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⛔ กรุณาเข้าสู่ระบบก่อนใช้งานหน้านี้")
    st.stop()

st.set_page_config(page_title="KPI & Cost Analytics", page_icon="🎯", layout="wide")

st.title("🎯 KPI & Cost Analytics")
st.caption("ระบบคำนวณต้นทุนการขนส่งเปรียบเทียบราคาน้ำมันและกำหนดค่าเสื่อมสภาพได้ตามต้องการ")

# 🌐 ฟังก์ชันดึงราคาน้ำมัน Real-Time
@st.cache_data(ttl=1800)
def fetch_today_diesel_price():
    try:
        res = requests.get("https://oil-price.bangchak.co.th/api/oilprice", timeout=4)
        if res.status_code == 200:
            data = res.json()
            for item in data[0]['type']:
                if 'diesel' in item['name'].lower() or 'ดีเซล' in item['name']:
                    return float(item['price']), f"🟢 ดึงราคาน้ำมันดีเซล Real-Time วันนี้สำเร็จ ({item['price']} บาท/ลิตร)"
    except Exception:
        pass
    return 32.94, "🟡 ใช้ราคาอ้างอิงมาตรฐาน (32.94 บาท/ลิตร)"

today_diesel_price, price_status = fetch_today_diesel_price()

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
    st.sidebar.markdown("### ⛽ เลือกโหมดคิดราคาน้ำมัน")
    price_mode = st.sidebar.radio("ตัวเลือกราคาน้ำมัน:", ["🌐 ราคาน้ำมันดีเซล Real-Time วันนี้", "สูตรเกณฑ์องค์กร (3.98 บ./กม. @ น้ำมัน 40 บ.)", "ตามค่าน้ำมันเดิมที่บันทึกในเอกสาร"])

    if price_mode == "🌐 ราคาน้ำมันดีเซล Real-Time วันนี้":
        active_fuel_price = st.sidebar.number_input("ราคาน้ำมันดีเซลวันนี้ (บาท/ลิตร):", value=today_diesel_price, step=0.10)
        st.sidebar.caption(price_status)
    elif price_mode == "สูตรเกณฑ์องค์กร (3.98 บ./กม. @ น้ำมัน 40 บ.)":
        active_fuel_price = 40.0
        st.sidebar.info("💡 คำนวณตามเกณฑ์ 3.98 บาท/กม.")
    else:
        active_fuel_price = None
        st.sidebar.info("💡 ใช้ข้อมูลค่าน้ำมันเดิมในตารางเอกสาร")

    # --- วางโค้ดนี้ใน Sidebar ของไฟล์ 4_KPI.py ---
st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ ปรับค่าเสื่อมสภาพยานพาหนะ (แยกตามประเภท)")

# ช่องกรอกแยกประเภทรถ 4W, 6W, 10W
depreciation_4w = st.sidebar.number_input(
    "ค่าเสื่อม 4W (บาท/เที่ยว)", value=250.0, step=50.0
)
depreciation_6w = st.sidebar.number_input(
    "ค่าเสื่อม 6W (บาท/เที่ยว)", value=500.0, step=50.0
)
depreciation_10w = st.sidebar.number_input(
    "ค่าเสื่อม 10W (บาท/เที่ยว)", value=800.0, step=50.0
)


# ฟังก์ชันเลือกค่าเสื่อมตามประเภทรถของแต่ละแถวข้อมูล
def get_dynamic_depreciation(vehicle_type):
  v_type = str(vehicle_type).upper()
  if "4W" in v_type:
    return depreciation_4w
  elif "6W" in v_type:
    return depreciation_6w
  elif "10W" in v_type:
    return depreciation_10w
  return 500.0


# นำไปคำนวณทับค่าเสื่อมในตารางข้อมูล (DataFrame)
df["Maintenance_Allocated_THB_Per_Trip"] = df["Vehicle_Type"].apply(
    get_dynamic_depreciation
)

    calc_df = df.copy()

    if price_mode == "🌐 ราคาน้ำมันดีเซล Real-Time วันนี้":
        calc_df['Calculated_Fuel_Cost'] = calc_df['Fuel_Liters'] * active_fuel_price
    elif price_mode == "สูตรเกณฑ์องค์กร (3.98 บ./กม. @ น้ำมัน 40 บ.)":
        calc_df['Calculated_Fuel_Cost'] = calc_df['Distance_km'] * 3.98
    else:
        calc_df['Calculated_Fuel_Cost'] = calc_df['Fuel_Cost_THB']

    calc_df['Depreciation_Cost'] = dep_per_trip
    calc_df['Total_Trip_Cost'] = calc_df['Calculated_Fuel_Cost'] + calc_df['Depreciation_Cost']
    calc_df['Calculated_Profit'] = calc_df['Revenue_THB'] - calc_df['Total_Trip_Cost']

    total_revenue = calc_df['Revenue_THB'].sum()
    total_calculated_fuel_cost = calc_df['Calculated_Fuel_Cost'].sum()
    total_depreciation = calc_df['Depreciation_Cost'].sum()
    net_profit_sum = calc_df['Calculated_Profit'].sum()
    profit_margin = (net_profit_sum / total_revenue * 100) if total_revenue > 0 else 0

    st.subheader("📌 สรุปผลการคำนวณต้นทุน Real-Time")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💵 รายได้รวม", f"฿{total_revenue:,.2f}")
    m2.metric("⛽ ค่าน้ำมันรวม", f"฿{total_calculated_fuel_cost:,.2f}", delta=f"@{active_fuel_price:.2f} บ./ลิตร" if active_fuel_price else "ข้อมูลเดิม")
    m3.metric("🛠️ ค่าเสื่อมสภาพรวม", f"฿{total_depreciation:,.2f}", delta=f"{dep_per_trip:,.0f} บ./เที่ยว")
    m4.metric("📈 กำไรสุทธิใหม่", f"฿{net_profit_sum:,.2f}", delta=f"Margin {profit_margin:.1f}%")

    st.divider()
    st.markdown("#### 📋 ตารางคำนวณรายเที่ยววิ่ง (ปรับเปลี่ยนค่าน้ำมันและค่าเสื่อมได้)")
    display_table = calc_df[['Trip_ID', 'Vehicle_Type', 'Distance_km', 'Fuel_Liters', 'Revenue_THB', 'Calculated_Fuel_Cost', 'Depreciation_Cost', 'Calculated_Profit']].copy()
    display_table.columns = ['รหัสเที่ยว', 'ประเภทรถ', 'ระยะทาง (กม.)', 'น้ำมัน (ลิตร)', 'รายได้ (บาท)', 'ค่าน้ำมันคำนวณ (บาท)', 'ค่าเสื่อมสภาพ (บาท)', 'กำไรสุทธิคำนวณ (บาท)']
    st.dataframe(display_table, use_container_width=True, hide_index=True)

else:
    st.info("💡 ไม่พบข้อมูลในระบบ กรุณาอัปโหลดไฟล์ในหน้า Import Data")
