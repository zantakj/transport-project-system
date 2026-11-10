"""
calculations.py — สูตรคำนวณตัวชี้วัดตามบทที่ 2 และตารางที่ 3.4 ของรายงาน

ต่อเที่ยว (หัวข้อ 2.4.6)
  รายได้ต่อเที่ยว      = ยอด E-Billing ของพนักงานขับรถในวันนั้น ÷ จำนวนเที่ยวของวันนั้น   (มาจากไฟล์ Revenue_THB)
  ค่าจ้างต่อเที่ยว      = ค่าจ้างรายวัน 500 ÷ จำนวนเที่ยวของพนักงานขับรถคนนั้นในวันนั้น
  ค่า OT ต่อเที่ยว     = ชั่วโมง OT ที่อนุมัติต่อเที่ยว × 80
  ลิตรน้ำมัน          = ระยะทาง ÷ 11 กม./ลิตร                                        (หัวข้อ 2.11.1)
  ค่าน้ำมัน           = ลิตร × ราคาน้ำมันดีเซลเฉลี่ยของเดือนนั้น
  ค่าซ่อมบำรุงต่อเที่ยว  = ค่าซ่อมบำรุงของกองรถต่อวัน ÷ จำนวนเที่ยวทั้งหมดในวันนั้น        (หัวข้อ 2.4.5)
      ค่าซ่อมบำรุงของกองรถต่อวัน = จำนวนรถทั้งหมด × (ค่าเสื่อม/คัน/วัน + ค่าประกัน/คัน/ปี ÷ 365)
  กำไรสุทธิต่อเที่ยว    = รายได้ − ค่าจ้าง − ค่า OT − ค่าน้ำมัน − ค่าซ่อมบำรุง
  CO₂e (กก.)        = ลิตร × EF 2.7406                                             (หัวข้อ 2.11.2)
  ศักยภาพลดการปล่อย  = ผลรวม (ระยะทางจริง − ระยะทางตามแผน ที่เกินแผน) ÷ 11 × EF          (หัวข้อ 2.11.3)

รายเดือน
  กำไรสุทธิ = รายได้รวม − ค่าจ้างรวม − ค่า OT รวม − ค่าน้ำมันรวม − ค่าซ่อมบำรุงของกองรถทั้งเดือน
  รายได้ ค่าจ้าง และ OT รวมรายการที่ไม่ผูกกับเที่ยววิ่ง (other_billing) ด้วย ไม่รวม Helper
  ค่าซ่อมบำรุงทั้งเดือน = ค่าซ่อมบำรุงของกองรถต่อวัน × จำนวนวันในเดือน (รถเสื่อมราคาทุกวันไม่ว่าจะวิ่งหรือไม่)
"""
import calendar

import numpy as np
import pandas as pd

COST_CATS = {"Labor_THB": "ค่าจ้างและค่าทำงานล่วงเวลา", "Fuel_Cost_THB": "ค่าน้ำมันเชื้อเพลิง",
             "Maint_THB": "ค่าซ่อมบำรุง (ค่าเสื่อม + ประกัน)"}


def fleet_day_cost(p):
  """ค่าซ่อมบำรุงของกองรถต่อวัน (บาท)"""
  return p["fleet_total"] * (p["dep_day"] + p["ins_year"] / 365)


def days_in_month(ym):
  y, m = map(int, ym.split("-"))
  return calendar.monthrange(y, m)[1]


