import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ตั้งค่าหน้าเว็บแบบ Wide Layout
st.set_page_config(page_title="Executive Dashboard", page_icon="🚚", layout="wide")

# CSS ตกแต่ง Card และส่วนประกอบต่างๆ ให้ดูสวยงาม
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222D;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #00D4B1;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 0.85rem;
        color: #A0AAB5;
        font-weight: 500;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: bold;
        color: #FFFFFF;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #00D4B1;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚚 Executive Transportation Dashboard")
st.caption("ระบบติดตามและวิเคราะห์ข้อมูลประสิทธิภาพการขนส่ง — บริษัท ABC")

# ดึงข้อมูลจากฐานข้อมูล SQLite
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
    # 🔍 SIDEBAR FILTER (ตัวกรองข้อมูล)
    # ------------------------------------
    st.sidebar.header("🎯 ตัวกรองข้อมูล (Filters)")
    
    # 1. กรองช่วงวันที่
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

    # 2. กรองประเภทรถ
    if 'Vehicle_Type' in df.columns:
        v_types = ['ทั้งหมด'] + list(df['Vehicle_Type'].dropna().unique())
        selected_vtype = st.sidebar.selectbox("ประเภทรถ:", v_types)
        if selected_vtype != 'ทั้งหมด':
            df = df[df['Vehicle_Type'] == selected_vtype]

    # 3. กรองสถานะงาน
    if 'Job_Status' in df.columns:
        statuses = ['ทั้งหมด'] + list(df['Job_Status'].dropna().unique())
        selected_status = st.sidebar.selectbox("สถานะการขนส่ง:", statuses)
        if selected_status != 'ทั้งหมด':
            df = df[df['Job_Status'] == selected_status]

    st.sidebar.divider()
    st.sidebar.caption(f"📊 ข้อมูลที่เลือก: **{len(df):,}** / {len(raw_df):,} รายการ")

    # ------------------------------------
    # 📊 SECTION 1: KEY PERFORMANCE METRICS
    # ------------------------------------
    st.subheader("📌 ภาพรวมดรรชนีวัดผลการดำเนินงาน (Key Metrics)")
    
    # คำนวณค่าต่างๆ
    total_trips = len(df)
    total_distance = df['Distance_km'].sum() if 'Distance_km' in df.columns else 0
    total_fuel = df['Fuel_Liters'].sum() if 'Fuel_Liters' in df.columns else 0
    avg_efficiency = (total_distance / total_fuel) if total_fuel > 0 else 0
    
    # คำนวณ Carbon Footprint (น้ำมันดีเซล 1 ลิตรปล่อย CO2 ประมาณ 2.68 kg)
    co2_emission = (total_fuel * 2.68) / 1000  # แปลงเป็น ตัน CO2

    total_revenue = df['Revenue_THB'].sum() if 'Revenue_THB' in df.columns else (df['Agreed_Price_THB'].sum() if 'Agreed_Price_THB' in df.columns else 0)
    total_fuel_cost = df['Fuel_Cost_THB'].sum() if 'Fuel_Cost_THB' in df.columns else 0
    total_profit = df['Profit_THB'].sum() if 'Profit_THB' in df.columns else (total_revenue - total_fuel_cost)

    # แถวที่ 1: การปฏิบัติงานและพลังงาน
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📦 จำนวนเที่ยววิ่งทั้งหมด</div>
            <div class="metric-value">{total_trips:,} <span style="font-size:1rem;">เที่ยว</span></div>
            <div class="metric-sub">การดำเนินงานรวม</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🛣️ ระยะทางขนส่งรวม</div>
            <div class="metric-value">{total_distance:,.1f} <span style="font-size:1rem;">กม.</span></div>
            <div class="metric-sub">ระยะทางสะสม</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⛽ อัตราสิ้นเปลืองเฉลี่ย</div>
            <div class="metric-value">{avg_efficiency:.2f} <span style="font-size:1rem;">กม./ลิตร</span></div>
            <div class="metric-sub">ใช้น้ำมันรวม {total_fuel:,.0f} ลิตร</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #00E676;">
            <div class="metric-title">🌿 ปริมาณการปล่อยคาร์บอน (CO₂)</div>
            <div class="metric-value">{co2_emission:,.2f} <span style="font-size:1rem;">ตัน CO₂</span></div>
            <div class="metric-sub">ประมาณการตามปริมาณเชื้อเพลิง</div>
        </div>
        """, unsafe_allow_html=True)

    # แถวที่ 2: มิติด้านการเงิน
    st.markdown("<h4 style='margin-top:15px; margin-bottom:10px;'>💰 สรุปประสิทธิภาพทางการเงิน (Financial Summary)</h4>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.metric("💵 รายได้รวมการขนส่ง", f"฿{total_revenue:,.2f}")
    with m2:
        st.metric("⛽ ค่าน้ำมันเชื้อเพลิงรวม", f"฿{total_fuel_cost:,.2f}")
    with m3:
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        st.metric("📈 กำไรขั้นต้นรวม", f"฿{total_profit:,.2f}", delta=f"Margin: {profit_margin:.1f}%")

    st.divider()

    # ------------------------------------
    # 📈 SECTION 2: CHARTS & VISUALIZATIONS
    # ------------------------------------
    row1_1, row1_2 = st.columns([1, 1])

    with row1_1:
        st.subheader("🚛 สัดส่วนการใช้งานรถจำแนกตามประเภท (Vehicle Fleet Distribution)")
        if 'Vehicle_Type' in df.columns:
            vtype_counts = df['Vehicle_Type'].value_counts().reset_index()
            vtype_counts.columns = ['Vehicle_Type', 'Count']
            fig_pie = px.pie(
                vtype_counts, 
                names='Vehicle_Type', 
                values='Count',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320)
            st.plotly_chart(fig_pie, use_container_width=True)

    with row1_2:
        st.subheader("📍 10 อันดับเส้นทางที่มีการขนส่งสูงสุด (Top 10 Routes)")
        if 'Route_Code' in df.columns:
            top_routes = df['Route_Code'].value_counts().head(10).reset_index()
            top_routes.columns = ['Route_Code', 'Trips']
            fig_route = px.bar(
                top_routes, 
                x='Trips', 
                y='Route_Code', 
                orientation='h',
                color='Trips',
                color_continuous_scale='Blues',
                labels={'Route_Code':'รหัสเส้นทาง', 'Trips':'จำนวนเที่ยว'}
            )
            fig_route.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=20, b=20, l=20, r=20), height=320)
            st.plotly_chart(fig_route, use_container_width=True)

    row2_1, row2_2 = st.columns([1, 1])

    with row2_1:
        st.subheader("📈 แนวโน้มการดำเนินงานและรายได้รายเดือน")
        if 'Year_Month' in df.columns and 'Revenue_THB' in df.columns:
            monthly = df.groupby('Year_Month').agg(
                Revenue=('Revenue_THB', 'sum'),
                Fuel_Cost=('Fuel_Cost_THB', 'sum'),
                Trips=('Trip_ID', 'count')
            ).reset_index()
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=monthly['Year_Month'], y=monthly['Revenue'], name='รายได้ (บาท)', marker_color='#00D4B1'))
            fig_trend.add_trace(go.Bar(x=monthly['Year_Month'], y=monthly['Fuel_Cost'], name='ค่าน้ำมัน (บาท)', marker_color='#FF5252'))
            fig_trend.update_layout(barmode='group', height=330, margin=dict(t=20, b=20, l=20, r=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_trend, use_container_width=True)

    with row2_2:
        st.subheader("⚡ อัตราสิ้นเปลืองน้ำมันเฉลี่ยแยกตามประเภทรถ (km/L)")
        if 'Vehicle_Type' in df.columns and 'Distance_km' in df.columns and 'Fuel_Liters' in df.columns:
            eff_df = df.groupby('Vehicle_Type').agg(
                Total_Dist=('Distance_km', 'sum'),
                Total_Fuel=('Fuel_Liters', 'sum')
            ).reset_index()
            eff_df['KM_per_Liter'] = eff_df['Total_Dist'] / eff_df['Total_Fuel']
            
            fig_eff = px.bar(
                eff_df, 
                x='Vehicle_Type', 
                y='KM_per_Liter',
                color='KM_per_Liter',
                color_continuous_scale='Tealgrn',
                text_auto='.2f',
                labels={'Vehicle_Type':'ประเภทรถ', 'KM_per_Liter':'กม. / ลิตร'}
            )
            fig_eff.update_layout(height=330, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_eff, use_container_width=True)

else:
    st.info("💡 ไม่พบข้อมูลในฐานข้อมูล กรุณาไปที่หน้า Import Data เพื่อนำเข้าไฟล์ Excel")
