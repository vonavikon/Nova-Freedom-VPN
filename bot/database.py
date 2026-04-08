"""
Database Manager for Nova VPN Bot
SQLite-based storage for users and devices
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

# User status constants
STATUS_PENDING = 'pending'
STATUS_APPROVED = 'approved'
STATUS_REJECTED = 'rejected'


class Database:
    """SQLite database manager"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info("Database initialized successfully")

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Devices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_name TEXT NOT NULL,
                public_key TEXT,
                private_key TEXT,
                protocol TEXT DEFAULT 'hiddify',
                ip_address TEXT,
                preshared_key TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, device_name)
            )
        """)

        conn.commit()
        conn.close()

    def get_or_create_user(self, telegram_id: int, username: str = None,
                           first_name: str = None, last_name: str = None) -> Dict:
        """Get or create user by Telegram ID"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()

        if row:
            user = dict(row)
            # Update info if changed
            if username != user.get('username') or first_name != user.get('first_name'):
                cursor.execute("""
                    UPDATE users SET username = ?, first_name = ?, last_name = ?, updated_at = ?
                    WHERE telegram_id = ?
                """, (username, first_name, last_name, datetime.now(), telegram_id))
                conn.commit()
                user['username'] = username
                user['first_name'] = first_name
                user['last_name'] = last_name
        else:
            cursor.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            """, (telegram_id, username, first_name, last_name))
            conn.commit()
            user = {
                'id': cursor.lastrowid,
                'telegram_id': telegram_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'status': STATUS_PENDING
            }
            logger.info(f"Created new user: {telegram_id}")

        conn.close()
        return user

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def add_device(self, user_id: int, device_name: str, public_key: str,
                   private_key: str, protocol: str = 'hiddify',
                   ip_address: str = None, preshared_key: str = None) -> Optional[int]:
        """Add new device for user"""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO devices (user_id, device_name, public_key, private_key, protocol, ip_address, preshared_key)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, device_name, public_key, private_key, protocol, ip_address, preshared_key))
            conn.commit()
            device_id = cursor.lastrowid
            logger.info(f"Added device {device_name} (ID: {device_id}) for user {user_id}")
            return device_id
        except sqlite3.IntegrityError:
            logger.warning(f"Device {device_name} already exists for user {user_id}")
            return None
        finally:
            conn.close()

    def get_device(self, device_id: int) -> Optional[Dict]:
        """Get device by ID"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_device_by_name(self, user_id: int, device_name: str) -> Optional[Dict]:
        """Get device by name for user"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE user_id = ? AND device_name = ?", (user_id, device_name))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_user_devices(self, user_id: int) -> List[Dict]:
        """Get all devices for user"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def remove_device(self, device_id: int) -> bool:
        """Remove device by ID"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        if deleted:
            logger.info(f"Removed device {device_id}")
        return deleted

    def get_device_count(self, user_id: int) -> int:
        """Get device count for user"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM devices WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_pending_users(self) -> List[Dict]:
        """Get all pending users"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE status = ? ORDER BY created_at DESC", (STATUS_PENDING,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def approve_user(self, telegram_id: int) -> bool:
        """Approve user by Telegram ID"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET status = ?, updated_at = ?
            WHERE telegram_id = ?
        """, (STATUS_APPROVED, datetime.now(), telegram_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        if success:
            logger.info(f"User {telegram_id} approved")
        return success

    def reject_user(self, telegram_id: int) -> bool:
        """Reject user by Telegram ID"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET status = ?, updated_at = ?
            WHERE telegram_id = ?
        """, (STATUS_REJECTED, datetime.now(), telegram_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        if success:
            logger.info(f"User {telegram_id} rejected")
        return success

    def is_user_approved(self, telegram_id: int) -> bool:
        """Check if user is approved"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        conn.close()
        return bool(row and row['status'] == STATUS_APPROVED)

    def get_user_status(self, telegram_id: int) -> Optional[str]:
        """Get user status"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        conn.close()
        return row['status'] if row else None

    def get_stats(self) -> Dict:
        """Get statistics"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE status = ?", (STATUS_APPROVED,))
        approved_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE status = ?", (STATUS_PENDING,))
        pending_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE status = ?", (STATUS_REJECTED,))
        rejected_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM devices")
        total_devices = cursor.fetchone()[0]

        conn.close()
        return {
            'total_users': total_users,
            'approved_users': approved_users,
            'pending_users': pending_users,
            'rejected_users': rejected_users,
            'total_devices': total_devices
        }

    def delete_user(self, user_id: int) -> bool:
        """Delete user by ID"""
        conn = self._get_conn()
        cursor = conn.cursor()
        # First delete all user devices
        cursor.execute("DELETE FROM devices WHERE user_id = ?", (user_id,))
        # Then delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        if success:
            logger.info(f"User {user_id} deleted")
        return success

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by internal ID"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
