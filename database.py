"""
database.py — ฐานข้อมูล SQLite ของระบบ (ไฟล์ transport_trips.db) ตามหัวข้อ 3.6.3 ของรายงาน

ตารางหลัก 6 ตาราง
  users        ผู้ใช้งาน รหัสผ่านที่แฮชด้วย bcrypt และสิทธิ์ (admin / viewer)
  trips        ข้อมูลรายเที่ยวตามตารางที่ 3.3 (1 แถว = 1 เที่ยววิ่ง)
  imports      ประวัติการนำเข้าไฟล์และเดือนของข้อมูล
  params       พารามิเตอร์ตามตารางที่ 3.5 (ค่าจ้าง OT อัตราสิ้นเปลือง EF)
  fuel_prices  ราคาน้ำมันดีเซลรายเดือนที่ผู้ใช้กรอก
  fleet_master จำนวนรถทั้งหมดและอัตราค่าซ่อมบำรุงของกองรถ (ค่าเสื่อม + ประกัน)

ตารางเสริม
  other_billing รายการเรียกเก็บเงินที่ไม่ผูกกับเที่ยววิ่ง (ไม่รวม Helper) ต้องรวมกับ trips จึงได้รายได้ครบ
  quality_log   บันทึกการจัดการข้อมูลจากขั้นตอนแปลงข้อมูล (ชีต Data_Quality_Log)
"""
import datetime as dt
import os
import sqlite3

import pandas as pd

