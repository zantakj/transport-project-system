"""
calculations.py — แกนการคำนวณของระบบ (ใช้ร่วมกันทุกหน้า)

โครงสร้างต้นทุน (ต้องอธิบายทฤษฎีในเล่ม):
  ต้นทุนผันแปร (Variable cost) ต่อเที่ยว
    ค่าน้ำมัน      = ลิตร × ราคาน้ำมัน
    ค่ายาง         = ระยะทาง × (จำนวนยาง × ราคายาง ÷ อายุยาง กม.)
    ค่าน้ำมันเครื่อง = ระยะทาง × (ค่าเปลี่ยนต่อครั้ง ÷ ระยะเปลี่ยน กม.)
    ค่าซ่อมบำรุง   = ระยะทาง × บาท/กม.
    ค่าทางด่วน + เบี้ยเลี้ยงคนขับ (ตามที่บันทึกในเที่ยว)
  ต้นทุนคงที่ (Fixed cost) ต่อคันต่อเดือน
    ค่าเสื่อมราคาแบบเส้นตรง = (ราคาซื้อ − มูลค่าซาก) ÷ อายุใช้งาน ÷ 12
    ประกัน/ภาษี = ต่อปี ÷ 12
    เงินเดือนคนขับ (เฉพาะรถ Active)
  การปันส่วน (Allocation)
    ต้นทุนคงที่ของรถแต่ละคันในเดือนนั้น → กระจายให้เที่ยวของรถคันนั้นตามสัดส่วนระยะทาง
    ต้นทุนคงที่ของรถที่ไม่มีเที่ยววิ่ง (รถจอด/สำรอง) = "ต้นทุนรถว่าง (Idle cost)"
      → กระจายให้ทุกเที่ยวของรถประเภทเดียวกันในเดือนนั้นตามสัดส่วนระยะทาง
  ผลคือ ผลรวมต้นทุนรายเที่ยว = ต้นทุนทั้งบริษัท (ไม่มีต้นทุนหายไป)
"""
import numpy as np
import pandas as pd

TIME_COLS = ["Departure_Time", "Scheduled_Delivery", "Actual_Delivery", "Completion_Time"]


def _months_in_data(trips):
  periods = trips["Trip_Date"].dt.to_period("M")
  return pd.period_range(periods.min(), periods.max(), freq="M")


def monthly_fixed_costs(vehicles, cost_params, months):
  """ต้นทุนคงที่ของรถ "ทุกคัน" ในแต่ละเดือน (รวมรถที่จอดไว้)"""
  v = vehicles.merge(cost_params, on="Vehicle_Type", how="left")
  v["Purchase_Date"] = pd.to_datetime(v["Purchase_Date"], errors="coerce")
  rows = []
  for m in months:
    month_start = m.start_time
    for _, r in v.iterrows():
      if pd.notna(r.Purchase_Date) and r.Purchase_Date > m.end_time:
        continue  # ยังไม่ได้ซื้อรถ
      life_months = r.Useful_Life_Years * 12
      age_months = (
          (month_start.year - r.Purchase_Date.year) * 12
          + month_start.month - r.Purchase_Date.month
          if pd.notna(r.Purchase_Date) else 0
      )
      dep = (
          (r.Purchase_Price_THB - r.Salvage_Value_THB) / life_months
          if age_months < life_months else 0.0  # หมดอายุ → ไม่มีค่าเสื่อมแล้ว
      )
      rows.append(dict(
          Year_Month=str(m), Vehicle_Code=r.Vehicle_Code,
          Vehicle_Type=r.Vehicle_Type, Status=r.Status,
          Depreciation_THB=dep,
          Insurance_THB=r.Insurance_Tax_THB_per_Year / 12,
          Driver_Salary_THB=(
              r.Driver_Salary_THB_per_Month if r.Status == "Active" else 0.0
          ),
      ))
  out = pd.DataFrame(rows)
  out["Fixed_Cost_THB"] = out[["Depreciation_THB", "Insurance_THB", "Driver_Salary_THB"]].sum(axis=1)
  return out


