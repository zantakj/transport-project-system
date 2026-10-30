"""
database.py — ฐานข้อมูล SQLite ของระบบ

ตาราง
  ops          ข้อมูลการปฏิบัติงานรายวันที่ผ่านการจัดเตรียมแล้ว (1 แถว = พนักงาน 1 คน 1 วัน)
  fleet_master ทะเบียนรถจากชีต Data Master
  imports      ประวัติการนำเข้ารายเดือน + จำนวนรถทั้งหมดของบริษัทในเดือนนั้น
  params       พารามิเตอร์ที่ใช้คำนวณ พร้อมแหล่งที่มาและสถานะ
  fuel_prices  ราคาน้ำมันรายเดือน (ผู้ใช้กรอก)
  users        ผู้ใช้งาน (รหัสผ่านเก็บเป็นค่าแฮช bcrypt)
"""
import datetime as dt
import sqlite3

import pandas as pd

DB_PATH = "transport.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  username TEXT PRIMARY KEY, pw_hash TEXT NOT NULL, role TEXT NOT NULL, created_at TEXT);
CREATE TABLE IF NOT EXISTS params(
  key TEXT PRIMARY KEY, grp TEXT, ord INTEGER, label TEXT, value REAL, unit TEXT, status TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS fuel_prices(
  year_month TEXT PRIMARY KEY, price REAL, source TEXT);
CREATE TABLE IF NOT EXISTS imports(
  year_month TEXT PRIMARY KEY, sheet TEXT, file_name TEXT, rows INTEGER, fleet_total INTEGER,
  fingerprint TEXT, imported_at TEXT, imported_by TEXT);
"""

# สถานะของพารามิเตอร์ (ต้องตรงกับตารางพารามิเตอร์ในเล่ม)
REAL, REF, ASSUMED, PENDING = "ข้อมูลจริง", "ค่าอ้างอิง", "ค่าสมมติ", "รอข้อมูลบริษัท"

# key: (กลุ่ม, ลำดับ, ชื่อ, ค่าเริ่มต้น, หน่วย, สถานะ, แหล่งที่มา)
DEFAULT_PARAMS = {
    "fleet_total": ("กองรถ", 1, "จำนวนรถทั้งหมดของบริษัท (ค่าเริ่มต้นตอนนำเข้า)", 173, "คัน", ASSUMED,
                    "สมมติไว้ก่อน รอบริษัทยืนยัน (ข้อมูล เม.ย./มิ.ย. มีรถวิ่งพร้อมกันสูงสุด 167–169 คัน/วัน)"),
    "vehicle_price": ("ค่าเสื่อมราคา", 1, "ราคาทุนรถ 4 ล้อ (รวมตู้) เฉลี่ยต่อคัน", None, "บาท/คัน", PENDING,
                      "รอข้อมูลจากฝ่ายบัญชีของบริษัท"),
    "useful_life": ("ค่าเสื่อมราคา", 2, "อายุการใช้งานรถ", 5, "ปี", REF,
                    "พ.ร.ฎ. ฉบับที่ 145 (พ.ศ. 2527) มาตรา 4(5): หักค่าเสื่อมได้ไม่เกินร้อยละ 20 ของต้นทุน/ปี (= 5 ปี) "
                    "https://rd.go.th/2369.html — ถ้าบริษัทใช้อายุอื่นให้ใช้ของบริษัท"),
    "salvage_value": ("ค่าเสื่อมราคา", 3, "มูลค่าซากต่อคัน", 0, "บาท/คัน", ASSUMED,
                      "ใช้ 0 ไว้ก่อน รอข้อมูลจากฝ่ายบัญชีของบริษัท"),
    "insurance_year": ("ต้นทุนคงที่อื่น", 1, "ค่าประกันภัย + ภาษีรถ + พ.ร.บ. ต่อคันต่อปี", None, "บาท/คัน/ปี",
                       PENDING, "รอข้อมูลจากบริษัท"),
    "maintenance_km": ("ต้นทุนผันแปรอื่น", 1, "ค่าซ่อมบำรุง + ยาง + น้ำมันเครื่อง ต่อกิโลเมตร", None, "บาท/กม.",
                       PENDING, "รอข้อมูลจากบริษัท"),
    "trip_price": ("รายได้", 1, "ค่าเที่ยวที่ลูกค้าจ่าย ต่อเที่ยว", None, "บาท/เที่ยว", ASSUMED,
                   "ค่าสมมติที่ทีมผู้จัดทำกำหนด (บริษัทไม่ได้ให้ข้อมูลราคาที่ลูกค้าจ่าย)"),
    "ef_diesel": ("คาร์บอน", 1, "ค่าการปล่อยก๊าซเรือนกระจกของน้ำมันดีเซล (Mobile combustion)", 2.7406,
                  "kgCO2e/ลิตร", REF,
                  "ตารางค่า Emission Factor สำหรับ CFO ของ อบก. (ปรับปรุง เม.ย. 2565) แถว Gas/Diesel Oil – Mobile "
                  "combustion อ้างอิง IPCC 2006 Vol.2 Table 3.2.1–3.2.2 — ควรตรวจกับเอกสาร อบก. ฉบับล่าสุด"),
    "tver_price": ("คาร์บอน", 2, "ราคาคาร์บอนเครดิต T-VER", None, "บาท/tCO2e", PENDING,
                   "ต้องใช้ราคาเฉลี่ยจากสถิติการซื้อขายของ อบก. (carbonmarket.tgo.or.th)"),
}

DEFAULT_FUEL = {
    "2026-06": (40.80, "ราคาขายปลีกดีเซล B7 ของ ปตท. ในกรุงเทพฯ ณ 11 มิ.ย. 2569 (PPTV, 11 มิ.ย. 2569) "
                       "— ควรเปลี่ยนเป็นราคาเฉลี่ยรายเดือนจาก สนพ."),
}


def get_connection():
  return sqlite3.connect(DB_PATH)


def init_db():
  with get_connection() as c:
    c.executescript(SCHEMA)
    for k, (grp, o, label, val, unit, status, src) in DEFAULT_PARAMS.items():
      c.execute("INSERT OR IGNORE INTO params VALUES (?,?,?,?,?,?,?,?)", (k, grp, o, label, val, unit, status, src))
    for ym, (price, src) in DEFAULT_FUEL.items():
      c.execute("INSERT OR IGNORE INTO fuel_prices VALUES (?,?,?)", (ym, price, src))


def _table_exists(c, name):
  return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


# ---------------- ข้อมูลการปฏิบัติงาน ----------------
def save_month(df, year_month, sheet, file_name, fleet_total, fp, user):
  """บันทึกข้อมูล 1 เดือน (ถ้าเคยนำเข้าเดือนนี้แล้วจะแทนที่ของเดิม)"""
  with get_connection() as c:
    if _table_exists(c, "ops"):
      c.execute("DELETE FROM ops WHERE Year_Month=?", (year_month,))
    out = df.copy()
    out["Work_Date"] = out["Work_Date"].dt.strftime("%Y-%m-%d")
    out.to_sql("ops", c, if_exists="append", index=False)
    c.execute("INSERT OR REPLACE INTO imports VALUES (?,?,?,?,?,?,?,?)",
              (year_month, sheet, file_name, len(df), int(fleet_total), fp,
               dt.datetime.now().strftime("%Y-%m-%d %H:%M"), user))


def save_master(master):
  with get_connection() as c:
    master.to_sql("fleet_master", c, if_exists="replace", index=False)


def delete_month(year_month):
  with get_connection() as c:
    if _table_exists(c, "ops"):
      c.execute("DELETE FROM ops WHERE Year_Month=?", (year_month,))
    c.execute("DELETE FROM imports WHERE year_month=?", (year_month,))


def load_ops():
  with get_connection() as c:
    if not _table_exists(c, "ops"):
      return pd.DataFrame()
    df = pd.read_sql("SELECT * FROM ops", c)
  df["Work_Date"] = pd.to_datetime(df["Work_Date"], errors="coerce")
  return df


def load_imports():
  with get_connection() as c:
    return pd.read_sql("SELECT * FROM imports ORDER BY year_month", c)


# ---------------- พารามิเตอร์ ----------------
def load_params():
  with get_connection() as c:
    return pd.read_sql("SELECT * FROM params ORDER BY grp, ord", c)


def param_values():
  p = load_params()
  return {k: (None if pd.isna(v) else float(v)) for k, v in zip(p["key"], p["value"])}


def update_param(key, value, status, source):
  with get_connection() as c:
    c.execute("UPDATE params SET value=?, status=?, source=? WHERE key=?", (value, status, source, key))


def load_fuel_prices():
  with get_connection() as c:
    return pd.read_sql("SELECT * FROM fuel_prices ORDER BY year_month", c)


def upsert_fuel_price(year_month, price, source):
  with get_connection() as c:
    c.execute("INSERT OR REPLACE INTO fuel_prices VALUES (?,?,?)", (year_month, price, source))


def update_fleet_total(year_month, n):
  with get_connection() as c:
    c.execute("UPDATE imports SET fleet_total=? WHERE year_month=?", (int(n), year_month))


def data_version():
  """ค่าที่เปลี่ยนทุกครั้งที่ฐานข้อมูลถูกแก้ไข (ใช้ล้าง cache การคำนวณ)"""
  import os
  return os.stat(DB_PATH).st_mtime_ns if os.path.exists(DB_PATH) else 0
