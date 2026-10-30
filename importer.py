"""
importer.py — อ่านและจัดเตรียมไฟล์ Excel ของบริษัท (ETL: Extract → Transform)

โครงสร้างไฟล์บริษัท
  - ชีต "Data Master"  : รายชื่อคนขับประจำ + ทะเบียนรถ + ประเภทตู้
  - ชีตรายเดือน (เช่น jun26) : 1 แถว = พนักงาน 1 คน (คนขับหรือเด็กรถ) ทำงาน 1 วัน, 45 คอลัมน์

สิ่งที่ทำตอนนำเข้า
  1) ปรับชื่อคอลัมน์ที่แต่ละเดือนตั้งไม่เหมือนกันให้เป็นชื่อมาตรฐาน
  2) แก้วันที่ที่สลับวัน/เดือน (เช่น ชีต เม.ย. มีวันที่ 2026-09-04 = 9 เม.ย.)
  3) ตรวจคุณภาพข้อมูลทีละแถว แล้ว "ทำเครื่องหมาย" ไว้ (ไม่ลบทิ้ง)
  4) เติมทะเบียนรถจาก Data Master เท่าที่จับคู่ได้
  5) ปกปิดข้อมูลส่วนบุคคล: ตัดชื่อ-นามสกุลและเบอร์โทรออก ใช้รหัสพนักงาน (Username) แทน
"""
import hashlib
import re

import numpy as np
import pandas as pd

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

# ชื่อคอลัมน์มาตรฐาน ← ชื่อที่พบในไฟล์บริษัท (ตัดช่องว่าง/ขึ้นบรรทัดใหม่ และเป็นตัวพิมพ์เล็กแล้ว)
ALIASES = {
    "Work_Date": ["date"],
    "Booking_Raw": ["booking_id clock out", "booking_id"],
    "Rate_Card": ["rate_card"],
    "Store": ["st."],
    "Zone": ["zone"],
    "Username": ["username"],
    "First_Name": ["ชื่อ"],
    "Last_Name": ["นามสกุล"],
    "Position": ["position"],
    "Supervisor": ["sup"],
    "Shift_In": ["shift in"],
    "Shift_Out": ["shift out"],
    "Punch_In": ["punch in"],
    "Punch_Out": ["punch out"],
    "OT_Hrs": ["over time (hrs)"],
    "OT_Request_Hrs": ["over time request (hrs)"],
    "OT_Approved_Hrs": ["over_time_approve_hours"],
    "Trips": ["จำนวนเที่ยวทั้งหมด"],
    "Drops": ["จำนวนจุดส่งทั้งหมด"],
    "Mileage_In": ["mileage in"],
    "Mileage_Out": ["mileage out"],
    "Odometer_km": ["ระยะทางรวม (เลิกงาน - เข้างาน)"],
    "Trips_TMS": ["trip_tms"],
    "Drops_TMS": ["drop_tms"],
    "Orders": ["order"],
    "Planned_km": ["planned_distance"],
    "Actual_km": ["actual_distance"],
    "Baseline_km": ["distance_baseline"],
    "Paid_km": ["paid_distance"],
    "Equivalent_Drop": ["equivalent drop"],
    "Remark": ["หมายเหตุ"],
    "Vehicle_Fee": ["ค่ารถ"],
    "Fuel_Fee": ["ค่าน้ำมัน"],
    "OT_Fee": ["ค่าโอที"],
    "Incentive": ["incentive"],
    "Night_Load": ["night load", "night_load"],
    "Other_Exp_VAT": ["others_expense_vat"],
    "Other_Exp_NonVAT": ["others_expense_non_vat"],
    "Exp_VAT": ["expense_vat"],
    "Exp_NonVAT": ["expense_non_vat"],
    "Penalty": ["penalty_fine"],
    "Early_Shift_Fee": ["ค่าตารางกะเช้าตรู่", "early_cost"],
    "Incentive_Monthly": ["incentive_monthly"],
    "Total_Payment": ["ยอดรวมทั้งหมด"],
    "EBilling_Status": ["e-billing"],
}
NUMERIC = ["OT_Hrs", "OT_Request_Hrs", "OT_Approved_Hrs", "Trips", "Drops", "Mileage_In", "Mileage_Out",
           "Odometer_km", "Trips_TMS", "Drops_TMS", "Orders", "Planned_km", "Actual_km", "Baseline_km",
           "Paid_km", "Equivalent_Drop", "Vehicle_Fee", "Fuel_Fee", "OT_Fee", "Incentive", "Night_Load",
           "Other_Exp_VAT", "Other_Exp_NonVAT", "Exp_VAT", "Exp_NonVAT", "Penalty", "Early_Shift_Fee",
           "Incentive_Monthly"]
