import streamlit as st

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="เข้าสู่ระบบ - ระบบบริหารจัดการการขนส่ง", page_icon="🔒")

# สร้างตัวแปรเช็กสถานะการเข้าสู่ระบบ
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# หน้าเข้าสู่ระบบ
if not st.session_state.logged_in:
    st.title("🔒 เข้าสู่ระบบก่อนใช้งาน")
    st.caption("ระบบวิเคราะห์และติดตามข้อมูลด้านการขนส่ง — บริษัท ABC")
    
    username = st.text_input("ชื่อผู้ใช้งาน (Username)")
    password = st.text_input("รหัสผ่าน (Password)", type="password")
    
    if st.button("เข้าสู่ระบบ", type="primary"):
        # กำหนด Username / Password สำหรับทดสอบเข้าใช้งาน
        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.success("เข้าสู่ระบบสำเร็จ!")
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")
            
    # คำสั่งหยุดการทำงานของโค้ดส่วนอื่น เพื่อไม่ให้โหลดเมนู/ข้อมูลด้านหลัง
    st.stop()

# หากเข้าสู่ระบบแล้ว จะแสดงข้อความต้อนรับ
st.title("🚚 ยินดีต้อนรับเข้าสู่ระบบบริหารจัดการการขนส่ง")
st.success("คุณได้เข้าสู่ระบบเรียบร้อยแล้ว สามารถเลือกเมนูวิเคราะห์ข้อมูลจากแถบด้านข้างได้เลยครับ")

if st.button("ออกจากระบบ"):
    st.session_state.logged_in = False
    st.rerun()
