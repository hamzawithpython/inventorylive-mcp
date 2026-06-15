"""Live WebSocket listener for manual testing.

Connects as agent_a, prints every unit_changed event pushed by the server.
Run this, then reserve a unit via /docs in another window and watch it appear.

Usage:
    python -m tests.ws_listen
"""
import asyncio
import json
import requests
import websockets

BASE = "http://localhost:8005"
WS_BASE = "ws://localhost:8005"
EMAIL = "agent_a@demo.com"
PASSWORD = "demo1234"


def login() -> str:
    r = requests.post(f"{BASE}/api/auth/login",
                      data={"username": EMAIL, "password": PASSWORD})
    r.raise_for_status()
    return r.json()["access_token"]


async def listen():
    token = login()
    uri = f"{WS_BASE}/ws?token={token}"
    async with websockets.connect(uri) as ws:
        print(f"Connected as {EMAIL}. Waiting for unit_changed events...")
        print("(Reserve a unit via /docs in another window.)\n")
        while True:
            msg = await ws.recv()
            event = json.loads(msg)
            uid = event["unit_id"]
            status = event["status"]
            version = event["version"]
            source = event["source"]
            print(f"  LIVE EVENT: unit {uid} -> {status} (v{version}, source={source})")


if __name__ == "__main__":
    asyncio.run(listen())