import plotly.express as px
import streamlit as st

import calculations as calc
from common import COLORS, PLOT, get_data, sidebar_filters, to_display

st.title("🏬 วิเคราะห์ตามสาขา")
st.caption("ข้อมูลของบริษัทไม่มีเส้นทางรายเที่ยว จึงวิเคราะห์ตามสาขาต้นทาง (St.) แทน")
t, daily, p, imports = get_data()
df, d, month = sidebar_filters(t, daily)
g = calc.group_summary(df, "Store")

metric = st.selectbox("เรียงสาขาตาม", {
    "Payment_THB": "ค่าใช้จ่ายตาม E-Billing", "Distance_km": "ระยะทาง (กม.)", "Drops": "จุดส่ง",
    "Cost_per_km": "ต้นทุน/กม.", "Cost_per_Drop": "ต้นทุน/จุดส่ง", "CO2_kg": "CO₂e (กก.)",
    "Profit_THB": "กำไรสุทธิ"}.items(), format_func=lambda x: x[1])
top = g.sort_values(metric[0], ascending=False).head(20)
fig = px.bar(top, x=metric[0], y="Store", orientation="h", color_discrete_sequence=[COLORS["primary"]])
fig.update_layout(height=40 + 24 * len(top), yaxis=dict(autorange="reversed", title=""), xaxis_title=metric[1], **PLOT)
st.plotly_chart(fig, width="stretch")

st.markdown("#### ตารางสรุปทุกสาขา")
st.dataframe(to_display(g).round(2), hide_index=True, width="stretch")
