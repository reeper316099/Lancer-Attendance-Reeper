import os

import board
import busio
from adafruit_pn532.i2c import PN532_I2C
import hashlib
import time

i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)
pn532.SAM_configuration()

MIFARE_CMD_AUTH_A = 0x60
KEY_DEFAULT = b'\xFF\xFF\xFF\xFF\xFF\xFF'
BLOCK = 4

class CardScanner:

    @staticmethod
    def write_card(input_string):
        print("Place card to write...")

        while True:
            uid = pn532.read_passive_target(timeout=0.5)
            if uid:
                print("UID:", [hex(x) for x in uid])
                if len(uid) != 4:
                    print("This card is not a MIFARE Classic tag. Aborting.")
                    return False

                if not pn532.mifare_classic_authenticate_block(uid, BLOCK, MIFARE_CMD_AUTH_A, KEY_DEFAULT):
                    print("Authentication failed.")
                    return False

                data = input_string.encode("utf-8")
                if len(data) > 16:
                    print("Input string too long for a single block (16 bytes max).")
                    return False

                padded_data = data.ljust(16, b'\x00')

                for attempt in range(1, 4):
                    success = pn532.mifare_classic_write_block(BLOCK, padded_data)
                    if success:
                        return True
                    else:
                        time.sleep(0.1)

                return False

            time.sleep(0.1)

    @staticmethod
    def read_card():
        print("Place card to read...")

        while True:
            uid = pn532.read_passive_target(timeout=0.5)

            if not uid:
                time.sleep(0.1)
                continue

            print("UID:", [hex(x) for x in uid])

            if len(uid) != 4:
                print("This card is not a MIFARE Classic tag. Aborting.")
                return None

            if not pn532.mifare_classic_authenticate_block(uid, BLOCK, MIFARE_CMD_AUTH_A, KEY_DEFAULT):
                print("Authentication failed.")
                return None

            block_data = pn532.mifare_classic_read_block(BLOCK)
            if not block_data:
                print("Read failed.")
                return None

            print("Read success.")

            while pn532.read_passive_target(timeout=0.5):
                time.sleep(0.1)

            try:
                return bytes(block_data).decode("utf-8").strip('\x00')
            except UnicodeDecodeError:
                print("Invalid UTF-8 data.")
                return None

if __name__ == "__main__":
    os.system("clear")
    print("\n\nMake sure that you enter the correct card ID for the correct student\n")

    while True:
        card_id = input("Card ID (######): ")

        if not card_id.isdigit() or len(card_id) != 6:
            print("Invalid card ID, please try again.")
            continue

        break

    if CardScanner.write_card(card_id):
        print(f"\n{card_id} successfully written to card!\nPlease double check to make sure no mistakes were made.\n")
    else:
        print("\nWrite failed, please try again\n")

