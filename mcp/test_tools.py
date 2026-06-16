"""Direct smoke test of MCP tool logic (no transport, no client).

Verifies the tools resolve the agent, enforce scope, and hit live Neon data.
Run with INVENTORYLIVE_API_KEY set to an agent key.
"""
import os
import server  # imports the tools and sets up sys.path to backend

def main():
    key = os.environ.get("INVENTORYLIVE_API_KEY", "")
    print(f"Using API key: {key[:12]}...\n")

    print("== check_availability (max 30000000 PKR) ==")
    avail = server.check_availability(max_price_pkr=30_000_000)
    print(f"  {len(avail)} available units in scope")
    if avail:
        print(f"  e.g. {avail[0]}")

    print("\n== inventory_summary (Bahria) ==")
    print(f"  {server.inventory_summary(project='Bahria')}")

    if avail:
        uid = avail[0]["unit_id"]
        print(f"\n== get_unit_details (unit {uid}) ==")
        print(f"  {server.get_unit_details(unit_id=uid)}")

        print(f"\n== reserve_unit (unit {uid}) ==")
        print(f"  {server.reserve_unit(unit_id=uid)}")

        print(f"\n== reserve_unit AGAIN (should fail) ==")
        print(f"  {server.reserve_unit(unit_id=uid)}")


if __name__ == "__main__":
    main()