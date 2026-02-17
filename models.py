"""
Database models for RFID Attendance System
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager

DATABASE_PATH = 'attendance.db'

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database with required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table - stores card assignments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfid_uid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                student_id TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                graduating_year INTEGER NOT NULL,
                assigned_task TEXT DEFAULT 'No task assigned',
                is_approved BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check-ins table - tracks all check-in/out events
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                check_in_time TIMESTAMP NOT NULL,
                check_out_time TIMESTAMP,
                auto_checkout BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Admins table - for authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Settings table - for system configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Insert default settings
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('max_occupancy', '30'),
                   ('auto_checkout_time', '17:00'),
                   ('auto_checkout_enabled', '1')
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rfid_uid ON users(rfid_uid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_id ON users(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_checkin_user ON checkins(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_checkin_time ON checkins(check_in_time)')
        
        conn.commit()
        print("Database initialized successfully!")

# User operations
def create_user(rfid_uid, name, student_id, email, graduating_year, assigned_task='No task assigned'):
    """Create a new user with RFID card assignment"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (rfid_uid, name, student_id, email, graduating_year, assigned_task, is_approved)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (rfid_uid, name, student_id, email, graduating_year, assigned_task))
        return cursor.lastrowid

def get_user_by_rfid(rfid_uid):
    """Get user by RFID UID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE rfid_uid = ?', (rfid_uid,))
        return cursor.fetchone()

def get_user_by_id(user_id):
    """Get user by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()

def get_all_users():
    """Get all users"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY name')
        return cursor.fetchall()

def update_user(user_id, name=None, student_id=None, email=None, graduating_year=None, assigned_task=None):
    """Update user information"""
    with get_db() as conn:
        cursor = conn.cursor()
        updates = []
        params = []
        
        if name: 
            updates.append('name = ?')
            params.append(name)
        if student_id: 
            updates.append('student_id = ?')
            params.append(student_id)
        if email: 
            updates.append('email = ?')
            params.append(email)
        if graduating_year: 
            updates.append('graduating_year = ?')
            params.append(graduating_year)
        if assigned_task is not None: 
            updates.append('assigned_task = ?')
            params.append(assigned_task)
        
        if updates:
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

def delete_user(user_id):
    """Delete user and all their check-in records"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM checkins WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))

# Check-in operations
def check_in(user_id):
    """Check in a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Check if user is already checked in
        cursor.execute('''
            SELECT id FROM checkins 
            WHERE user_id = ? AND check_out_time IS NULL
        ''', (user_id,))
        
        if cursor.fetchone():
            return False, "Already checked in"
        
        cursor.execute('''
            INSERT INTO checkins (user_id, check_in_time)
            VALUES (?, ?)
        ''', (user_id, datetime.now()))
        return True, "Checked in successfully"

def check_out(user_id, auto=False):
    """Check out a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE checkins 
            SET check_out_time = ?, auto_checkout = ?
            WHERE user_id = ? AND check_out_time IS NULL
        ''', (datetime.now(), auto, user_id))
        
        if cursor.rowcount > 0:
            return True, "Checked out successfully"
        return False, "Not checked in"

def get_current_checkins():
    """Get all users currently checked in"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, c.check_in_time, c.id as checkin_id
            FROM users u
            JOIN checkins c ON u.id = c.user_id
            WHERE c.check_out_time IS NULL
            ORDER BY c.check_in_time DESC
        ''')
        return cursor.fetchall()

def get_user_status(user_id):
    """Check if user is currently checked in"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM checkins 
            WHERE user_id = ? AND check_out_time IS NULL
        ''', (user_id,))
        return cursor.fetchone() is not None

def get_user_history(user_id, limit=50):
    """Get check-in history for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM checkins 
            WHERE user_id = ?
            ORDER BY check_in_time DESC
            LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()

def get_all_checkins(start_date=None, end_date=None):
    """Get all check-in records with optional date filtering"""
    with get_db() as conn:
        cursor = conn.cursor()
        if start_date and end_date:
            cursor.execute('''
                SELECT c.*, u.name, u.student_id, u.email
                FROM checkins c
                JOIN users u ON c.user_id = u.id
                WHERE c.check_in_time BETWEEN ? AND ?
                ORDER BY c.check_in_time DESC
            ''', (start_date, end_date))
        else:
            cursor.execute('''
                SELECT c.*, u.name, u.student_id, u.email
                FROM checkins c
                JOIN users u ON c.user_id = u.id
                ORDER BY c.check_in_time DESC
                LIMIT 500
            ''')
        return cursor.fetchall()

# Admin operations
def create_admin(username, password_hash, full_name):
    """Create admin account"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO admins (username, password_hash, full_name)
            VALUES (?, ?, ?)
        ''', (username, password_hash, full_name))
        return cursor.lastrowid

def get_admin_by_username(username):
    """Get admin by username"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins WHERE username = ?', (username,))
        return cursor.fetchone()

# Settings operations
def get_setting(key):
    """Get a setting value"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result['value'] if result else None

def update_setting(key, value):
    """Update a setting value"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        ''', (key, value))

# Auto-checkout operations
def auto_checkout_all():
    """Auto checkout all currently checked-in users"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE checkins 
            SET check_out_time = ?, auto_checkout = 1
            WHERE check_out_time IS NULL
        ''', (datetime.now(),))
        return cursor.rowcount

if __name__ == '__main__':
    init_db()
    print("Database setup complete!")
