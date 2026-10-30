"""
calculations.py — สูตรคำนวณของระบบ (ใช้ร่วมกันทุกหน้า)

1) การใช้น้ำมัน
     ลิตร                 = ค่าน้ำมัน (บาท, จากไฟล์) ÷ ราคาน้ำมันของเดือนนั้น (บาท/ลิตร, ผู้ใช้กรอก)
     อัตราสิ้นเปลือง (กม./ลิตร) = ระยะทาง ÷ ลิตร
   หมายเหตุ: ในไฟล์บริษัท ค่าน้ำมัน = paid_distance × อัตราบาท/กม. ตามสัญญา (เช่น 4.18 บาท/กม. ใน มิ.ย.)
   ดังนั้น กม./ลิตรที่ได้คือ "อัตราที่สัญญาใช้คิดเงิน" ไม่ใช่อัตราที่วัดจากการเติมน้ำมันจริง

2) คาร์บอน (Fuel-based method, IPCC 2006 Vol.2 Ch.3 Mobile Combustion)
     CO2e (กก.) = ลิตร × EF (kgCO2e/ลิตร)
   ศักยภาพลดคาร์บอน (ไม่ใช่คาร์บอนเครดิตที่ได้รับรอง)
     ระยะเกินแผน = max(actual_distance − planned_distance, 0)
     CO2e ที่ลดได้ = ระยะเกินแผน ÷ กม./ลิตร × EF
     มูลค่าประมาณการ = CO2e ที่ลดได้ (ตัน) × ราคาเครดิต T-VER

3) ค่าเสื่อมราคา (วิธีเส้นตรง — ระบบคำนวณเอง)
     ค่าเสื่อมต่อคันต่อเดือน = (ราคาทุน − มูลค่าซาก) ÷ (อายุใช้งาน × 12)
     ค่าเสื่อมต่อคันต่อวัน   = ค่าเสื่อมต่อคันต่อเดือน ÷ จำนวนวันในเดือน
     รถที่วิ่งในวันนั้น        = จำนวนคนขับ (Position = Driver) ที่ไม่ซ้ำกันในวันนั้น
     ค่าเสื่อมรถที่วิ่ง          → คิดให้แถวคนขับ 1 คัน-วัน ต่อ 1 แถว
     ต้นทุนรถว่าง             = (รถทั้งหมด − รถที่วิ่ง) × (ค่าเสื่อม + ประกัน) ต่อคันต่อวัน
   นับรถเป็นรายวัน เพราะคนขับหมุนเวียน (มิ.ย. มีคนขับไม่ซ้ำ 221 คน แต่วิ่งพร้อมกันสูงสุด 169 คัน/วัน)

4) กำไรสุทธิ
     รายได้ (ค่าสมมติ)   = ค่าเที่ยว × จำนวนเที่ยว (เฉพาะแถวคนขับ)
     − ค่าใช้จ่ายตาม E-Billing = ยอดรวมทั้งหมด (รวมค่ารถ ค่าน้ำมัน OT Incentive ฯลฯ และหักค่าปรับแล้ว)
     − ค่าซ่อมบำรุง/ยาง  = ระยะทาง × บาท/กม.
     − ค่าเสื่อมราคา และ ประกัน/ภาษีรถ (ของรถที่วิ่ง)
     = กำไรสุทธิรายแถว ;  ระดับบริษัทหักต้นทุนรถว่างเพิ่ม
   ค่าน้ำมันรวมอยู่ในยอดรวมทั้งหมดแล้ว จึงไม่หักซ้ำ
   ถ้าพารามิเตอร์ใดยังไม่มีค่า ระบบจะไม่หักรายการนั้นและแสดงรายชื่อรายการที่ "ยังไม่ได้หัก" กำกับเสมอ
"""
import calendar

import numpy as np
import pandas as pd

COST_ITEMS = {  # คอลัมน์ต้นทุน → (ชื่อ, พารามิเตอร์ที่ต้องมี)
    "Payment_THB": ("ค่าใช้จ่ายตาม E-Billing", None),
    "Maintenance_THB": ("ค่าซ่อมบำรุง/ยาง", "maintenance_km"),
    "Depreciation_THB": ("ค่าเสื่อมราคา", "vehicle_price"),
    "Insurance_THB": ("ประกัน/ภาษีรถ", "insurance_year"),
}


def _nz(x):
  return 0.0 if x is None else x


