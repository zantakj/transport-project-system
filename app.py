import streamlit as st

import auth
import database as db

st.set_page_config(page_title="ระบบวิเคราะห์และติดตามข้อมูลการขนส่ง", page_icon="🚛", layout="wide")
db.init_db()
auth.ensure_default_admin()


def login_page():
  st.markdown("<div style='height:6vh'></div>", unsafe_allow_html=True)
  _, mid, _ = st.columns([1, 1.2, 1])
  with mid:
    st.markdown("## 🚛 ระบบวิเคราะห์และติดตามข้อมูลการขนส่ง")
    st.caption("กรุณาเข้าสู่ระบบด้วยชื่อผู้ใช้และรหัสผ่าน")
    with st.form("login"):
      u = st.text_input("ชื่อผู้ใช้")
      pw = st.text_input("รหัสผ่าน", type="password")
      ok = st.form_submit_button("เข้าสู่ระบบ", type="primary", width="stretch")
    if ok:
      role = auth.verify(u, pw)
      if role:
        st.session_state.update(user=u.strip(), role=role)
        st.rerun()
      else:
        st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")


if "user" not in st.session_state:
  st.navigation([st.Page(login_page, title="เข้าสู่ระบบ", icon="🔐")]).run()
  st.stop()

admin = st.session_state["role"] == "admin"
with st.sidebar:
  st.markdown(f"👤 **{st.session_state['user']}** · {auth.ROLES[st.session_state['role']]}")
  if st.button("ออกจากระบบ", width="stretch"):
    st.session_state.clear()
    st.rerun()

data_pages = [st.Page("pages/quality.py", title="ตรวจคุณภาพข้อมูล", icon="🧪")]
if admin:
  data_pages.insert(0, st.Page("pages/import_data.py", title="นำเข้าข้อมูล", icon="📥"))

pg = st.navigation({
    "ภาพรวม": [st.Page("pages/dashboard.py", title="ภาพรวม (Dashboard)", icon="📊", default=True)],
    "วิเคราะห์": [
        st.Page("pages/daily.py", title="ข้อมูลการปฏิบัติงานรายวัน", icon="📋"),
        st.Page("pages/vehicle.py", title="ยานพาหนะ", icon="🚚"),
        st.Page("pages/branch.py", title="วิเคราะห์ตามสาขา", icon="🏬"),
        st.Page("pages/cost.py", title="ต้นทุนและกำไร", icon="💰"),
        st.Page("pages/carbon.py", title="น้ำมันและคาร์บอน", icon="🌿"),
    ],
    "ข้อมูล": data_pages,
    "ตั้งค่า": [st.Page("pages/settings.py", title="ตั้งค่าพารามิเตอร์", icon="⚙️")],
})
pg.run()