def build_trip_costs(tables):
  """คืน (trips_ที่คำนวณแล้ว, ต้นทุนคงที่รายคันรายเดือน)"""
  t = tables["Trips"].copy()
  vehicles, routes = tables["Vehicles"], tables["Routes"]
  cp, ef = tables["Cost_Parameters"], tables["Emission_Factors"]

  t["Trip_Date"] = pd.to_datetime(t["Trip_Date"], errors="coerce")
  t["Year_Month"] = t["Trip_Date"].dt.strftime("%Y-%m")
  for c in TIME_COLS:
    if c in t.columns:
      t[c] = pd.to_datetime(t[c], errors="coerce")

  done = t["Job_Status"].eq("Completed")
  t = t.merge(cp, on="Vehicle_Type", how="left")
  t = t.merge(vehicles[["Vehicle_Code", "Fuel_Type"]], on="Vehicle_Code", how="left")
  t = t.merge(ef[["Fuel_Type", "kgCO2_per_L"]], on="Fuel_Type", how="left")
  route_cols = [c for c in ["Route_Code", "One_Way_km", "Destination_Province_TH", "Delivery_Area"] if c in routes.columns]
  t = t.merge(routes[route_cols], on="Route_Code", how="left")
  done = t["Job_Status"].eq("Completed")

  km = t["Distance_km"].fillna(0)
  # ---------- ต้นทุนผันแปร ----------
  t["Revenue_THB"] = np.where(done, t["Agreed_Price_THB"], 0.0)
  t["Fuel_Cost_THB"] = t["Fuel_Liters"].fillna(0) * t["Fuel_Price_THB_per_L"].fillna(0)
  t["Tire_Cost_THB"] = km * t["Tire_Count"] * t["Tire_Price_THB"] / t["Tire_Life_km"]
  t["Oil_Cost_THB"] = km * t["Oil_Change_Cost_THB"] / t["Oil_Change_Interval_km"]
  t["Repair_Cost_THB"] = km * t["Repair_THB_per_km"]
  var_cols = ["Fuel_Cost_THB", "Tire_Cost_THB", "Oil_Cost_THB", "Repair_Cost_THB",
              "Toll_THB", "Driver_Allowance_THB"]
  t["Variable_Cost_THB"] = t[var_cols].fillna(0).sum(axis=1)

  # ---------- ต้นทุนคงที่ + การปันส่วน ----------
  fixed = monthly_fixed_costs(vehicles, cp, _months_in_data(t))
  km_by_vm = t[done].groupby(["Year_Month", "Vehicle_Code"])["Distance_km"].sum().rename("VM_km")
  km_by_tm = t[done].groupby(["Year_Month", "Vehicle_Type"])["Distance_km"].sum().rename("TM_km")
  fixed = fixed.merge(km_by_vm, on=["Year_Month", "Vehicle_Code"], how="left")
  fixed["VM_km"] = fixed["VM_km"].fillna(0)
  # รถที่ไม่มีเที่ยววิ่งในเดือนนั้น → ต้นทุนทั้งหมดเป็น Idle cost ของประเภทรถนั้น
  idle_pool = (
      fixed[fixed["VM_km"] == 0]
      .groupby(["Year_Month", "Vehicle_Type"])["Fixed_Cost_THB"].sum().rename("Idle_Pool")
  )

  t = t.merge(fixed[["Year_Month", "Vehicle_Code", "Depreciation_THB", "Insurance_THB",
                     "Driver_Salary_THB", "VM_km"]],
              on=["Year_Month", "Vehicle_Code"], how="left")
  t = t.merge(km_by_tm, on=["Year_Month", "Vehicle_Type"], how="left")
  t = t.merge(idle_pool, on=["Year_Month", "Vehicle_Type"], how="left")

  share_own = np.where(done & (t["VM_km"] > 0), km / t["VM_km"], 0.0)
  share_type = np.where(done & (t["TM_km"] > 0), km / t["TM_km"], 0.0)
  for c in ["Depreciation_THB", "Insurance_THB", "Driver_Salary_THB"]:
    t[c] = t[c].fillna(0) * share_own
  t["Idle_Cost_THB"] = t["Idle_Pool"].fillna(0) * share_type
  t["Fixed_Cost_THB"] = t[["Depreciation_THB", "Insurance_THB", "Driver_Salary_THB", "Idle_Cost_THB"]].sum(axis=1)

  # ---------- ผลลัพธ์ ----------
  t["Total_Cost_THB"] = t["Variable_Cost_THB"] + t["Fixed_Cost_THB"]
  t["Profit_THB"] = t["Revenue_THB"] - t["Total_Cost_THB"]
  t["Profit_Margin"] = np.where(t["Revenue_THB"] > 0, t["Profit_THB"] / t["Revenue_THB"] * 100, 0.0)
  t["Cost_per_km"] = np.where(km > 0, t["Total_Cost_THB"] / km, np.nan)
  t["Revenue_per_km"] = np.where(km > 0, t["Revenue_THB"] / km, np.nan)
  t["km_per_L"] = np.where(t["Fuel_Liters"] > 0, km / t["Fuel_Liters"], np.nan)
  t["CO2_kg"] = t["Fuel_Liters"].fillna(0) * t["kgCO2_per_L"].fillna(0)
  if "Load_kg" in t.columns and "One_Way_km" in t.columns:
    # ton-km ของเที่ยวขาไป (ขากลับวิ่งรถเปล่า)
    t["Ton_km"] = t["Load_kg"].fillna(0) / 1000 * t["One_Way_km"].fillna(0)
  if {"Actual_Delivery", "Scheduled_Delivery"} <= set(t.columns):
    t["On_Time"] = np.where(
        done & t["Actual_Delivery"].notna(),
        t["Actual_Delivery"] <= t["Scheduled_Delivery"], np.nan)

  t = t.drop(columns=["VM_km", "TM_km", "Idle_Pool"])
  return t, fixed.drop(columns=["VM_km"])


