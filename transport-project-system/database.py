import sqlite3

import pandas as pd

DB_PATH = "transport.db"

# ชีตที่ระบบต้องการ และคอลัมน์ขั้นต่ำของแต่ละชีต
REQUIRED_SHEETS = {
    "Trips": [
        "Trip_ID", "Trip_Date", "Vehicle_Code", "Vehicle_Type", "Route_Code",
        "Distance_km", "Fuel_Liters", "Fuel_Price_THB_per_L", "Toll_THB",
        "Driver_Allowance_THB", "Agreed_Price_THB", "Job_Status",
    ],
    "Vehicles": [
        "Vehicle_Code", "Vehicle_Type", "Fuel_Type", "Status", "Purchase_Date",
        "Purchase_Price_THB", "Useful_Life_Years", "Salvage_Value_THB",
    ],
    "Routes": ["Route_Code", "One_Way_km", "Round_Trip_km"],
    "Cost_Parameters": [
        "Vehicle_Type", "Driver_Salary_THB_per_Month",
        "Insurance_Tax_THB_per_Year", "Tire_Count", "Tire_Price_THB",
        "Tire_Life_km", "Oil_Change_Cost_THB", "Oil_Change_Interval_km",
        "Repair_THB_per_km",
    ],
    "Emission_Factors": ["Fuel_Type", "kgCO2_per_L"],
}

# ชื่อคอลัมน์ 2 ภาษา (ใช้แสดงผลทุกหน้า)
COLUMN_LABELS = {
    "Trip_ID": "รหัสเที่ยว", "Trip_Date": "วันที่", "Year_Month": "เดือน",
    "Customer_Code": "รหัสลูกค้า", "Vehicle_Code": "รหัสรถ",
    "Vehicle_Type": "ประเภทรถ", "Route_Code": "รหัสเส้นทาง",
    "Destination_Province_TH": "จังหวัดปลายทาง", "Delivery_Area": "ภาค",
    "Distance_km": "ระยะทางไป-กลับ (กม.)", "One_Way_km": "ระยะเที่ยวเดียว (กม.)",
    "Round_Trip_km": "ระยะไป-กลับ (กม.)", "Load_kg": "น้ำหนักสินค้า (กก.)",
    "Departure_Time": "เวลาออก", "Scheduled_Delivery": "กำหนดส่ง",
    "Actual_Delivery": "ส่งถึงจริง", "Completion_Time": "กลับถึงคลัง",
    "Fuel_Liters": "น้ำมัน (ลิตร)", "Fuel_Price_THB_per_L": "ราคาน้ำมัน (บาท/ลิตร)",
    "Toll_THB": "ค่าทางด่วน (บาท)", "Driver_Allowance_THB": "เบี้ยเลี้ยง (บาท)",
    "Agreed_Price_THB": "ค่าขนส่ง (บาท)", "Job_Status": "สถานะงาน",
    "Revenue_THB": "รายได้ (บาท)", "Fuel_Cost_THB": "ค่าน้ำมัน (บาท)",
    "Tire_Cost_THB": "ค่ายาง (บาท)", "Oil_Cost_THB": "ค่าน้ำมันเครื่อง (บาท)",
    "Repair_Cost_THB": "ค่าซ่อมบำรุง (บาท)", "Variable_Cost_THB": "ต้นทุนผันแปร (บาท)",
    "Depreciation_THB": "ค่าเสื่อมราคา (บาท)", "Insurance_THB": "ประกัน/ภาษี (บาท)",
    "Driver_Salary_THB": "เงินเดือนคนขับ (บาท)", "Idle_Cost_THB": "ต้นทุนรถว่าง/จอด (บาท)",
    "Fixed_Cost_THB": "ต้นทุนคงที่ (บาท)", "Total_Cost_THB": "ต้นทุนรวม (บาท)",
    "Profit_THB": "กำไรสุทธิ (บาท)", "Profit_Margin": "อัตรากำไร (%)",
    "Cost_per_km": "ต้นทุน/กม. (บาท)", "Revenue_per_km": "รายได้/กม. (บาท)",
    "CO2_kg": "CO₂ (กก.)", "km_per_L": "อัตราสิ้นเปลือง (กม./ลิตร)",
    "Load_Factor": "อัตราการบรรทุก (%)", "On_Time": "ส่งตรงเวลา",
    "Trips": "จำนวนเที่ยว", "Status": "สถานะรถ", "Fuel_Type": "ชนิดเชื้อเพลิง",
}


def label(col):
  """คืนชื่อคอลัมน์แบบ 'ชื่อไทย (EN)'"""
  th = COLUMN_LABELS.get(col)
  return f"{th} ({col})" if th else col


def to_display(df):
  return df.rename(columns={c: label(c) for c in df.columns})


def get_connection():
  return sqlite3.connect(DB_PATH)


def validate_workbook(sheets):
  """คืนรายการปัญหา (ชีต/คอลัมน์ที่ขาด) ถ้าไม่มีปัญหาคืน list ว่าง"""
  problems = []
  for sheet, cols in REQUIRED_SHEETS.items():
    if sheet not in sheets:
      problems.append(f"ไม่พบชีต '{sheet}'")
      continue
    missing = [c for c in cols if c not in sheets[sheet].columns]
    if missing:
      problems.append(f"ชีต '{sheet}' ขาดคอลัมน์: {', '.join(missing)}")
  return problems


def save_workbook(sheets):
  """บันทึกทุกชีตที่ระบบใช้ลงฐานข้อมูล คืน dict จำนวนแถวต่อชีต"""
  conn = get_connection()
  counts = {}
  try:
    for name in REQUIRED_SHEETS:
      df = sheets[name].copy()
      df.columns = df.columns.astype(str).str.strip()
      df.to_sql(name, conn, if_exists="replace", index=False)
      counts[name] = len(df)
  finally:
    conn.close()
  return counts


def load_table(name):
  conn = get_connection()
  try:
    return pd.read_sql(f'SELECT * FROM "{name}"', conn)
  except Exception:
    return pd.DataFrame()
  finally:
    conn.close()


def load_all():
  """โหลดทุกตาราง คืน None ถ้ายังนำเข้าข้อมูลไม่ครบ"""
  tables = {name: load_table(name) for name in REQUIRED_SHEETS}
  if any(t.empty for t in tables.values()):
    return None
  return tables


def load_data_from_db():
  return load_table("Trips")
