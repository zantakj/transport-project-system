import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Analysis / Visualization", page_icon="📉", layout="wide"
)
st.title("📉 5. Analysis / Visualization - เจาะลึกข้อมูลการขนส่ง")

if not st.session_state.get("logged_in", False):
    st.warning("กรุณา Login ที่หน้าหลักก่อนใช้งาน")
    st.stop()

conn = sqlite3.connect("transport.db")
try:
    df = pd.read_sql_query("SELECT * FROM shipments", conn)
except Exception:
    df = pd.DataFrame()
conn.close()

if df.empty:
    st.info("ยังไม่มีข้อมูลในระบบ กรุณาอัปโหลดข้อมูลที่หน้า 6. Import Data ก่อนครับ")
else:
    st.subheader("🎛️ ตัวเลือกวิเคราะห์ข้อมูล")

    col1, col2 = st.columns(2)
    with col1:
        selected_vehicle = (
            st.selectbox(
                "เลือกรถที่ต้องการวิเคราะห์",
                ["ทั้งหมด"] + list(df["plate_no"].dropna().unique()),
            )
            if "plate_no" in df
            else "ทั้งหมด"
        )
    with col2:
        selected_vendor = (
            st.selectbox(
                "เลือกบริษัทรถ",
                ["ทั้งหมด"] + list(df["vendor_name"].dropna().unique()),
            )
            if "vendor_name" in df
            else "ทั้งหมด"
        )

    filtered_df = df.copy()
    if selected_vehicle != "ทั้งหมด" and "plate_no" in filtered_df:
        filtered_df = filtered_df[filtered_df["plate_no"] == selected_vehicle]
    if selected_vendor != "ทั้งหมด" and "vendor_name" in filtered_df:
        filtered_df = filtered_df[filtered_df["vendor_name"] == selected_vendor]

    st.divider()

    st.subheader("📈 แนวโน้มและเปรียบเทียบข้อมูล")
    c1, c2 = st.columns(2)

    with c1:
        st.write("#### ระยะทางขนส่งตามเส้นทาง / ปลายทาง")
        # รองรับทั้งชื่อ route_name และ destination
        route_col = (
            "route_name"
            if "route_name" in filtered_df
            else ("destination" if "destination" in filtered_df else None)
        )
        if route_col and "distance" in filtered_df:
            chart_data = filtered_df.groupby(route_col)["distance"].sum()
            st.bar_chart(chart_data)
        else:
            st.info("ไม่มีข้อมูลระยะทางหรือเส้นทาง")

    with c2:
        st.write("#### จำนวนเที่ยวตามประเภทรถ")
        if "vehicle_type" in filtered_df:
            st.line_chart(filtered_df["vehicle_type"].value_counts())
        else:
            st.info("ไม่มีข้อมูลประเภทรถ")

    st.write("#### ตารางรายละเอียดการวิเคราะห์")
    st.dataframe(filtered_df, use_container_width=True)