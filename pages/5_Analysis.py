import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Analysis", layout="wide")
st.title("📈 5. Analysis - แนวโน้มและเปรียบเทียบข้อมูล")

conn = sqlite3.connect('transport.db')
try:
    df = pd.read_sql("SELECT * FROM shipments", conn)
except Exception:
    df = pd.DataFrame()
conn.close()

if not df.empty:
    st.subheader("📈 แนวโน้มและเปรียบเทียบข้อมูล")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**ระยะทางขนส่งตามเส้นทาง (Top 10)**")
        if 'Route_Code' in df.columns and 'Distance_km' in df.columns:
            route_dist = df.groupby('Route_Code')['Distance_km'].sum().reset_index().sort_values(by='Distance_km', ascending=False).head(10)
            fig1 = px.bar(route_dist, x='Route_Code', y='Distance_km', labels={'Route_Code':'เส้นทาง', 'Distance_km':'ระยะทางรวม (กม.)'})
            st.plotly_chart(fig1, use_container_width=True)
            
    with c2:
        st.markdown("**จำนวนเที่ยวตามประเภทรถ**")
        if 'Vehicle_Type' in df.columns:
            fig2 = px.pie(df, names='Vehicle_Type', title='สัดส่วนประเภทรถที่ใช้ปฏิบัติงาน')
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📋 ตารางรายละเอียดการวิเคราะห์")
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("💡 ไม่พบข้อมูลสำหรับวิเคราะห์")
