"""
auth.py — การยืนยันตัวตน (Authentication)

รหัสผ่านไม่ถูกเก็บเป็นข้อความปกติ แต่เก็บเป็นค่าแฮชที่สร้างด้วย bcrypt (มี Salt สุ่มในตัว)
สิทธิ์ผู้ใช้ 2 ระดับ: admin (นำเข้าข้อมูล แก้พารามิเตอร์ จัดการผู้ใช้) และ viewer (ดูอย่างเดียว)
"""
import datetime as dt
import os

import bcrypt

import database as db

ROLES = {"admin": "ผู้ดูแลระบบ", "viewer": "ผู้ใช้งานทั่วไป (ดูอย่างเดียว)"}
DEFAULT_ADMIN = ("admin", os.environ.get("APP_ADMIN_PASSWORD", "admin1234"))


def hash_password(pw):
  return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def ensure_default_admin():
  """สร้างผู้ดูแลระบบเริ่มต้นเมื่อยังไม่มีผู้ใช้ในระบบ (ควรเปลี่ยนรหัสผ่านหลังเข้าใช้ครั้งแรก)"""
  with db.get_connection() as c:
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
      add_user(*DEFAULT_ADMIN, "admin")


def add_user(username, password, role):
  username = username.strip()
  if not username or len(password) < 8:
    raise ValueError("ชื่อผู้ใช้ห้ามว่าง และรหัสผ่านต้องยาวอย่างน้อย 8 ตัวอักษร")
  if role not in ROLES:
    raise ValueError("สิทธิ์ไม่ถูกต้อง")
  with db.get_connection() as c:
    if c.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
      raise ValueError("มีชื่อผู้ใช้นี้แล้ว")
    c.execute("INSERT INTO users VALUES (?,?,?,?)",
              (username, hash_password(password), role, dt.datetime.now().strftime("%Y-%m-%d %H:%M")))


def verify(username, password):
  """คืน role ถ้าชื่อผู้ใช้และรหัสผ่านถูกต้อง ไม่ถูกคืน None"""
  with db.get_connection() as c:
    row = c.execute("SELECT pw_hash, role FROM users WHERE username=?", (username.strip(),)).fetchone()
  if row and bcrypt.checkpw(password.encode("utf-8"), row[0].encode("utf-8")):
    return row[1]
  return None


def change_password(username, old, new):
  if verify(username, old) is None:
    raise ValueError("รหัสผ่านเดิมไม่ถูกต้อง")
  if len(new) < 8:
    raise ValueError("รหัสผ่านใหม่ต้องยาวอย่างน้อย 8 ตัวอักษร")
  with db.get_connection() as c:
    c.execute("UPDATE users SET pw_hash=? WHERE username=?", (hash_password(new), username))


def list_users():
  import pandas as pd
  with db.get_connection() as c:
    return pd.read_sql("SELECT username, role, created_at FROM users ORDER BY username", c)


def delete_user(username):
  with db.get_connection() as c:
    if c.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND username<>?", (username,)).fetchone()[0] == 0:
      raise ValueError("ต้องมีผู้ดูแลระบบอย่างน้อย 1 คน")
    c.execute("DELETE FROM users WHERE username=?", (username,))