# องค์ประกอบของยอดรวมทั้งหมด (ค่าปรับบันทึกเป็นค่าติดลบในไฟล์)
PAYMENT_PARTS = ["Vehicle_Fee", "Fuel_Fee", "OT_Fee", "Incentive", "Night_Load", "Other_Exp_VAT",
                 "Other_Exp_NonVAT", "Exp_VAT", "Exp_NonVAT", "Early_Shift_Fee", "Incentive_Monthly", "Penalty"]
VALID_ZONES = {"BKK", "UPC", "MainUPC"}
MAX_DAILY_KM = 1000  # ระยะทางต่อวันเกินค่านี้ถือว่าผิดปกติ (รถ 4 ล้อในเมือง)

# ประเภทปัญหาคุณภาพข้อมูล: รหัส → (คำอธิบาย, มิติคุณภาพตามบทที่ 2)
FLAGS = {
    "DATE_FIXED": ("วันที่สลับวัน/เดือน (แก้ให้แล้ว)", "ความสอดคล้อง"),
    "DATE_INVALID": ("วันที่ไม่อยู่ในเดือนของชีต", "ความสมเหตุสมผล"),
    "NO_BOOKING": ("ไม่มีเลข Booking", "ความครบถ้วน"),
    "DUP_BOOKING": ("Booking ซ้ำ (บริษัทระบุว่าซ้ำ)", "ความไม่ซ้ำซ้อน"),
    "NO_CLOCKOUT": ("คนขับไม่กด Clock OUT", "ความครบถ้วน"),
    "DUP_PERSON_DAY": ("พนักงานคนเดียวมีหลายแถวในวันเดียวกัน", "ความไม่ซ้ำซ้อน"),
    "TOTAL_TEXT": ("ยอดรวมไม่ใช่ตัวเลข (เช่น \"-\")", "ความสมเหตุสมผล"),
    "TOTAL_MISMATCH": ("ยอดรวมไม่เท่ากับผลรวมค่าใช้จ่ายย่อย", "ความถูกต้อง"),
    "EBILL_NOT_APPROVED": ("E-Billing ยังไม่อนุมัติ/ว่าง", "ความครบถ้วน"),
    "ZONE_INVALID": ("ZONE ผิดรูปแบบ (เช่น 0)", "ความสมเหตุสมผล"),
    "STORE_INVALID": ("สาขาว่างหรือผิดรูปแบบ", "ความสมเหตุสมผล"),
    "DIST_OUTLIER": (f"ระยะทางผิดปกติ (> {MAX_DAILY_KM:,} กม./วัน หรือติดลบ)", "ค่าผิดปกติ"),
    "SHIFT_MISSING": ("ไม่มีเวลาเข้า-ออกกะ", "ความครบถ้วน"),
    "NOT_IN_MASTER": ("คนขับไม่อยู่ใน Data Master (ไม่ทราบทะเบียนรถ)", "ความครบถ้วน"),
}


def _norm(s):
  return re.sub(r"\s+", " ", str(s)).strip().lower()


def sheet_year_month(name):
  """'jun26' → '2026-06' ถ้าไม่ใช่ชีตรายเดือนคืน None"""
  m = re.fullmatch(r"([a-z]{3})(\d{2})", name.strip().lower())
  if not m or m.group(1) not in MONTHS:
    return None
  return f"20{m.group(2)}-{MONTHS[m.group(1)]:02d}"


def fingerprint(df):
  """ลายนิ้วมือของข้อมูล ใช้ตรวจว่าชีตสองชีตเป็นข้อมูลชุดเดียวกันหรือไม่"""
  raw = df.dropna(how="all").to_csv(index=False).encode("utf-8")
  return hashlib.sha1(raw).hexdigest()


def list_month_sheets(sheets):
  """สรุปชีตรายเดือนในไฟล์ พร้อมตรวจชีตที่ซ้ำกันทั้งชีต"""
  rows, seen = [], {}
  for name, df in sheets.items():
    ym = sheet_year_month(name)
    if ym is None:
      continue
    fp = fingerprint(df)
    rows.append(dict(sheet=name, year_month=ym, rows=len(df.dropna(how="all")),
                     fingerprint=fp, duplicate_of=seen.get(fp)))
    seen.setdefault(fp, name)
  return rows


