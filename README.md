# InventoryLive-MCP

**Real-time real estate inventory portal + MCP server ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â two interfaces, one live source of truth.**

Property developers'' in-house agents lack live shared visibility of unit inventory, so two agents can sell the same unit and deals collapse at closing. InventoryLive solves the shared-state problem: one Postgres source of truth, a real-time portal (WebSockets) where every agent sees availability change instantly, and an MCP server exposing the *same* live data ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â with the *same* access control ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â as AI-callable tools.

> All inventory is **synthetic** (generated Pakistani housing-society data). No real developer data.

## Architecture
One database, two doors (portal + MCP server) over a shared service layer. _(Diagram added Phase 8.)_

## Tech Stack
FastAPI Ãƒâ€šÃ‚Â· WebSockets Ãƒâ€šÃ‚Â· PostgreSQL Ãƒâ€šÃ‚Â· SQLAlchemy Ãƒâ€šÃ‚Â· React Ãƒâ€šÃ‚Â· Python MCP (FastMCP) Ãƒâ€šÃ‚Â· Docker

## Status
- [x] Phase 1 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Data model, synthetic seed, read-only API
- [ ] Phase 2 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Auth + RBAC
- [ ] Phase 3 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Reservations + concurrency
- [ ] Phase 4 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Real-time WebSocket push
- [ ] Phase 5 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â React portal
- [ ] Phase 6 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Deploy
- [ ] Phase 7 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â MCP server
- [ ] Phase 8 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Docs + writeup

## Technical Decisions
- **Optimistic locking (`version` column) + `SELECT FOR UPDATE`** for reservation concurrency ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â prevents double-selling.
- **Shared service layer** so portal and MCP enforce identical logic and permissions.
- **HTTP/SSE MCP transport** (not stdio) so the server is remotely hostable over live data.

## What Didn''t Work / Lessons
- Postgres in Docker only applies credentials on first volume init ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â stale volumes cause auth failures; `docker compose down -v` resets them.
- A leftover service squatting on a host port (5434) silently intercepts connections; moved the DB mapping to 5440.
- PowerShell here-strings/redirection inject a BOM that corrupts `.env`/YAML; write config with .NET `WriteAllText` + BOM-less UTF-8.