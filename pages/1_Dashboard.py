import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Transportation Dashboard", page_icon="📊", layout="wide")

# 2. ปรับแต่งสไตล์ Modern Light UI
st.markdown("""
<style>
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
    }
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .kpi-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.875rem;
        font-weight: 700;
        color: #0F172A;
    }
    .kpi-sub {
        font-size: 0.8rem;
        font-weight: 500;
        color: #10B981;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# 3. ดึงข้อมูลจากฐานข้อมูล SQLite
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

# 4. แสดงส่วนหัวของ Dashboard
st.markdown("<h2 style='color:#0F172A; font-weight:800; margin-bottom: 0px;'>📊 Logistics & Transportation Analytics</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748B; margin-bottom: 24px;'>ภาพรวมประสิทธิภาพการขนส่ง ต้นทุนเชื้อเพลิง และการปล่อยก๊าซเรือนกระจก — บริษัท ABC</p>", unsafe_allow_html=True)

if not raw_df.empty:
    # --- Sidebar Filters ---
    st.sidebar.markdown("### 🎯 ตัวกรองข้อมูล")
    
    min_date = raw_df['Trip_Date'].min() if 'Trip_Date' in raw_df.columns else None
    max_date = raw_df['Trip_Date'].max() if 'Trip_Date' in raw_df.columns else None
    
    if min_date and max_date:
        date_range = st.sidebar.date_input(
            "ช่วงวันที่:",
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

    st.sidebar.caption(f"📌 แสดงข้อมูล **{len(df):,}** / {len(raw_df):,} รายการ")

    # --- KPI Summary Calculation ---
    total_trips = len(df)
    total_distance = df['Distance_km'].sum() if 'Distance_km' in df.columns else 0
    total_fuel = df['Fuel_Liters'].sum() if 'Fuel_Liters' in df.columns else 0
    avg_efficiency = (total_distance / total_fuel) if total_fuel > 0 else 0
    co2_emission = (total_fuel * 2.68) / 1000

    total_revenue = df['Revenue_THB'].sum() if 'Revenue_THB' in df.columns else 0
    total_fuel_cost = df['Fuel_Cost_THB'].sum() if 'Fuel_Cost_THB' in df.columns else 0
    total_profit = df['Profit_THB'].sum() if 'Profit_THB' in df.columns else (total_revenue - total_fuel_cost)
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

    # --- Top KPI Cards ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">📦 เที่ยววิ่งรวมทั้งหมด</div>
            <div class="kpi-value">{total_trips:,} <span style="font-size:1rem; color:#64748B;">เที่ยว</span></div>
            <div class="kpi-sub">ระยะทางรวม {total_distance:,.0f} กม.</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">⚡ อัตราสิ้นเปลืองเฉลี่ย</div>
            <div class="kpi-value">{avg_efficiency:.2f} <span style="font-size:1rem; color:#64748B;">กม./ลิตร</span></div>
            <div class="kpi-sub">ปริมาณน้ำมัน {total_fuel:,.0f} ลิตร</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">💰 รายได้รวมการขนส่ง</div>
            <div class="kpi-value">฿{total_revenue/1e3:,.1f}k</div>
            <div class="kpi-sub">ค่าน้ำมัน ฿{total_fuel_cost/1e3:,.1f}k</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">🌿 การปล่อยคาร์บอน (CO₂)</div>
            <div class="kpi-value">{co2_emission:,.2f} <span style="font-size:1rem; color:#64748B;">ตัน</span></div>
            <div class="kpi-sub" style="color:#2563EB;">Profit Margin: {profit_margin:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # --- Charts Section 1 ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📈 แนวโน้มรายได้ และ ค่าน้ำมันเชื้อเพลิงรายเดือน")
        if 'Year_Month' in df.columns and not df.empty:
            monthly = df.groupby('Year_Month').agg(
                Revenue=('Revenue_THB', 'sum'),
                Fuel_Cost=('Fuel_Cost_THB', 'sum')
            ).reset_index()
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=monthly['Year_Month'], y=monthly['Revenue'], name='รายได้ (บาท)', marker_color='#2563EB'))
            fig_trend.add_trace(go.Bar(x=monthly['Year_Month'], y=monthly['Fuel_Cost'], name='ค่าน้ำมัน (บาท)', marker_color='#F59E0B'))
            
            fig_trend.update_layout(
                template="plotly_white",
                barmode='group',
                height=300,
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    with col_right:
        st.markdown("#### 🚚 สัดส่วนประเภทรถที่ใช้ในการขนส่ง")
        if 'Vehicle_Type' in df.columns and not df.empty:
            vtype_counts = df['Vehicle_Type'].value_counts().reset_index()
            vtype_counts.columns = ['Vehicle_Type', 'Count']
            
            fig_pie = px.pie(
                vtype_counts, 
                names='Vehicle_Type', 
                values='Count',
                hole=0.5,
                template="plotly_white",
                color_discrete_sequence=['#3B82F6', '#10B981', '#F59E0B', '#6366F1']
            )
            fig_pie.update_layout(
                height=300,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- Charts Section 2 ---
    col_b1, col_b2 = st.columns(2)

    with col_b1:
        st.markdown("#### 📍 Top 10 เส้นทางที่มีเที่ยววิ่งมากที่สุด")
        if 'Route_Code' in df.columns and not df.empty:
            top_routes = df['Route_Code'].value_counts().head(10).reset_index()
            top_routes.columns = ['Route_Code', 'Trips']
            
            fig_route = px.bar(
                top_routes, 
                x='Trips', 
                y='Route_Code', 
                orientation='h',
                template="plotly_white",
                color='Trips',
                color_continuous_scale='Blues',
                text='Trips'
            )
            fig_route.update_layout(
                yaxis=dict(autorange="reversed"),
                height=300,
                margin=dict(t=10, b=10, l=10, r=10),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_route, use_container_width=True)

    with col_b2:
        st.markdown("#### ⚡ อัตราสิ้นเปลืองน้ำมันแยกตามประเภทรถ (กม./ลิตร)")
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
                template="plotly_white",
                color='KM_per_Liter',
                color_continuous_scale='Emerald',
                text='KM_per_Liter'
            )
            fig_eff.update_layout(
                height=300,
                margin=dict(t=10, b=10, l=10, r=10),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_eff, use_container_width=True)

else:
    st.info("💡 ไม่พบข้อมูลในระบบ กรุณาอัปโหลดไฟล์ในหน้า Import Data")
