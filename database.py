import sqlite3
import pandas as pd


def get_connection():
  return sqlite3.connect("transport.db")


def process_and_save_excel(file_path):
  # ใช้ sheet_name=0 เพื่อให้อ่านชีตแรกสุดของไฟล์ Excel ทันทีโดยไม่สนชื่อชีต (Title)
  df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")

  # ทำความสะอาดชื่อคอลัมน์ (ตัดช่องว่างออกป้องกัน Error)
  df.columns = df.columns.str.strip()

  conn = get_connection()
  # บันทึกลงตาราง Trips ใน SQLite
  df.to_sql("Trips", conn, if_exists="replace", index=False)
  conn.close()

  return len(df)


def load_data_from_db():
  conn = get_connection()
  try:
    df = pd.read_sql("SELECT * FROM Trips", conn)
  except Exception:
    df = pd.DataFrame()
  finally:
    conn.close()
  return df