def depreciation_per_month(p):
  if p.get("vehicle_price") is None or not p.get("useful_life"):
    return None
  return (p["vehicle_price"] - _nz(p.get("salvage_value"))) / (p["useful_life"] * 12)


def missing_deductions(p):
  """รายการต้นทุนที่ยังหักไม่ได้เพราะยังไม่มีพารามิเตอร์"""
  return [name for col, (name, key) in COST_ITEMS.items() if key and p.get(key) is None]


def build(ops, p, fuel_prices, imports):
  """คืน (ตารางรายแถว, ตารางรายวัน)"""
  t = ops.copy()
  if t.empty:
    return t, pd.DataFrame()
  driver = t["Position"].eq("Driver")
  valid_date = ~t["Flags"].str.contains("DATE_INVALID")
  t = t[valid_date].copy()
  driver = driver[valid_date]
  km = t["Distance_km"].fillna(0)

  # ---------- 1) น้ำมัน ----------
  price = t["Year_Month"].map(dict(zip(fuel_prices["year_month"], fuel_prices["price"])))
  t["Fuel_Price"] = price
  t["Fuel_L"] = np.where(price > 0, t["Fuel_Fee"] / price, np.nan)
  t["km_per_L"] = np.where(t["Fuel_L"] > 0, km / t["Fuel_L"], np.nan)

  # ---------- 2) คาร์บอน ----------
  ef = p.get("ef_diesel")
  t["CO2_kg"] = t["Fuel_L"] * ef if ef else np.nan
  planned = t["Planned_km"].where(t["Planned_km"].between(1, 1000))
  t["Excess_km"] = (t["Distance_km"] - planned).clip(lower=0).fillna(0)
  t["CO2_Reducible_kg"] = np.where(t["km_per_L"] > 0, t["Excess_km"] / t["km_per_L"] * (ef or np.nan), 0.0)

  # ---------- 3) ค่าเสื่อม + ประกัน ต่อคัน-วัน ----------
  days_in_month = t["Year_Month"].map(lambda ym: calendar.monthrange(int(ym[:4]), int(ym[5:]))[1])
  dep_m = depreciation_per_month(p)
  dep_day = dep_m / days_in_month if dep_m is not None else np.nan
  ins_day = p["insurance_year"] / 365 if p.get("insurance_year") is not None else np.nan
  # 1 คัน-วัน ต่อคนขับ 1 คนต่อวัน (ถ้ามีหลายแถวในวันเดียวกัน คิดที่แถวแรก)
  first_driver_row = ~t[driver].duplicated(["Work_Date", "Username"])
  t["Vehicle_Day"] = first_driver_row.reindex(t.index, fill_value=False).astype(int)
  t["Depreciation_THB"] = t["Vehicle_Day"] * dep_day
  t["Insurance_THB"] = t["Vehicle_Day"] * ins_day

  # ---------- 4) รายได้ ต้นทุน กำไร ----------
  tp = p.get("trip_price")
  t["Revenue_THB"] = np.where(driver, t["Trips"] * tp, 0.0) if tp is not None else np.nan
  t["Payment_THB"] = t["Total_Payment"]
  t["Maintenance_THB"] = km * p["maintenance_km"] if p.get("maintenance_km") is not None else np.nan
  cost_cols = list(COST_ITEMS)
  t["Total_Cost_THB"] = t[cost_cols].fillna(0).sum(axis=1)  # หักเฉพาะรายการที่มีค่า
  t["Profit_THB"] = t["Revenue_THB"] - t["Total_Cost_THB"]
  t["Cost_per_km"] = np.where(km > 0, t["Total_Cost_THB"] / km, np.nan)

  # ---------- ช่วงกะ ----------
  t["Shift_Group"] = np.select(
      [t["Shift_In_min"] < 6 * 60, t["Shift_In_min"] < 12 * 60, t["Shift_In_min"].notna()],
      ["กะเช้าตรู่ (ก่อน 06:00)", "กะเช้า (06:00–11:59)", "กะบ่าย/ค่ำ (12:00 เป็นต้นไป)"], "ไม่มีข้อมูลเวลา")

  # ---------- รายวัน: รถที่วิ่ง vs รถทั้งหมด ----------
  fleet = dict(zip(imports["year_month"], imports["fleet_total"]))
  daily = (t[t["Vehicle_Day"] == 1].groupby(["Year_Month", "Work_Date"])
           .agg(Active_Vehicles=("Username", "nunique")).reset_index())
  daily["Fleet_Total"] = daily["Year_Month"].map(fleet).fillna(p.get("fleet_total") or 0)
  daily["Idle_Vehicles"] = (daily["Fleet_Total"] - daily["Active_Vehicles"]).clip(lower=0)
  daily["Utilization"] = np.where(daily["Fleet_Total"] > 0, daily["Active_Vehicles"] / daily["Fleet_Total"] * 100, np.nan)
  d_dep = daily["Year_Month"].map(lambda ym: calendar.monthrange(int(ym[:4]), int(ym[5:]))[1])
  if dep_m is None and p.get("insurance_year") is None:
    daily["Idle_Cost_THB"] = np.nan  # ยังไม่มีข้อมูลค่าเสื่อม/ประกัน → แสดงเป็น "รอข้อมูล" ไม่ใช่ 0
  else:
    per_vday = (dep_m / d_dep if dep_m is not None else 0) + (_nz(p.get("insurance_year")) / 365)
    daily["Idle_Cost_THB"] = daily["Idle_Vehicles"] * per_vday
  return t, daily