def summarize(df, by):
  """สรุปตัวชี้วัดตามกลุ่ม (เช่น ประเภทรถ / เส้นทาง)"""
  d = df[df["Job_Status"] == "Completed"]
  g = d.groupby(by).agg(
      Trips=("Trip_ID", "count"), Distance_km=("Distance_km", "sum"),
      Fuel_Liters=("Fuel_Liters", "sum"), Revenue_THB=("Revenue_THB", "sum"),
      Variable_Cost_THB=("Variable_Cost_THB", "sum"), Fixed_Cost_THB=("Fixed_Cost_THB", "sum"),
      Total_Cost_THB=("Total_Cost_THB", "sum"), Profit_THB=("Profit_THB", "sum"),
      CO2_kg=("CO2_kg", "sum"),
  ).reset_index()
  g["Profit_Margin"] = np.where(g["Revenue_THB"] > 0, g["Profit_THB"] / g["Revenue_THB"] * 100, 0)
  g["Cost_per_km"] = g["Total_Cost_THB"] / g["Distance_km"]
  g["Revenue_per_km"] = g["Revenue_THB"] / g["Distance_km"]
  g["km_per_L"] = g["Distance_km"] / g["Fuel_Liters"]
  g["CO2_kg_per_km"] = g["CO2_kg"] / g["Distance_km"]
  return g


def check_route_distances(trips, routes):
  """เที่ยวที่ระยะทางไม่ตรงกับระยะมาตรฐานของเส้นทาง (Route master)"""
  m = trips.merge(routes[["Route_Code", "Round_Trip_km"]], on="Route_Code", how="left")
  m = m[m["Job_Status"] == "Completed"]
  bad = m[(m["Distance_km"] - m["Round_Trip_km"]).abs() > 0.05 * m["Round_Trip_km"]]
  return bad


def price_regression(df):
  """หาความสัมพันธ์ ราคา = a + b × ระยะเที่ยวเดียว แยกประเภทรถ (Least squares)"""
  d = df[(df["Job_Status"] == "Completed") & df["One_Way_km"].notna()]
  rows = []
  for vt, g in d.groupby("Vehicle_Type"):
    if g["One_Way_km"].nunique() < 2:
      continue
    b, a = np.polyfit(g["One_Way_km"], g["Agreed_Price_THB"], 1)
    pred = a + b * g["One_Way_km"]
    ss_res = ((g["Agreed_Price_THB"] - pred) ** 2).sum()
    ss_tot = ((g["Agreed_Price_THB"] - g["Agreed_Price_THB"].mean()) ** 2).sum()
    rows.append(dict(Vehicle_Type=vt, Base_THB=a, THB_per_km=b,
                     R2=1 - ss_res / ss_tot if ss_tot else np.nan, n=len(g)))
  return pd.DataFrame(rows)


def fleet_utilization(trips, vehicles):
  """อัตราการใช้รถ = วันที่มีงาน ÷ วันทำงานในช่วงข้อมูล (จ.–ส.)"""
  d = trips[trips["Job_Status"] == "Completed"]
  start, end = trips["Trip_Date"].min(), trips["Trip_Date"].max()
  workdays = len(pd.bdate_range(start, end, freq="C", weekmask="Mon Tue Wed Thu Fri Sat"))
  used = d.groupby("Vehicle_Code")["Trip_Date"].nunique().rename("Days_Used")
  v = vehicles.set_index("Vehicle_Code").join(used).reset_index()
  v["Days_Used"] = v["Days_Used"].fillna(0).astype(int)
  v["Utilization"] = v["Days_Used"] / workdays * 100
  return v, workdays
