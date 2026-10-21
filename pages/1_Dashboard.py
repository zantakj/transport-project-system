import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Executive Dashboard", page_icon="🚚", layout="wide")

st.title("🚚 Executive Transportation Dashboard")
st.caption("ระบบติดตามและวิเคราะห์ข้อมูลประสิทธิภาพการขนส่ง — บริษัท ABC")

# ดึงข้อมูลจาก SQLite
def load_data():
    conn = sqlite3.connect('transport.db')
    try:
        df = pd.read_sql("SELECT * FROM shipments", conn)
        if 'Trip_Date' in df.columns:
            df['Trip_Date'] = pd.to_datetime(df['Trip_Date'])
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

raw_df = load_data()

if not raw_df.empty:
    # ------------------------------------
    # 🔍 SIDEBAR FILTER
    # ------------------------------------
    st.sidebar.header("🎯 ตัวกรองข้อมูล (Filters)")
    
    min_date = raw_df['Trip_Date'].min() if 'Trip_Date' in raw_df.columns else None
    max_date = raw_df['Trip_Date'].max() if 'Trip_Date' in raw_df.columns else None
    
    if min_date and max_date:
        date_range = st.sidebar.date_input(
            "ช่วงวันที่ปฏิบัติงาน:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_d, end_d = date_range
            df = raw_df[(raw_df['Trip_Date'].dt.date >= start_d) & (raw_df['Trip_Date'].dt.date <= end_d)]
        else:
            df = raw_df.copy()
    else:
        df = raw_df.copy()

    if 'Vehicle_Type' in df.columns:
        v_types = ['ทั้งหมด'] + list(df['Vehicle_Type'].dropna().unique())
        selected_vtype = st.sidebar.selectbox("ประเภทรถ:", v_types)
        if selected_vtype != 'ทั้งหมด':
            df = df[df['Vehicle_Type'] == selected_vtype]

    if 'Job_Status' in df.columns:
        statuses = ['ทั้งหมด'] + list(df['Job_Status'].dropna().unique())
        selected_status = st.sidebar.selectbox("สถานะการขนส่ง:", statuses)
        if selected_status != 'ทั้งหมด':
            df = df[df['Job_Status'] == selected_status]

    st.sidebar.caption(f"📊 แสดงข้อมูล: **{len(df):,}** / {len(raw_df):,} รายการ")

    # ------------------------------------
    # 📊 METRICS SECTION (ใช้ Metric ของ Streamlit อ่านง่าย สบายตา)
    # ------------------------------------
    total_trips = len(df)
    total_distance = df['Distance_km'].sum() if 'Distance_km' in df.columns else 0
    total_fuel = df['Fuel_Liters'].sum() if 'Fuel_Liters' in df.columns else 0
    avg_efficiency = (total_distance / total_fuel) if total_fuel > 0 else 0
    co2_emission = (total_fuel * 2.68) / 1000  # ตัน CO2

    total_revenue = df['Revenue_THB'].sum() if 'Revenue_THB' in df.columns else (df['Agreed_Price_THB'].sum() if 'Agreed_Price_THB' in df.columns else 0)
    total_fuel_cost = df['Fuel_Cost_THB'].sum() if 'Fuel_Cost_THB' in df.columns else 0
    total_profit = df['Profit_THB'].sum() if 'Profit_THB' in df.columns else (total_revenue - total_fuel_cost)

    st.markdown("### 📌 สรุปดรรชนีวัดผลหลัก")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 เที่ยววิ่งรวม", f"{total_trips:,} เที่ยว")
    c2.metric("🛣️ ระยะทางรวม", f"{total_distance:,.1f} กม.")
    c3.metric("⛽ อัตราสิ้นเปลืองเฉลี่ย", f"{avg_efficiency:.2f} กม./ลิตร")
    c4.metric("🌿 ปล่อยคาร์บอน (CO₂)", f"{co2_emission:,.2f} ตัน")

    st.markdown("### 💰 ผลประกอบการทางการเงิน")
    m1, m2, m3 = st.columns(3)
    m1.metric("💵 รายได้รวม", f"฿{total_revenue:,.2f}")
    m2.metric("⛽ ค่าน้ำมันรวม", f"฿{total_fuel_cost:,.2f}")
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    m3.metric("📈 กำไรขั้นต้นรวม", f"฿{total_profit:,.2f}", delta=f"Margin: {profit_margin:.1f}%")

    st.divider()

    # ------------------------------------
    # 📈 CHARTS SECTION (ปรับแต่ง Theme ให้มองเห็นชัดเจน)
    # ------------------------------------
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.markdown("#### 🚛 สัดส่วนประเภทรถที่ใช้")
        if 'Vehicle_Type' in df.columns and not df.empty:
            vtype_counts = df['Vehicle_Type'].value_counts().reset_index()
            vtype_counts.columns = ['Vehicle_Type', 'Count']
            
            fig_pie = px.pie(
                vtype_counts, 
                names='Vehicle_Type', 
                values='Count',
                hole=0.4,
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=280,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with row1_col2:
        st.markdown("#### 📍 10 อันดับเส้นทางสูงสุด")
        if 'Route_Code' in df.columns and not df.empty:
            top_routes = df['Route_Code'].value_counts().head(10).reset_index()
            top_routes.columns = ['Route_Code', 'Trips']
            
            fig_route = px.bar(
                top_routes, 
                x='Trips', 
                y='Route_Code', 
                orientation='h',
                template="plotly_dark",
                color='Trips',
                color_continuous_scale='Blues',
                labels={'Route_Code':'เส้นทาง', 'Trips':'จำนวนเที่ยว'}
            )
            fig_route.update_layout(
                yaxis=dict(autorange="reversed"), 
                margin=dict(t=10, b=10, l=10, r=10), 
                height=280,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_route, use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.markdown("#### 📈 รายได้ และ ค่าน้ำมันรายเดือน")
        if 'Year_Month' in df.columns and 'Revenue_THB' in df.columns and not df.empty:
            monthly = df.groupby('Year_Month').agg(
                Revenue=('Revenue_THB', 'sum'),
                Fuel_Cost=('Fuel_Cost_THB', 'sum')
            ).reset_index()
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=monthly['Year_Month'], y=monthly['Revenue'], name='รายได้', marker_color='#2ecc71'))
            fig_trend.add_trace(go.Bar(x=monthly['Year_Month'], y=monthly['Fuel_Cost'], name='ค่าน้ำมัน', marker_color='#e74c3c'))
            
            fig_trend.update_layout(
                template="plotly_dark",
                barmode='group', 
                height=280, 
                margin=dict(t=10, b=10, l=10, r=10), 
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    with row2_col2:
        st.markdown("#### ⚡ อัตราสิ้นเปลืองแยกตามรถ (km/L)")
        if 'Vehicle_Type' in df.columns and 'Distance_km' in df.columns and 'Fuel_Liters' in df.columns and not df.empty:
            eff_df = df.groupby('Vehicle_Type').agg(
                Total_Dist=('Distance_km', 'sum'),
                Total_Fuel=('Fuel_Liters', 'sum')
            ).reset_index()
            eff_df['KM_per_Liter'] = (eff_df['Total_Dist'] / eff_df['Total_Fuel']).round(2)
            
            fig_eff = px.bar(
                eff_df, 
                x='Vehicle_Type', 
                y='KM_per_Liter',
                template="plotly_dark",
                color='KM_per_Liter',
                color_continuous_scale='Viridis',
                text='KM_per_Liter',
                labels={'Vehicle_Type':'ประเภทรถ', 'KM_per_Liter':'กม./ลิตร'}
            )
            fig_eff.update_layout(
                height=280, 
                margin=dict(t=10, b=10, l=10, r=10),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_eff, use_container_width=True)

else:
    st.info("💡 ยังไม่มีข้อมูลในระบบ กรุณาอัปโหลดไฟล์ในหน้า Import Data")