def rename_columns(df):
  """คืน (df ที่เปลี่ยนชื่อคอลัมน์แล้ว, รายการคอลัมน์ที่หาไม่เจอ)"""
  lookup = {a: canon for canon, al in ALIASES.items() for a in al}
  mapping = {c: lookup[_norm(c)] for c in df.columns if _norm(c) in lookup}
  out = df.rename(columns=mapping)
  missing = [c for c in ALIASES if c not in out.columns]
  return out[[c for c in ALIASES if c in out.columns]], missing


def _to_minutes(v):
  """เวลา (time / datetime / 'HH:MM') → นาทีนับจากเที่ยงคืน"""
  if v is None or (isinstance(v, float) and np.isnan(v)):
    return np.nan
  if hasattr(v, "hour"):
    return v.hour * 60 + v.minute
  m = re.match(r"^\s*(\d{1,2}):(\d{2})", str(v))
  return int(m.group(1)) * 60 + int(m.group(2)) if m else np.nan


def _fmt_minutes(m):
  return "" if pd.isna(m) else f"{int(m) // 60:02d}:{int(m) % 60:02d}"


def parse_master(df):
  """ชีต Data Master → ตารางทะเบียนรถ (ใช้ Username และเลข Booking เป็นกุญแจ)"""
  if df is None or df.empty:
    return pd.DataFrame(columns=["Username", "Booking", "Plate", "Box_Type", "Master_Store"])
  m = pd.DataFrame({
      "Username": df.get("Frog Username"),
      "Booking": df.get("Booking"),
      "Plate": df.get("ทะเบียน").fillna("").astype(str).str.replace(r"\s+", "", regex=True),
      "Box_Type": df.get("ชนิด").fillna("").astype(str).str.strip().str.title(),
      "Master_Store": df.get("Store"),
  })
  m = m[m["Plate"] != ""]
  return m.drop_duplicates()


