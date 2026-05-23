"""
抖音小游戏直接 API 上传 - 使用浏览器 cookies
"""
import os
import json
import requests
import zipfile
import io
import time

APP_ID = "tte7a1911c79c6fc8302"
GAME_DIR = "D:/games/match3-xiaoxiaoxiao"
COOKIE_DEBUG = os.path.expanduser("~/.tmg-cli/cookies_debug.json")
UPLOAD_URL = f"https://developer.toutiao.com/api/developer/ide/microgame/v1/testing?appid={APP_ID}"
META_URL = f"https://developer.toutiao.com/api/v2/app/{APP_ID}/meta"
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://developer.open-douyin.com/",
    "Origin": "https://developer.open-douyin.com",
}

def load_cookies():
    with open(COOKIE_DEBUG, "r") as f:
        raw_cookies = json.load(f)
    # Build cookie dict and string
    cookie_dict = {}
    cookie_parts = []
    for c in raw_cookies:
        name = c["name"]
        value = c["value"]
        cookie_dict[name] = value
        cookie_parts.append(f"{name}={value}")
    cookie_string = "; ".join(cookie_parts)
    return cookie_string

def create_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(GAME_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, GAME_DIR)
                zf.write(file_path, arcname)
    buf.seek(0)
    return buf

def main():
    cookie_string = load_cookies()
    print(f"[1] Cookies loaded ({len(cookie_string)} chars)")

    # First, check if session is valid by getting user info
    headers = {**BASE_HEADERS, "Cookie": cookie_string}
    print("[2] Checking session...")
    resp = requests.get("https://developer.open-douyin.com/api/admin/user/info",
                       headers=headers, timeout=30)
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        try:
            data = resp.json()
            print(f"  Response: {json.dumps(data, ensure_ascii=False)[:300]}")
        except:
            print(f"  Response text: {resp.text[:300]}")
    else:
        print(f"  Response: {resp.text[:300]}")

    # Try getting meta info
    print("[3] Getting app meta...")
    resp = requests.get(META_URL, headers=headers, timeout=30)
    print(f"  Status: {resp.status_code}")
    try:
        data = resp.json()
        print(f"  Response: {json.dumps(data, ensure_ascii=False)[:500]}")
    except:
        print(f"  Response: {resp.text[:300]}")

    # Try upload
    print("[4] Creating zip package...")
    zip_buf = create_zip()
    zip_size = zip_buf.getbuffer().nbytes
    print(f"  Zip size: {zip_size} bytes")

    print("[5] Uploading to Douyin...")
    files = {
        "package": (f"{APP_ID}.zip", zip_buf, "application/zip"),
    }
    upload_data = {
        "appid": APP_ID,
        "version": "1.0.0",
        "desc": "初始版本-三消小游戏",
    }

    resp = requests.post(UPLOAD_URL, headers=headers, files=files,
                        data=upload_data, timeout=120)
    print(f"  Status: {resp.status_code}")
    try:
        data = resp.json()
        print(f"  Response: {json.dumps(data, ensure_ascii=False)[:500]}")
    except:
        print(f"  Response: {resp.text[:500]}")

    # Also try the v2 upload endpoint
    print("[6] Trying v2 upload endpoint...")
    zip_buf.seek(0)
    v2_url = f"https://developer.toutiao.com/api/v2/app/{APP_ID}/testing"
    resp = requests.post(v2_url, headers=headers, files=files,
                        data=upload_data, timeout=120)
    print(f"  Status: {resp.status_code}")
    try:
        data = resp.json()
        print(f"  Response: {json.dumps(data, ensure_ascii=False)[:500]}")
    except:
        print(f"  Response: {resp.text[:500]}")

if __name__ == "__main__":
    main()
