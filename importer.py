"""
importer.py — อ่านไฟล์ Excel รายเที่ยว (ตารางที่ 3.3) และตรวจคุณภาพข้อมูลตามตารางที่ 3.2

ไฟล์นำเข้า (ผลจากการแปลงข้อมูลรายวันของบริษัทเป็นรายเที่ยว ตามหัวข้อ 3.4.4)
  ชีต Trips            1 แถว = 1 เที่ยววิ่ง  (จำเป็น)
  ชีต Billing_No_Trip  ยอดบิลที่ไม่มีเที่ยววิ่ง (ชื่อเดิม Other_Billing)  (ถ้ามี — ตัดแถว Helper ออก)
  ชีต Data_Quality_Log บันทึกการจัดการข้อมูลตอนแปลง  (ถ้ามี — แสดงในหน้าตรวจคุณภาพข้อมูล)
"""
import re

import numpy as np
import pandas as pd

REQUIRED = ["Trip_ID", "Trip_Date", "Driver_Code", "Branch_Code", "Zone", "Distance_km", "Planned_Distance_km",
            "Drops", "Revenue_THB", "Driver_Wage_THB", "OT_Approved_Hours", "EBilling_Status"]
OPTIONAL = ["Trips_That_Day", "Fuel_Liters", "Distance_Source", "Source_Sheet", "Source_Row"]
OTHER_COLS = ["Date", "Person_Code", "Position", "Branch_Code", "Zone", "Reason", "Revenue_THB",
              "Driver_Wage_THB", "OT_Approved_Hours", "EBilling_Status", "Source_Sheet", "Source_Row"]
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov",
                                      "dec"], 1)}

MAX_DROPS = 100  # จุดส่งต่อเที่ยวสูงสุดที่สมเหตุสมผลสำหรับรถ 4 ล้อ (ข้อมูลจริง 99.9% ไม่เกิน 37 จุด)

# รหัสปัญหา: (คำอธิบาย, มิติคุณภาพตามตารางที่ 3.2, ผลต่อการคำนวณ)
FLAGS = {
    "MISSING_KEY": ("ไม่มีวันที่ รหัสพนักงานขับรถ หรือรหัสสาขา", "ความครบถ้วน", "ไม่นำเข้า"),
    "NO_DISTANCE": ("ไม่มีระยะทาง", "ความครบถ้วน", "ไม่ใช้คำนวณน้ำมันและคาร์บอน"),
    "DIST_REPLACED": ("ระยะทางจริงว่างหรือผิดปกติ ใช้ระยะจากเลขไมล์แทน", "ความครบถ้วน", "ใช้ค่าทดแทน"),
    "NO_PLAN": ("ไม่มีระยะทางตามแผน", "ความครบถ้วน", "ไม่ใช้คำนวณศักยภาพลดการปล่อย"),
    "DUP_TRIP": ("รหัสเที่ยววิ่ง (Trip_ID) ซ้ำ", "ความไม่ซ้ำซ้อน", "ตัดรายการซ้ำออก"),
    "ZONE_INVALID": ("รหัสโซนไม่ถูกต้อง เช่น 0", "ความสมเหตุสมผล", "แสดงเป็นโซน 'ไม่ระบุ'"),
    "NEG_VALUE": ("ระยะทางหรือจุดส่งติดลบ", "ความสมเหตุสมผล", "ทำเครื่องหมายไว้"),
    "DROPS_INVALID": (f"จุดส่งต่อเที่ยวเกิน {MAX_DROPS} จุด (น่าจะบันทึกผิด)", "ความสมเหตุสมผล",
                      "ไม่ใช้คำนวณตัวชี้วัดด้านจุดส่ง"),
    "ZONE_SPELLING": ("ชื่อโซนสะกดไม่ตรงกัน เช่น Main UPC / MainUPC", "ความสอดคล้อง", "ปรับเป็นชื่อเดียวกัน"),
    "ZERO_BILLING": ("มีเที่ยววิ่งแต่ยอด E-Billing เป็น 0", "ความถูกต้อง", "นับรายได้ = 0"),
    "EBILL_PENDING": ("E-Billing ยังไม่อนุมัติ", "ความเป็นปัจจุบัน", "นับเป็นรายได้ตามที่บริษัทยืนยัน"),
    "DIST_OUTLIER": ("ระยะทางต่อเที่ยวสูงผิดปกติ (เกิน Q3 + 1.5×IQR)", "ค่าผิดปกติ", "ทำเครื่องหมายไว้ ไม่ตัดออก"),
}