def clean_month(raw, year_month, master=None):
  """แปลงชีตรายเดือนเป็นตารางมาตรฐาน + คอลัมน์ Flags (รหัสปัญหาคั่นด้วย ,)"""
  df, missing = rename_columns(raw.dropna(how="all"))
  if missing:
    raise ValueError("ไม่พบคอลัมน์: " + ", ".join(missing))
  df = df.reset_index(drop=True).copy()
  flags = [[] for _ in range(len(df))]

  def flag(mask, code):
    for i in np.flatnonzero(np.asarray(mask, dtype=bool)):
      flags[i].append(code)

  # ---------- วันที่ ----------
  y, mth = int(year_month[:4]), int(year_month[5:])
  d = pd.to_datetime(df["Work_Date"], errors="coerce")
  swap = d.notna() & (d.dt.month != mth) & (d.dt.day == mth) & (d.dt.month <= 31)
  fixed = pd.to_datetime(dict(year=y, month=mth, day=d.dt.month.where(swap, 1)), errors="coerce")
  d = d.where(~swap, fixed)
  flag(swap, "DATE_FIXED")
  bad_date = d.isna() | (d.dt.month != mth) | (d.dt.year != y)
  flag(bad_date, "DATE_INVALID")
  df["Work_Date"] = d.dt.normalize()
  df["Year_Month"] = year_month

  # ---------- ตัวเลข ----------
  total_num = pd.to_numeric(df["Total_Payment"], errors="coerce")
  flag(total_num.isna(), "TOTAL_TEXT")
  for c in NUMERIC:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
  df["Total_Payment"] = total_num.fillna(0.0)
  parts = df[PAYMENT_PARTS].sum(axis=1)
  flag(total_num.notna() & ((parts - total_num).abs() > 0.05), "TOTAL_MISMATCH")

  # ---------- ข้อความ: แทนค่าว่างด้วย "" ก่อน (pandas 3 เก็บค่าว่างเป็น NaN แม้แปลงเป็น str) ----------
  for c in ["Booking_Raw", "Rate_Card", "Store", "Zone", "Username", "Position", "Supervisor", "Remark",
            "EBilling_Status"]:
    df[c] = df[c].fillna("").astype(str).replace("nan", "")

  # ---------- Booking / สถานะ ----------
  b = df["Booking_Raw"]
  df["Booking"] = b.str.extract(r"(B\d+_\d+)")[0]
  flag(df["Booking"].isna(), "NO_BOOKING")
  flag(b.str.contains("ซ้ำ"), "DUP_BOOKING")
  flag(b.str.contains("Clock OUT", case=False), "NO_CLOCKOUT")
  df["EBilling_Status"] = df["EBilling_Status"].str.strip().str.lower().replace({"-": ""})
  flag(df["EBilling_Status"] != "approved", "EBILL_NOT_APPROVED")

  # ---------- รหัส/ชื่อ ----------
  df["Zone"] = df["Zone"].astype(str).str.replace(" ", "").str.strip()
  df.loc[df["Zone"].str.upper() == "MAINUPC", "Zone"] = "MainUPC"
  flag(~df["Zone"].isin(VALID_ZONES), "ZONE_INVALID")
  df["Store"] = df["Store"].astype(str).str.strip()
  flag(~df["Store"].str.match(r"^ST\.\d+"), "STORE_INVALID")
  df["Position"] = df["Position"].astype(str).str.strip().str.title()
  df["Supervisor"] = df["Supervisor"].astype(str).str.upper()
  df["Username"] = df["Username"].astype(str).str.strip()
  dup = df.duplicated(["Work_Date", "Username"], keep=False)
  flag(dup, "DUP_PERSON_DAY")

  # ---------- ระยะทาง ----------
  out = (df["Actual_km"] > MAX_DAILY_KM) | (df["Actual_km"] < 0) | (df["Odometer_km"] > MAX_DAILY_KM)
  flag(out, "DIST_OUTLIER")
  df["Distance_km"] = df["Actual_km"].where(~out, np.nan)  # ระยะทางที่ใช้คำนวณ (actual_distance)

  # ---------- เวลา ----------
  for c in ["Shift_In", "Shift_Out", "Punch_In", "Punch_Out"]:
    df[c + "_min"] = df[c].map(_to_minutes)
    df[c] = df[c + "_min"].map(_fmt_minutes)
  flag(df["Shift_In_min"].isna() | df["Punch_In_min"].isna(), "SHIFT_MISSING")
  work = df["Punch_Out_min"] - df["Punch_In_min"]
  df["Work_Hrs"] = (work.where(work >= 0, work + 24 * 60)) / 60  # กะข้ามเที่ยงคืน

  # ---------- ทะเบียนรถจาก Data Master ----------
  df["Plate"], df["Box_Type"] = np.nan, np.nan
  if master is not None and not master.empty:
    by_user = master.drop_duplicates("Username").set_index("Username")
    by_book = master.drop_duplicates("Booking").set_index("Booking")
    df["Plate"] = df["Username"].map(by_user["Plate"]).fillna(df["Booking"].map(by_book["Plate"]))
    df["Box_Type"] = df["Username"].map(by_user["Box_Type"]).fillna(df["Booking"].map(by_book["Box_Type"]))
  is_driver = df["Position"].eq("Driver")
  flag(is_driver & df["Plate"].isna(), "NOT_IN_MASTER")
  df["Box_Type"] = df["Box_Type"].where(is_driver, "Helper").fillna("ไม่ทราบ")

  df["Flags"] = [",".join(f) for f in flags]
  # ปกปิดข้อมูลส่วนบุคคล (PDPA): ไม่เก็บชื่อ-นามสกุลลงฐานข้อมูล
  return df.drop(columns=["First_Name", "Last_Name"])


def quality_summary(df):
  """จำนวนแถวที่พบปัญหาแต่ละประเภท"""
  rows = []
  for code, (desc, dim) in FLAGS.items():
    n = int(df["Flags"].str.contains(rf"\b{code}\b", regex=True).sum())
    # ใช้ dict literal เพราะชื่อ kwargs ภาษาไทยถูก Python แปลงรูป (NFKC) เช่น "ำ"
    rows.append({"รหัส": code, "ปัญหา": desc, "มิติคุณภาพ": dim, "จำนวนแถว": n,
                 "ร้อยละ": round(n / len(df) * 100, 2) if len(df) else 0})
  return pd.DataFrame(rows)


def mask_plate(p):
  """แสดงทะเบียนรถแบบปกปิด 2 หลักท้าย เช่น ฒร8878 → ฒร88xx"""
  if not isinstance(p, str) or not p or p == "nan":
    return "ไม่พบใน Master"
  return p[:-2] + "xx" if len(p) > 2 else "xx"
