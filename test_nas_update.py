"""
Test kết nối NAS WebDAV và download SystemCheck.exe
Chạy: python test_nas_update.py
"""

import requests
from requests.auth import HTTPBasicAuth

url      = "https://domain:port/path/to/SystemCheck.exe"
user     = "username"
password = "password"

print("=" * 50)
print("TEST NAS WEBDAV - SystemCheck.exe")
print("=" * 50)

print(f"\n[1] Kết nối: {url}")
response = requests.get(url, auth=HTTPBasicAuth(user, password), stream=True, timeout=60)
print(f"    Status : {response.status_code}")
print(f"    Size   : {int(response.headers.get('Content-Length', 0)) / 1024 / 1024:.1f} MB")

if response.status_code != 200:
    print(f"\n❌ Lỗi kết nối: HTTP {response.status_code}")
    exit(1)

print("\n[2] Kiểm tra file...")
content = response.content
size_mb = len(content) / 1024 / 1024
print(f"    Đã tải : {size_mb:.1f} MB")
print(f"    2 bytes đầu: {content[:2].hex().upper()}")

if content[:2] != b'MZ':
    print(f"\n❌ FAIL: Không phải EXE hợp lệ (cần 'MZ', thực tế '{content[:2].hex().upper()}')")
    print("   → Upload đúng file SystemCheck.exe lên NAS rồi thử lại.")
    exit(1)

if size_mb < 5:
    print(f"\n❌ FAIL: File quá nhỏ ({size_mb:.1f} MB), nghi upload sai file.")
    exit(1)

print("\n[3] Lưu file test...")
with open("Test_SystemCheck.exe", "wb") as f:
    f.write(content)
print("    Đã lưu: Test_SystemCheck.exe")

print("\n✅ PASS: Kết nối NAS thành công, file EXE hợp lệ!")
print(f"   Sẵn sàng dùng /update trên bot.")
print("=" * 50)