def sheet_year_month(name):
  """'Jun26' -> '2026-06'"""
  m = re.fullmatch(r"([A-Za-z]{3})[a-z]*\s*(\d{2})", str(name).strip())
  if not m or m.group(1).lower() not in MONTHS:
    return None
  return f"20{m.group(2)}-{MONTHS[m.group(1).lower()]:02d}"


def _text(s):
  """แปลงเป็นข้อความ (object) โดยค่าว่างเป็น None — เลี่ยงปัญหา NA ของ pandas"""
  return s.map(lambda x: None if pd.isna(x) or str(x).strip() == "" else str(x).strip()).astype(object)


def _norm_zone(z):
  return re.sub(r"\s+", "", str(z)).upper()


# ชื่อคอลัมน์อื่นที่ระบบรู้จัก (ภาษาไทย / สะกดต่าง) — เทียบแบบไม่สนตัวพิมพ์ เว้นวรรค _ - ( ) .
ALIASES = {
    "Trip_ID": ["TripID", "Trip No", "รหัสเที่ยว", "รหัสเที่ยววิ่ง", "เลขที่เที่ยว"],
    "Trip_Date": ["Date", "Work Date", "TripDate", "วันที่", "วันที่วิ่ง", "วันที่ทำงาน"],
    "Driver_Code": ["Driver", "DriverID", "Driver ID", "Employee Code", "รหัสคนขับ", "รหัสพนักงานขับรถ",
                    "รหัสพนักงาน"],
    "Branch_Code": ["Branch", "Store", "Store Code", "Route_Code", "Route", "St.", "รหัสสาขา", "สาขา"],
    "Zone": ["Area", "Delivery Area", "โซน", "พื้นที่"],
    "Distance_km": ["Distance", "Actual Distance", "Actual_km", "km", "ระยะทาง", "ระยะทางจริง", "ระยะทาง (กม.)"],
    "Planned_Distance_km": ["Planned Distance", "Planned_km", "Plan km", "Plan Distance", "ระยะทางตามแผน",
                            "ระยะตามแผน", "ระยะทางแผน"],
    "Drops": ["Drop", "Drop Points", "Stops", "จุดส่ง", "จำนวนจุดส่ง", "จุดส่งต่อเที่ยว"],
    "Revenue_THB": ["Revenue", "EBilling", "E-Billing", "Income", "รายได้", "รายได้ต่อเที่ยว",
                    "ยอด E-Billing"],
    "Driver_Wage_THB": ["Wage", "Driver Wage", "ค่าจ้าง", "ค่าจ้างคนขับ", "ค่าจ้างต่อเที่ยว"],
    "OT_Approved_Hours": ["OT", "OT Hours", "OT_Hrs", "OT Approved", "OT_Approved_Hrs", "ชั่วโมง OT",
                          "OT อนุมัติ", "ชั่วโมงทำงานล่วงเวลา"],
    "EBilling_Status": ["Status", "Billing Status", "E-Billing Status", "สถานะ E-Billing", "สถานะวางบิล"],
    "Trips_That_Day": ["Trips per Day", "จำนวนเที่ยวของคนขับวันนั้น", "เที่ยวของคนขับวันนั้น"],
    "Fuel_Liters": ["Fuel L", "Liters", "ลิตรน้ำมัน", "น้ำมัน (ลิตร)"],
    "Source_Sheet": ["ชีตต้นฉบับ"], "Source_Row": ["แถวต้นฉบับ"], "Distance_Source": ["ที่มาระยะทาง"],
}
DAILY_HINTS = ["จำนวนเที่ยวทั้งหมด", "จำนวนจุดส่งทั้งหมด", "Booking", "E-Billing Status"]


def _key(name):
  return re.sub(r"[\s_\-().]+", "", str(name)).lower()


