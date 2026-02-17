"""
RFID Scanner - PN532 Version for Raspberry Pi 5
Uses Adafruit CircuitPython PN532 library
"""
import time
import sys
from datetime import datetime

# Try to import PN532 library
try:
    import board
    import busio
    from adafruit_pn532.i2c import PN532_I2C
    HARDWARE_AVAILABLE = True
    print("✓ Using PN532 NFC module (Adafruit library)")
except ImportError:
    print("WARNING: PN532 library not found. Running in simulation mode.")
    HARDWARE_AVAILABLE = False

import models
from config import RFID_SCAN_INTERVAL

class RFIDScanner:
    def __init__(self):
        if HARDWARE_AVAILABLE:
            try:
                # Initialize I2C and PN532
                i2c = busio.I2C(board.SCL, board.SDA)
                self.reader = PN532_I2C(i2c, debug=False)
                
                # Get firmware version to verify connection
                ic, ver, rev, support = self.reader.firmware_version
                print(f"✓ PN532 initialized - Firmware v{ver}.{rev}")
                
                # Configure SAM
                self.reader.SAM_configuration()
                print("✓ PN532 configured and ready")
                
                self.hardware_available = True
            except Exception as e:
                print(f"Error initializing PN532: {e}")
                print("Running in simulation mode")
                self.reader = None
                self.hardware_available = False
        else:
            self.reader = None
            self.hardware_available = False
        
        self.last_scan_uid = None
        self.last_scan_time = 0
        self.scan_cooldown = 2  # Seconds to prevent double-scans
    
    def read_card(self):
        """Read NFC/RFID card and return UID"""
        if not self.reader:
            return None
        
        try:
            # Try to read a card (non-blocking)
            uid = self.reader.read_passive_target(timeout=0.1)
            if uid:
                # Convert UID bytes to string
                uid_string = ''.join([str(x) for x in uid])
                return uid_string
        except Exception as e:
            # Silently ignore - normal when no card present
            pass
        return None
    
    def process_scan(self, rfid_uid):
        """Process a card scan - check in or check out"""
        current_time = time.time()
        if rfid_uid == self.last_scan_uid and (current_time - self.last_scan_time) < self.scan_cooldown:
            return None
        
        self.last_scan_uid = rfid_uid
        self.last_scan_time = current_time
        
        user = models.get_user_by_rfid(rfid_uid)
        
        if not user:
            print(f"⚠️  Unknown card: {rfid_uid}")
            self.beep(pattern='error')
            return {'status': 'error', 'message': 'Card not registered'}
        
        is_checked_in = models.get_user_status(user['id'])
        
        if is_checked_in:
            success, message = models.check_out(user['id'])
            if success:
                print(f"✓ {user['name']} checked OUT at {datetime.now().strftime('%H:%M:%S')}")
                self.beep(pattern='checkout')
                return {
                    'status': 'checkout',
                    'user': dict(user),
                    'message': f"{user['name']} checked out"
                }
        else:
            success, message = models.check_in(user['id'])
            if success:
                print(f"✓ {user['name']} checked IN at {datetime.now().strftime('%H:%M:%S')}")
                self.beep(pattern='checkin')
                return {
                    'status': 'checkin',
                    'user': dict(user),
                    'message': f"{user['name']} checked in"
                }
        
        return None
    
    def beep(self, pattern='single'):
        """Audio feedback"""
        if pattern == 'checkin':
            print("♪ BEEP!")
        elif pattern == 'checkout':
            print("♪♪ BEEP BEEP!")
        elif pattern == 'error':
            print("⚠️  BUZZ!")
    
    def run(self):
        """Main scanning loop"""
        print("="*60)
        print("       RFID ATTENDANCE SCANNER - PN532")
        print("="*60)
        if self.hardware_available:
            print("✓ Hardware: PN532 NFC Reader READY")
            print("  Place NFC/RFID card near reader to check in/out")
        else:
            print("⚠️  Hardware: SIMULATION MODE")
        print("\nPress Ctrl+C to stop\n")
        print("-" * 60)
        
        try:
            while True:
                if self.hardware_available:
                    rfid_uid = self.read_card()
                    if rfid_uid:
                        result = self.process_scan(rfid_uid)
                        if result:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f"[{timestamp}] {result['message']}")
                            print("-" * 60)
                
                time.sleep(RFID_SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n" + "="*60)
            print("Scanner stopped")
            print("="*60)
            sys.exit(0)

def manual_scan():
    """Manual scan mode for testing/admin override"""
    scanner = RFIDScanner()
    print("Manual scan mode - scan one card")
    
    if not scanner.hardware_available:
        print("No RFID reader available!")
        return None
    
    print("Place card on reader...")
    rfid_uid = scanner.read_card()
    if rfid_uid:
        result = scanner.process_scan(rfid_uid)
        return result
    return None

if __name__ == '__main__':
    models.init_db()
    scanner = RFIDScanner()
    scanner.run()
