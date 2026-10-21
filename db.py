from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "myproject.db"


def get_connection() -> sqlite3.Connection:
    """Create a SQLite connection safe for Streamlit reruns."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_table (
                id_num INTEGER PRIMARY KEY AUTOINCREMENT,
                userid TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profile_table (
                id_num INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id_num INTEGER NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                address TEXT NOT NULL,
                phone TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id_num) REFERENCES user_table(id_num)
            )
            """
        )
        conn.commit()


def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_value: str) -> bool:
    try:
        salt_hex, expected_hex = stored_value.split("$", 1)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, TypeError):
        return False
    actual_hex = _hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(actual_hex, expected_hex)


def create_user(userid: str, username: str, password: str, email: str) -> tuple[bool, str]:
    created_at = datetime.now().isoformat(timespec="seconds")
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO user_table(userid, username, password, email, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (userid.strip(), username.strip(), _hash_password(password), email.strip().lower(), created_at),
            )
            conn.commit()
        return True, "사용자 등록이 완료되었습니다. 이제 로그인해 주세요."
    except sqlite3.IntegrityError as exc:
        msg = str(exc).lower()
        if "userid" in msg:
            return False, "이미 사용 중인 아이디입니다."
        if "email" in msg:
            return False, "이미 등록된 이메일입니다."
        return False, "중복된 사용자 정보가 있습니다."


def authenticate_user(userid: str, password: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id_num, userid, username, password, email, created_at FROM user_table WHERE userid = ?",
            (userid.strip(),),
        ).fetchone()
    if row and _verify_password(password, row["password"]):
        return {key: row[key] for key in row.keys() if key != "password"}
    return None


def add_profile(user_id_num: int, name: str, age: int, address: str, phone: str) -> None:
    created_at = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO profile_table(user_id_num, name, age, address, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id_num, name.strip(), int(age), address.strip(), phone.strip(), created_at),
        )
        conn.commit()


def get_profiles(user_id_num: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id_num, name, age, address, phone, created_at
            FROM profile_table
            WHERE user_id_num = ?
            ORDER BY id_num DESC
            """,
            (user_id_num,),
        ).fetchall()
    return [dict(row) for row in rows]