# ใช้ไฟล์ใหม่ เพื่อไม่ปนกับฐานข้อมูลของเว็บเวอร์ชันก่อน (transport.db / transport_real.db)
DB_PATH = "transport_trips.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  username TEXT PRIMARY KEY, pw_hash TEXT NOT NULL, role TEXT NOT NULL, created_at TEXT);
CREATE TABLE IF NOT EXISTS params(
  key TEXT PRIMARY KEY, ord INTEGER, label TEXT, value REAL, unit TEXT, status TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS fleet_master(
  key TEXT PRIMARY KEY, ord INTEGER, label TEXT, value REAL, unit TEXT, status TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS fuel_prices(
  year_month TEXT PRIMARY KEY, price REAL, source TEXT);
CREATE TABLE IF NOT EXISTS imports(
  year_month TEXT PRIMARY KEY, file_name TEXT, trips INTEGER, other_rows INTEGER,
  imported_at TEXT, imported_by TEXT);
"""

COMPANY, REF = "ข้อมูลจากบริษัท", "ค่าอ้างอิง"

# ตารางที่ 3.5 — key: (ลำดับ, ชื่อ, ค่า, หน่วย, สถานะ, แหล่งที่มา)
FLEET = {
    "fleet_total": (1, "จำนวนรถทั้งหมด", 173, "คัน", COMPANY, "บริษัทกรณีศึกษา"),
    "dep_day": (2, "ค่าเสื่อมราคา (รวมค่าซ่อมบำรุงอื่น)", 494.97, "บาท/คัน/วัน", COMPANY, "บริษัทกรณีศึกษา"),
    "ins_year": (3, "ค่าเบี้ยประกันภัย", 5000, "บาท/คัน/ปี", COMPANY, "บริษัทกรณีศึกษา"),
}
PARAMS = {
    "wage_day": (1, "ค่าจ้างพนักงานขับรถ", 500, "บาท/คน/วัน", COMPANY, "บริษัทกรณีศึกษา"),
    "ot_rate": (2, "ค่าทำงานล่วงเวลา", 80, "บาท/ชั่วโมง", COMPANY, "บริษัทกรณีศึกษา"),
    "km_per_l": (3, "อัตราการสิ้นเปลืองเชื้อเพลิง", 11, "กม./ลิตร", COMPANY,
                 "บริษัทกรณีศึกษา สอดคล้องกับกรมการขนส่งทางบก (2560) และศรัณย์ ไชยางพานิช (2566)"),
    "ef_diesel": (4, "ค่าการปล่อยก๊าซเรือนกระจกของดีเซล", 2.7406, "kgCO₂e/ลิตร", REF,
                  "องค์การบริหารจัดการก๊าซเรือนกระจก (2565) และ IPCC (2006)"),
}
FUEL_SOURCE = ("ราคาขายปลีกดีเซล B7 ของ ปตท. (PTT Station) เขตกรุงเทพฯ เฉลี่ยถ่วงน้ำหนักตามจำนวนวัน"
               " ที่ใช้แต่ละราคาในเดือน (บริษัทเติมน้ำมันที่ ปตท.)")
OLD_FUEL_SOURCE = "ราคาเฉลี่ยรายเดือนดีเซล B7 กรุงเทพฯ บริษัท บางจาก คอร์ปอเรชั่น จำกัด (มหาชน) (ม.ป.ป.)"
DEFAULT_FUEL = {"2026-06": 39.25, "2026-07": 36.05, "2026-08": 37.59, "2026-09": 40.26, "2026-10": 42.84}


def get_connection():
  return sqlite3.connect(DB_PATH)


def init_db():
  with get_connection() as c:
    c.executescript(SCHEMA)
    for table, rows in (("params", PARAMS), ("fleet_master", FLEET)):
      for k, v in rows.items():
        c.execute(f"INSERT OR IGNORE INTO {table} VALUES (?,?,?,?,?,?,?)", (k, *v))
    for ym, price in DEFAULT_FUEL.items():
      c.execute("INSERT OR IGNORE INTO fuel_prices VALUES (?,?,?)", (ym, price, FUEL_SOURCE))
    c.execute("UPDATE fuel_prices SET source=? WHERE source=?", (FUEL_SOURCE, OLD_FUEL_SOURCE))


def _exists(c, name):
  return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


# ---------------- ข้อมูลรายเที่ยว ----------------
def save_months(trips, other, qlog, months, file_name, user):
  """บันทึกข้อมูลตามเดือนที่เลือก (ถ้าเดือนนั้นเคยนำเข้าแล้ว จะแทนที่ของเดิมทั้งเดือน)"""
  now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
  with get_connection() as c:
    for ym in months:
      for table in ("trips", "other_billing", "quality_log"):
        if _exists(c, table):
          c.execute(f"DELETE FROM {table} WHERE Year_Month=?", (ym,))
      t = trips[trips["Year_Month"] == ym].copy()
      t["Trip_Date"] = t["Trip_Date"].dt.strftime("%Y-%m-%d")
      t.to_sql("trips", c, if_exists="append", index=False)
      o = other[other["Year_Month"] == ym]
      if len(o):
        o.to_sql("other_billing", c, if_exists="append", index=False)
      q = qlog[qlog["Year_Month"] == ym] if len(qlog) else qlog
      if len(q):
        q.to_sql("quality_log", c, if_exists="append", index=False)
      c.execute("INSERT OR REPLACE INTO imports VALUES (?,?,?,?,?,?)", (ym, file_name, len(t), len(o), now, user))


def delete_month(ym):
  with get_connection() as c:
    for table in ("trips", "other_billing", "quality_log"):
      if _exists(c, table):
        c.execute(f"DELETE FROM {table} WHERE Year_Month=?", (ym,))
    c.execute("DELETE FROM imports WHERE year_month=?", (ym,))


def clear_all_data():
  """ล้างข้อมูลเที่ยววิ่งทุกเดือน (เก็บผู้ใช้ พารามิเตอร์ และราคาน้ำมันไว้)"""
  with get_connection() as c:
    for table in ("trips", "other_billing", "quality_log"):
      c.execute(f"DROP TABLE IF EXISTS {table}")
    c.execute("DELETE FROM imports")


def reset_params():
  """คืนพารามิเตอร์และราคาน้ำมันเป็นค่าเริ่มต้นตามรายงาน (ตารางที่ 3.5)"""
  with get_connection() as c:
    for table in ("params", "fleet_master", "fuel_prices"):
      c.execute(f"DELETE FROM {table}")
  init_db()


def _read(table):
  with get_connection() as c:
    return pd.read_sql(f"SELECT * FROM {table}", c) if _exists(c, table) else pd.DataFrame()


def load_trips():
  t = _read("trips")
  if len(t):
    t["Trip_Date"] = pd.to_datetime(t["Trip_Date"])
  return t


def load_other():
  return _read("other_billing")


def load_quality_log():
  return _read("quality_log")


def load_imports():
  with get_connection() as c:
    return pd.read_sql("SELECT * FROM imports ORDER BY year_month", c)


# ---------------- พารามิเตอร์ ----------------
def load_param_table():
  """ตารางที่ 3.5 ทั้งหมด (fleet_master + params) เรียงตามลำดับในรายงาน"""
  with get_connection() as c:
    f = pd.read_sql("SELECT * FROM fleet_master ORDER BY ord", c).assign(table="fleet_master")
    p = pd.read_sql("SELECT * FROM params ORDER BY ord", c).assign(table="params")
  return pd.concat([f.iloc[:1], p, f.iloc[1:]], ignore_index=True)


def param_values():
  t = load_param_table()
  return {k: float(v) for k, v in zip(t["key"], t["value"]) if pd.notna(v)}


def update_param(table, key, value, source):
  assert table in ("params", "fleet_master")
  with get_connection() as c:
    c.execute(f"UPDATE {table} SET value=?, source=? WHERE key=?", (value, source, key))


def load_fuel_prices():
  with get_connection() as c:
    return pd.read_sql("SELECT * FROM fuel_prices ORDER BY year_month", c)


def fuel_dict():
  f = load_fuel_prices()
  return dict(zip(f["year_month"], f["price"]))


def upsert_fuel_price(ym, price, source):
  with get_connection() as c:
    c.execute("INSERT OR REPLACE INTO fuel_prices VALUES (?,?,?)", (ym, price, source))


def data_version():
  """ค่าที่เปลี่ยนทุกครั้งที่ฐานข้อมูลถูกแก้ไข (ใช้ล้าง cache การคำนวณ)"""
  return os.stat(DB_PATH).st_mtime_ns if os.path.exists(DB_PATH) else 0
