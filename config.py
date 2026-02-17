"""
Configuration for RFID Attendance System
"""
import os

# Flask Configuration
SECRET_KEY = os.urandom(24)  # Change this to a fixed key in production
DEBUG = True

# Database
DATABASE_PATH = 'attendance.db'

# RFID Scanner Settings
RFID_ENABLED = True  # Set to False for testing without hardware
RFID_SCAN_INTERVAL = 0.3  # Seconds between scans

# Auto-checkout settings
AUTO_CHECKOUT_TIME = "17:00"  # 5:00 PM
AUTO_CHECKOUT_ENABLED = True

# System settings
MAX_OCCUPANCY = 30
SESSION_TIMEOUT = 3600  # 1 hour in seconds

# Audio/Visual feedback (for future hardware integration)
BEEP_ON_SCAN = True
LED_FEEDBACK = True
