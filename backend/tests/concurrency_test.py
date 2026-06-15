"""Concurrency proof: two agents reserve the SAME unit simultaneously.

Exactly one must succeed (200) and the other must be cleanly rejected (409).
This demonstrates the SELECT FOR UPDATE row lock preventing double-selling.

Usage:
    python -m tests.concurrency_test
"""
import concurrent.futures
import requests

BASE = "http://localhost:8005"
EMAIL = "agent_a@demo.com"
PASSWORD = "demo1234"


def login() -> str:
    r = requests.post(f"{BASE}/api/auth/login",
                      data={"username": EMAIL, "password": PASSWORD})
    r.raise_for_status()
    return r.json()["access_token"]


def first_available_unit(token: str) -> int:
    r = requests.get(f"{BASE}/api/units", params={"status": "available"},
                     headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    units = r.json()
    if not units:
        raise SystemExit("No available units — reseed first.")
    return units[0]["id"]


def reserve(token: str, unit_id: int) -> tuple[int, str]:
    r = requests.post(f"{BASE}/api/units/{unit_id}/reserve",
                      headers={"Authorization": f"Bearer {token}"})
    return r.status_code, r.text


def main():
    token = login()
    unit_id = first_available_unit(token)
    print(f"Targeting unit {unit_id} with 2 simultaneous reservations...\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(reserve, token, unit_id) for _ in range(2)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    codes = sorted(c for c, _ in results)
    for code, body in results:
        tag = "WON " if code == 200 else "LOST"
        print(f"  [{tag}] HTTP {code}: {body[:120]}")

    print()
    if codes == [200, 409]:
        print("PASS: exactly one reservation succeeded. Double-sell prevented.")
    else:
        print(f"FAIL: expected [200, 409], got {codes}.")


if __name__ == "__main__":
    main()