_LOOKUP = {}
for _c, _names in ALIASES.items():
  for _n in [_c] + _names:
    _LOOKUP.setdefault(_key(_n), _c)
for _c in REQUIRED + OPTIONAL:
  _LOOKUP.setdefault(_key(_c), _c)


def auto_map(columns):
  """จับคู่ชื่อคอลัมน์ในไฟล์กับชื่อมาตรฐานตามตารางที่ 3.3 → {ชื่อในไฟล์: ชื่อมาตรฐาน}"""
  exact = {_key(c): c for c in ALIASES.keys() | set(REQUIRED + OPTIONAL)}
  out = {col: exact[_key(col)] for col in columns if _key(col) in exact}  # ชื่อมาตรฐานตรงตัวมาก่อน
  used = set(out.values())
  for col in columns:
    canon = _LOOKUP.get(_key(col))
    if col not in out and canon and canon not in used:
      out[col] = canon
      used.add(canon)
  return out


def pick_trip_sheet(sheets):
  """ใช้ชีตชื่อ Trips ถ้ามี ไม่อย่างนั้นใช้ชีตที่จับคู่คอลัมน์จำเป็นได้มากที่สุด"""
  name = next((s for s in sheets if s.strip().lower() == "trips"), None)
  if name:
    return name
  score = {s: sum(v in REQUIRED for v in auto_map(df.columns).values()) for s, df in sheets.items()}
  return max(score, key=score.get) if score else None


def looks_daily(df):
  """เป็นไฟล์รายวันของบริษัท (ยังไม่ได้แปลงเป็นรายเที่ยว) หรือไม่"""
  cols = " ".join(map(str, df.columns))
  return sum(h in cols for h in DAILY_HINTS) >= 2


