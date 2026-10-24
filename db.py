import sqlite3
import pandas as pd

DB_Name = "transport.db"


def get_fixed_depreciation(vehicle_type):
  """ค่าเสื่อมสภาพเหมาจ่ายต่อเที่ยวแยกตามประเภทรถ"""
  rates = {"4W": 250.0, "6W": 500.0, "10W": 800.0}
  return rates.get(str(vehicle_type).upper(), 500.0)


def process_and_save_excel(file_path):
  """ประมวลผลไฟล์ Excel คำนวณต้นทุน/ค่าเสื่อม และบันทึกลง transport.db"""
  df = pd.read_excel(file_path, sheet_name="Trips")

  # จัดรูปแบบวันที่และเวลา
  df["Trip_Date"] = pd.to_datetime(df["Trip_Date"]).dt.date
  for col in [
      "Departure_Time",
      "Actual_Delivery",
      "Scheduled_Delivery",
      "Completion_Time",
  ]:
    if col in df.columns:
      df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime(
          "%H:%M:%S"
      )

  # คำนวณค่าเสื่อมตามประเภทรถ
  df["Maintenance_Allocated_THB_Per_Trip"] = df["Vehicle_Type"].apply(
      get_fixed_depreciation
  )

  # คำนวณต้นทุนผันแปร
  df["Variable_Cost_THB"] = (
      df["Fuel_Cost_THB"].fillna(0)
      + df["Driver_Allowance_THB"].fillna(0)
      + df["Tollway_Cost_THB"].fillna(0)
      + df["Other_Variable_Cost_THB"].fillna(0)
  )

  # ต้นทุนปันส่วน
  df["Allocated_Cost_THB"] = df[
      "Maintenance_Allocated_THB_Per_Trip"
  ].fillna(0) + df["Insurance_Allocated_THB"].fillna(0)

  # ต้นทุนรวมและกำไร
  df["Total_Recorded_Cost_THB"] = (
      df["Variable_Cost_THB"] + df["Allocated_Cost_THB"]
  )
  df["Revenue_THB"] = df["Agreed_Price_THB"]
  df["Profit_THB"] = df["Revenue_THB"] - df["Total_Recorded_Cost_THB"]

  df["Profit_Margin"] = df.apply(
      lambda r: (r["Profit_THB"] / r["Revenue_THB"])
      if r["Revenue_THB"] > 0
      else 0,
      axis=1,
  )
  df["Profit_per_km"] = df.apply(
      lambda r: (r["Profit_THB"] / r["Distance_km"])
      if r["Distance_km"] > 0
      else 0,
      axis=1,
  )

  # จัดเรียงคอลัมน์เวลาให้อยู่ชิดกัน
  time_cols = [
      "Departure_Time",
      "Actual_Delivery",
      "Scheduled_Delivery",
      "Completion_Time",
  ]
  current_cols = [c for c in df.columns if c not in time_cols]
  if "Trip_Date" in current_cols:
    idx = current_cols.index("Trip_Date") + 1
    new_cols = current_cols[:idx] + time_cols + current_cols[idx:]
  else:
    new_cols = current_cols + time_cols
  df = df[new_cols]

  # บันทึกลง SQLite
  conn = sqlite3.connect(DB_Name)
  df.to_sql("Trips", conn, if_exists="replace", index=False)
  conn.close()
  return len(df)


def load_data_from_db():
  """ดึงข้อมูลจากฐานข้อมูล transport.db มาใช้งานในหน้าเว็บต่างๆ"""
  conn = sqlite3.connect(DB_Name)
  try:
    df = pd.read_sql_query("SELECT * FROM Trips", conn)
  except Exception:
    df = pd.DataFrame()
  conn.close()
  return df