def build(trips, p, fuel):
  """เพิ่มคอลัมน์ที่คำนวณได้ให้ข้อมูลรายเที่ยว"""
  t = trips.copy()
  # จำนวนเที่ยวของพนักงานขับรถคนนั้นในวันนั้น (N) — ใช้ค่าจากไฟล์ซึ่งนับตามแถวต้นฉบับ ถ้าไม่มีให้นับเอง
  n = t.groupby(["Trip_Date", "Driver_Code"])["Trip_ID"].transform("size")
  t["Trips_That_Day"] = t["Trips_That_Day"].fillna(n) if "Trips_That_Day" in t else n
  t["Wage_THB"] = p["wage_day"] / t["Trips_That_Day"]
  t["OT_Cost_THB"] = t["OT_Approved_Hours"].fillna(0) * p["ot_rate"]
  t["Labor_THB"] = t["Wage_THB"] + t["OT_Cost_THB"]
  t["Fuel_L"] = t["Distance_km"] / p["km_per_l"]
  t["Fuel_Price"] = t["Year_Month"].map(fuel)
  t["Fuel_Cost_THB"] = t["Fuel_L"].fillna(0) * t["Fuel_Price"]
  t["Day_Trips"] = t.groupby("Trip_Date")["Trip_ID"].transform("size")
  t["Maint_THB"] = fleet_day_cost(p) / t["Day_Trips"]
  t["Cost_THB"] = t["Labor_THB"] + t["Fuel_Cost_THB"] + t["Maint_THB"]
  t["Profit_THB"] = t["Revenue_THB"].fillna(0) - t["Cost_THB"]
  t["CO2_kg"] = t["Fuel_L"] * p["ef_diesel"]
  plan_ok = t["Planned_Distance_km"] > 0
  t["Excess_km"] = np.where(plan_ok, (t["Distance_km"] - t["Planned_Distance_km"]).clip(lower=0), np.nan)
  t["Reduction_kg"] = t["Excess_km"] / p["km_per_l"] * p["ef_diesel"]
  return t


def other_costs(other, p):
  o = other.copy()
  o["Wage_THB"] = np.where(o["Driver_Wage_THB"] > 0, p["wage_day"], 0.0)
  o["OT_Cost_THB"] = o["OT_Approved_Hours"] * p["ot_rate"]
  return o


def summarize(t, o, p, months, whole_fleet=True):
  """ตัวชี้วัดรวมของชุดข้อมูลที่กรองแล้ว
  whole_fleet=True  → ค่าซ่อมบำรุง = กองรถทั้งเดือน (ตามสูตรกำไรสุทธิรายเดือน)
  whole_fleet=False → กรองสาขา/โซนอยู่ ใช้ค่าซ่อมบำรุงที่ปันส่วนให้เที่ยววิ่งของสาขา/โซนนั้น"""
  k = {}
  k["trips"] = len(t)
  k["km"] = t["Distance_km"].sum()
  k["km_avg"] = k["km"] / k["trips"] if k["trips"] else np.nan
  k["drops"] = t["Drops"].sum()
  k["days"] = t["Trip_Date"].nunique()
  active = t.groupby("Trip_Date")["Driver_Code"].nunique()
  k["active_avg"] = active.mean() if len(active) else np.nan
  k["active_max"] = active.max() if len(active) else np.nan
  k["fleet"] = p["fleet_total"]
  k["util"] = k["active_avg"] / k["fleet"] * 100
  k["ot_hrs"] = t["OT_Approved_Hours"].sum() + o["OT_Approved_Hours"].sum()
  k["revenue"] = t["Revenue_THB"].sum() + o["Revenue_THB"].sum()
  k["wage"] = t["Wage_THB"].sum() + o["Wage_THB"].sum()
  k["ot_cost"] = t["OT_Cost_THB"].sum() + o["OT_Cost_THB"].sum()
  k["fuel_l"] = t["Fuel_L"].sum()
  k["fuel_cost"] = t["Fuel_Cost_THB"].sum(min_count=1)
  k["fuel_missing"] = sorted(t.loc[t["Fuel_Price"].isna(), "Year_Month"].unique())
  if whole_fleet:
    k["maint_days"] = sum(days_in_month(m) for m in months)
    k["maint"] = fleet_day_cost(p) * k["maint_days"]
  else:
    k["maint_days"] = None
    k["maint"] = t["Maint_THB"].sum()
  k["labor"] = k["wage"] + k["ot_cost"]
  k["cost"] = k["labor"] + (k["fuel_cost"] if pd.notna(k["fuel_cost"]) else 0) + k["maint"]
  k["profit"] = k["revenue"] - k["cost"]
  k["margin"] = k["profit"] / k["revenue"] * 100 if k["revenue"] else np.nan
  k["rev_trip"] = k["revenue"] / k["trips"] if k["trips"] else np.nan
  k["cost_trip"] = k["cost"] / k["trips"] if k["trips"] else np.nan
  k["cost_km"] = k["cost"] / k["km"] if k["km"] else np.nan
  k["co2"] = t["CO2_kg"].sum()
  k["co2_trip"] = k["co2"] / k["trips"] if k["trips"] else np.nan
  k["co2_km"] = k["co2"] / k["km"] if k["km"] else np.nan
  k["co2_drop"] = k["co2"] / k["drops"] if k["drops"] else np.nan
  k["excess_km"] = t["Excess_km"].sum()
  k["reduction"] = t["Reduction_kg"].sum()
  k["no_plan"] = int(t["Excess_km"].isna().sum())
  return k