def read_trips(sheets, manual=None, sheet=None):
  """คืน (trips, other, qlog, missing_columns) จาก dict ของชีต
  manual: {ชื่อมาตรฐาน: ชื่อคอลัมน์ในไฟล์} สำหรับคอลัมน์ที่ผู้ใช้จับคู่เอง"""
  name = sheet or pick_trip_sheet(sheets)
  if name is None:
    return None, None, None, ["ชีตข้อมูลรายเที่ยว"]
  raw = sheets[name]
  rename = auto_map(raw.columns)
  for canon, col in (manual or {}).items():
    if col:
      rename = {k: v for k, v in rename.items() if v != canon and k != col}
      rename[col] = canon
  raw = raw.rename(columns=rename)
  raw = raw.loc[:, ~raw.columns.duplicated()]
  missing = [c for c in REQUIRED if c not in raw.columns]
  if missing:
    return None, None, None, missing
  keep = REQUIRED + [c for c in OPTIONAL if c in raw.columns]
  t = raw[keep].copy()
  t["Trip_Date"] = pd.to_datetime(t["Trip_Date"], errors="coerce")
  for c in ["Distance_km", "Planned_Distance_km", "Drops", "Revenue_THB", "Driver_Wage_THB", "OT_Approved_Hours",
            "Trips_That_Day"]:
    if c in t:
      t[c] = pd.to_numeric(t[c], errors="coerce")
  for c in ["Trip_ID", "Driver_Code", "Branch_Code", "Zone", "EBilling_Status", "Distance_Source", "Source_Sheet",
            "Source_Row"]:
    if c in t:
      t[c] = _text(t[c])

  flags = pd.DataFrame(False, index=t.index, columns=list(FLAGS))
  flags["MISSING_KEY"] = t["Trip_Date"].isna() | t["Driver_Code"].isna() | t["Branch_Code"].isna()
  flags["NO_DISTANCE"] = t["Distance_km"].isna()
  if "Distance_Source" in t:
    flags["DIST_REPLACED"] = t["Distance_Source"].fillna("").str.contains("mileage")
  flags["NO_PLAN"] = t["Planned_Distance_km"].isna() | (t["Planned_Distance_km"] <= 0)
  flags["DUP_TRIP"] = t["Trip_ID"].duplicated(keep="first")
  zone = t["Zone"].fillna("")
  bad_zone = ~zone.str.fullmatch(r"[A-Za-z ]+")
  flags["ZONE_INVALID"] = bad_zone
  norm = zone.map(_norm_zone)
  canon = zone[~bad_zone].groupby(norm[~bad_zone]).agg(lambda s: s.value_counts().index[0])
  std = norm.map(canon)
  flags["ZONE_SPELLING"] = ~bad_zone & std.notna() & (std != zone)
  flags["NEG_VALUE"] = (t["Distance_km"] < 0) | (t["Drops"] < 0)
  flags["DROPS_INVALID"] = t["Drops"] > MAX_DROPS
  flags["ZERO_BILLING"] = t["Revenue_THB"].fillna(0) == 0
  flags["EBILL_PENDING"] = t["EBilling_Status"].fillna("").str.lower() != "approved"
  q1, q3 = t["Distance_km"].quantile([.25, .75])
  flags["DIST_OUTLIER"] = t["Distance_km"] > q3 + 1.5 * (q3 - q1)

  t["Drops_Raw"] = t["Drops"]
  t.loc[flags["DROPS_INVALID"], "Drops"] = np.nan  # ไม่นำไปรวมจำนวนจุดส่ง (หัวข้อ 3.4.3 ข้อ 1)
  t["Zone"] = np.where(bad_zone, "ไม่ระบุ", std.fillna(zone))
  t["Flags"] = flags.apply(lambda r: " ".join(c for c in FLAGS if r[c]), axis=1)
  t = t[~flags["MISSING_KEY"] & ~flags["DUP_TRIP"]].copy()
  t["Year_Month"] = t["Trip_Date"].dt.strftime("%Y-%m")
  t.attrs["sheet"] = name
  t.attrs["renamed"] = {k: v for k, v in rename.items() if k != v}
  t.attrs["dropped"] = {"MISSING_KEY": int(flags["MISSING_KEY"].sum()), "DUP_TRIP": int(flags["DUP_TRIP"].sum())}

  other = pd.DataFrame(columns=OTHER_COLS + ["Year_Month"])
  oname = next((s for s in sheets if s.strip().lower() in ("billing_no_trip", "other_billing")), None)
  if oname is not None:
    o = sheets[oname]
    o = o[[c for c in OTHER_COLS + ["Month"] if c in o.columns]].copy()
    if "Position" in o:
      o = o[o["Position"].fillna("").astype(str) != "Helper"]  # ไม่รวม Helper ตามที่บริษัทกำหนด
    o["Year_Month"] = _text(o["Month"]) if "Month" in o else pd.to_datetime(o["Date"]).dt.strftime("%Y-%m")
    o = o.drop(columns=[c for c in ["Month"] if c in o])
    for c in ["Revenue_THB", "Driver_Wage_THB", "OT_Approved_Hours"]:
      o[c] = pd.to_numeric(o.get(c), errors="coerce").fillna(0)
    for c in ["Person_Code", "Position", "Branch_Code", "Zone", "Reason", "EBilling_Status", "Source_Sheet",
              "Source_Row"]:
      if c in o:
        o[c] = _text(o[c])
    if "Date" in o:
      o["Date"] = pd.to_datetime(o["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    other = o

  qlog = pd.DataFrame()
  lname = next((s for s in sheets if s.strip().lower() == "data_quality_log"), None)
  if lname is not None:
    q = sheets[lname].apply(_text)
    if {"Month", "Issue", "Action"} <= set(q.columns):
      q["Year_Month"] = q["Month"].map(sheet_year_month)
      qlog = q.dropna(subset=["Year_Month"])
  return t, other, qlog, []


def quality_summary(t):
  """สรุปจำนวนเที่ยวที่พบปัญหาแต่ละประเภท"""
  rows = []
  for code, (label, dim, action) in FLAGS.items():
    if code in ("MISSING_KEY", "DUP_TRIP"):
      n = t.attrs.get("dropped", {}).get(code, 0)
    else:
      n = int(t["Flags"].str.contains(rf"\b{code}\b").sum())
    rows.append({"มิติคุณภาพ": dim, "ปัญหา": label, "จำนวนเที่ยว": n, "การจัดการ": action, "รหัส": code})
  return pd.DataFrame(rows)
