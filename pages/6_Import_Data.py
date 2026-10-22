import sqlite3
import pandas as pd
import streamlit as st

# 🚨 ระบบป้องกันขั้นที่ 2
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⛔ กรุณาเข้าสู่ระบบก่อนใช้งานหน้านี้")
    st.stop()

st.set_page_config(page_title="Import Data", page_icon="📥", layout="wide")

st.title("📥 นำเข้าข้อมูลการขนส่ง (Import Data)")
st.caption("อัปโหลดไฟล์ Excel เลือก Sheet และเลือกเฉพาะหัวข้อ/คอลัมน์ที่ต้องการนำเข้าลงฐานข้อมูล")

uploaded_file = st.file_uploader("เลือกไฟล์ Excel ข้อมูลการขนส่ง", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # 1. โหลดรายชื่อ Sheet ทั้งหมดในไฟล์ Excel
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names
        
        st.divider()
        col_sheet, col_header = st.columns([1, 1])
        
        with col_sheet:
            selected_sheet = st.selectbox("📌 เลือก Sheet ที่ต้องการดึงข้อมูล:", sheet_names)
            
        with col_header:
            header_row = st.number_input("📌 บรรทัดที่เป็นหัวข้อคอลัมน์ (Header Row Index):", min_value=0, value=0, help="หากแถวแรกๆ เป็นคำอธิบาย ให้ปรับเป็นบรรทัดหัวข้อจริง")

        # อ่านข้อมูลตาม Sheet และ Header ที่เลือก
        raw_df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, header=header_row)
        
        # ทำความสะอาดชื่อคอลัมน์
        raw_df.columns = [str(col).strip() for col in raw_df.columns]

        if not raw_df.empty:
            st.markdown("---")
            st.subheader("🎯 เลือกหัวข้อ/คอลัมน์ที่ต้องการใช้")
            
            all_columns = list(raw_df.columns)
            selected_columns = st.multiselect(
                "เลือกคอลัมน์ที่จะนำเข้าลงระบบ (สามารถลบ/เพิ่มได้ตามต้องการ):",
                options=all_columns,
                default=all_columns
            )

            if selected_columns:
                # กรองเฉพาะคอลัมน์ที่เลือก
                filtered_df = raw_df[selected_columns].dropna(how='all')

                st.markdown(f"#### 📋 พรีวิวข้อมูลที่จะนำเข้า ({len(filtered_df):,} รายการ):")
                st.dataframe(filtered_df.head(10), use_container_width=True)

                if st.button("💾 ยืนยันบันทึกข้อมูลที่เลือกลงฐานข้อมูล", type="primary", use_container_width=True):
                    conn = sqlite3.connect('transport.db')
                    cursor = conn.cursor()
                    
                    # ล้างข้อมูลเก่า
                    cursor.execute("DELETE FROM shipments")
                    conn.commit()
                    
                    # บันทึกข้อมูลเฉพาะคอลัมน์ที่เลือก
                    filtered_df.to_sql('shipments', conn, if_exists='replace', index=False)
                    conn.close()
                    
                    # เคลียร์ Cache ของ Streamlit
                    st.cache_data.clear()
                    
                    st.balloons()
                    st.success("🎉 บันทึกข้อมูลที่เลือกเข้าสู่ระบบเรียบร้อยแล้ว! สามารถสลับไปหน้า Dashboard เพื่อดูผลวิเคราะห์ได้เลยครับ")
            else:
                st.warning("⚠️ กรุณาเลือกอย่างน้อย 1 คอลัมน์เพื่อนำเข้าข้อมูล")

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