def monthly(t, o, p, whole_fleet=True):
  """ตัวชี้วัดรายเดือน + อัตราการเปลี่ยนแปลงเทียบเดือนก่อน (หัวข้อ 2.3)"""
  rows = []
  for ym in sorted(t["Year_Month"].unique()):
    k = summarize(t[t["Year_Month"] == ym], o[o["Year_Month"] == ym], p, [ym], whole_fleet)
    k["Year_Month"] = ym
    rows.append(k)
  m = pd.DataFrame(rows)
  return m.drop(columns=["fuel_missing"]) if len(m) else m


def pct_change(cur, prev):
  if prev is None or pd.isna(prev) or prev == 0 or pd.isna(cur):
    return None
  return (cur - prev) / abs(prev) * 100


def daily(t, p):
  d = t.groupby("Trip_Date").agg(Trips=("Trip_ID", "size"), Active=("Driver_Code", "nunique"),
                                 km=("Distance_km", "sum")).reset_index()
  d["Utilization"] = d["Active"] / p["fleet_total"] * 100
  d["km_per_vehicle"] = d["km"] / d["Active"]
  return d


def group_summary(t, o, p, by):
  """เปรียบเทียบตามสาขาหรือโซน (ค่าซ่อมบำรุงใช้ส่วนที่ปันส่วนให้เที่ยววิ่ง)"""
  g = t.groupby(by).agg(Trips=("Trip_ID", "size"), km=("Distance_km", "sum"), Drops=("Drops", "sum"),
                        Revenue=("Revenue_THB", "sum"), Labor=("Labor_THB", "sum"), Fuel=("Fuel_Cost_THB", "sum"),
                        Maint=("Maint_THB", "sum"), CO2=("CO2_kg", "sum"), Excess=("Excess_km", "sum"))
  if by in o.columns and len(o):
    og = o.groupby(by).agg(oRev=("Revenue_THB", "sum"), oWage=("Wage_THB", "sum"), oOT=("OT_Cost_THB", "sum"))
    g = g.join(og, how="left").fillna({"oRev": 0, "oWage": 0, "oOT": 0})
    g["Revenue"] += g["oRev"]
    g["Labor"] += g["oWage"] + g["oOT"]
    g = g.drop(columns=["oRev", "oWage", "oOT"])
  g["Cost"] = g["Labor"] + g["Fuel"] + g["Maint"]
  g["Profit"] = g["Revenue"] - g["Cost"]
  g["Margin"] = g["Profit"] / g["Revenue"] * 100
  g["km_trip"] = g["km"] / g["Trips"]
  g["Cost_km"] = g["Cost"] / g["km"]
  g["CO2_km"] = g["CO2"] / g["km"]
  return g.reset_index()
