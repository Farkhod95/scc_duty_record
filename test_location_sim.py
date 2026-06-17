#!/usr/bin/env python3
"""
Chilonzor xududidagi xodimlar uchun GPS simulyator.
Har 10 soniyada map/live/ dan xodimlarni olib, gRPC orqali lokatsiya yuboradi.

Ishga tushirish:
    pip install requests grpcio grpcio-tools
    python test_location_sim.py
"""

import sys
import os
import time
import random
import math
import requests
import grpc

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "proto"))
from proto import location_service_pb2, location_service_pb2_grpc

# ─── Konfiguratsiya ───────────────────────────────────────────────────────────
API_BASE    = "http://192.168.168.24:8080/api/v1"
GRPC_ADDR   = "192.168.168.24:50051"
USERNAME    = "officer"
PASSWORD    = "q1w2e3"
INTERVAL    = 10   # soniya

# Chilonzor markaziy koordinatasi
CHILONZOR_LAT = 41.2995
CHILONZOR_LON = 69.2401
RADIUS_M      = 500   # simulyatsiya radiusi (metr)
# ─────────────────────────────────────────────────────────────────────────────

def get_token():
    r = requests.post(f"{API_BASE}/auth/token/",
                      json={"username": USERNAME, "password": PASSWORD}, timeout=10)
    r.raise_for_status()
    return r.json()["access"]

def get_live_employees(token):
    r = requests.get(f"{API_BASE}/map/live/",
                     headers={"Authorization": f"Bearer {token}"}, timeout=10)
    r.raise_for_status()
    data = r.json()
    employees = []
    for item in data.get("results", []):
        if "type" not in item and item.get("pinfl_hash"):
            employees.append(item["pinfl_hash"])
    return employees

def random_nearby(lat, lon, radius_m):
    """radius_m metr doirasida tasodifiy koordinata."""
    angle = random.uniform(0, 2 * math.pi)
    dist  = random.uniform(0, radius_m)
    dlat  = (dist * math.cos(angle)) / 111320
    dlon  = (dist * math.sin(angle)) / (111320 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon

def send_locations(stub, pinfl_hashes):
    sent = 0
    for pinfl in pinfl_hashes:
        lat, lon = random_nearby(CHILONZOR_LAT, CHILONZOR_LON, RADIUS_M)
        req = location_service_pb2.LocationRequest(
            pinfl_hash=pinfl,
            latitude=lat,
            longitude=lon,
            accuracy=5.0,
            timestamp=int(time.time() * 1000),
        )
        try:
            stub.Location(req, timeout=5)
            sent += 1
        except grpc.RpcError as e:
            print(f"  [!] gRPC xato {pinfl[:8]}...: {e.code()} — {e.details()}")
    return sent

def main():
    print(f"Server: {API_BASE}")
    print(f"gRPC:   {GRPC_ADDR}")
    print(f"Chilonzor markazi: {CHILONZOR_LAT}, {CHILONZOR_LON}  radius: {RADIUS_M}m")
    print(f"Interval: {INTERVAL}s\n")

    # Token olish
    print("Login qilinmoqda...")
    try:
        token = get_token()
        print("Token olindi.\n")
    except Exception as e:
        print(f"Login xato: {e}")
        sys.exit(1)

    token_refreshed_at = time.time()

    # gRPC ulanish
    channel = grpc.insecure_channel(GRPC_ADDR)
    stub    = location_service_pb2_grpc.LocationServiceStub(channel)

    iteration = 0
    while True:
        iteration += 1

        # Har 5 daqiqada token yangilash
        if time.time() - token_refreshed_at > 300:
            try:
                token = get_token()
                token_refreshed_at = time.time()
            except Exception:
                pass

        # Xodimlarni olish
        try:
            employees = get_live_employees(token)
        except Exception as e:
            print(f"[{iteration}] map/live/ xato: {e}")
            time.sleep(INTERVAL)
            continue

        if not employees:
            print(f"[{iteration}] Aktiv xodim yo'q — navbatchilik boshlanmagan bo'lishi mumkin.")
            time.sleep(INTERVAL)
            continue

        # Lokatsiya yuborish
        sent = send_locations(stub, employees)
        print(f"[{iteration}] {sent}/{len(employees)} xodimga lokatsiya yuborildi  "
              f"(lat≈{CHILONZOR_LAT:.4f}, lon≈{CHILONZOR_LON:.4f})")

        time.sleep(INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTo'xtatildi.")