def kpis(t, daily, p):
  """ตัวเลขสรุปสำหรับการ์ด"""
  drv = t[t["Position"] == "Driver"]
  km = t["Distance_km"].sum()
  k = dict(
      rows=len(t), days=t["Work_Date"].nunique(),
      active_avg=daily["Active_Vehicles"].mean() if len(daily) else 0,
      active_max=daily["Active_Vehicles"].max() if len(daily) else 0,
      fleet=daily["Fleet_Total"].max() if len(daily) else p.get("fleet_total"),
      util=daily["Utilization"].mean() if len(daily) else np.nan,
      km=km, trips=drv["Trips"].sum(), drops=drv["Drops"].sum(),
      payment=t["Payment_THB"].sum(),
      revenue=t["Revenue_THB"].sum(min_count=1),
      cost=t["Total_Cost_THB"].sum(),
      idle=daily["Idle_Cost_THB"].sum(min_count=1) if len(daily) else np.nan,
      fuel_l=t["Fuel_L"].sum(min_count=1), co2=t["CO2_kg"].sum(min_count=1),
      co2_red=t["CO2_Reducible_kg"].sum(min_count=1),
      excess_km=t["Excess_km"].sum(),
      ot=t["OT_Hrs"].sum(), ot_req=t["OT_Request_Hrs"].sum(), ot_appr=t["OT_Approved_Hrs"].sum(),
  )
  k["profit_rows"] = k["revenue"] - k["cost"] if pd.notna(k["revenue"]) else np.nan
  k["profit"] = k["profit_rows"] - (0 if pd.isna(k["idle"]) else k["idle"]) if pd.notna(k["profit_rows"]) else np.nan
  k["km_per_L"] = km / k["fuel_l"] if k["fuel_l"] else np.nan
  return k


def group_summary(t, by):
  """สรุปตามกลุ่ม (สาขา / วัน / กะ ฯลฯ)"""
  drv = t["Position"].eq("Driver")
  sum1 = lambda s: s.sum(min_count=1)  # noqa: E731 — ถ้าไม่มีค่าเลยให้เป็นค่าว่าง ไม่ใช่ 0
  g = t.assign(_trips=t["Trips"].where(drv, 0), _drops=t["Drops"].where(drv, 0)).groupby(by).agg(
      Person_Days=("Username", "size"), Vehicle_Days=("Vehicle_Day", "sum"),
      Trips=("_trips", "sum"), Drops=("_drops", "sum"), Distance_km=("Distance_km", "sum"),
      Payment_THB=("Payment_THB", "sum"), Total_Cost_THB=("Total_Cost_THB", "sum"),
      Revenue_THB=("Revenue_THB", sum1), Profit_THB=("Profit_THB", sum1),
      Fuel_L=("Fuel_L", sum1), CO2_kg=("CO2_kg", sum1), OT_Hrs=("OT_Hrs", "sum"),
  ).reset_index()
  g["Cost_per_km"] = np.where(g["Distance_km"] > 0, g["Total_Cost_THB"] / g["Distance_km"], np.nan)
  g["Cost_per_Drop"] = np.where(g["Drops"] > 0, g["Total_Cost_THB"] / g["Drops"], np.nan)
  g["CO2_per_km"] = np.where(g["Distance_km"] > 0, g["CO2_kg"] / g["Distance_km"], np.nan)
  return g
