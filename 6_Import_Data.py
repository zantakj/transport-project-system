import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Import Data", page_icon="📥", layout="wide")
st.title("📥 6. Import Data - นำเข้าข้อมูลการขนส่ง")

if not st.session_state.get("logged_in", False):
    st.warning("กรุณา Login ที่หน้าหลักก่อนใช้งาน")
    st.stop()

DB_NAME = "transport.db"


def init_db():
    """สร้างตารางรองรับข้อมูลการขนส่งจาก Excel"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_no TEXT,
            open_date TEXT,
            ship_date TEXT,
            trip_type TEXT,
            status TEXT,
            route_code TEXT,
            route_name TEXT,
            route_type TEXT,
            distance REAL,
            plate_no TEXT,
            vehicle_type TEXT,
            vendor_code TEXT,
            vendor_name TEXT
        )
    """
    )
    conn.commit()
    conn.close()


init_db()

uploaded_file = st.file_uploader(
    "อัปโหลดไฟล์ Excel จากบริษัท (.xlsx / .xls)", type=["xlsx", "xls"]
)

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.subheader("📋 ตรวจสอบข้อมูลก่อนบันทึก")
        st.dataframe(df.head(10))

        if st.button("📥 บันทึกเข้า Database (SQLite)", type="primary"):
            conn = sqlite3.connect(DB_NAME)

            # Mapping คอลัมน์จาก Excel ภาษาไทย ให้เป็นชื่อคอลัมน์ใน DB
            column_mapping = {
                "เลขที่ใบเที่ยวรถ": "trip_no",
                "วันที่เปิด": "open_date",
                "วันที่ขนส่ง": "ship_date",
                "ประเภทเที่ยวรถ": "trip_type",
                "สถานะ": "status",
                "รหัสเส้นทาง": "route_code",
                "ชื่อเส้นทาง": "route_name",
                "ประเภทเส้นทาง": "route_type",
                "ระยะทาง": "distance",
                "ทะเบียนรถ": "plate_no",
                "ประเภทรถ": "vehicle_type",
                "รหัสบริษัทรถ": "vendor_code",
                "ชื่อบริษัทรถ": "vendor_name",
                "ชื่อสถานที่ส่งสินค้า": "route_name",  # รองรับชื่อหัวคอลัมน์อีกรูปแบบ
            }

            # แปลงชื่อคอลัมน์
            df_mapped = df.rename(columns=column_mapping)

            # คัดเลือกเฉพาะคอลัมน์ที่มีอยู่ในโครงสร้างตาราง DB
            allowed_cols = [
                "trip_no",
                "open_date",
                "ship_date",
                "trip_type",
                "status",
                "route_code",
                "route_name",
                "route_type",
                "distance",
                "plate_no",
                "vehicle_type",
                "vendor_code",
                "vendor_name",
            ]
            valid_cols = [c for c in df_mapped.columns if c in allowed_cols]
            df_to_save = df_mapped[valid_cols]

            # บันทึกลงตาราง shipments
            df_to_save.to_sql("shipments", conn, if_exists="append", index=False)
            conn.close()

            st.balloons()
            st.success("บันทึกข้อมูลเข้าฐานข้อมูลเรียบร้อยแล้ว! 🎉")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")