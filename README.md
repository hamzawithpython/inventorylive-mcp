# InventoryLive-MCP

**Real-time real estate inventory portal + MCP server Ã¢â‚¬â€ two interfaces, one live source of truth.**

Property developers'' in-house agents lack live shared visibility of unit inventory, so two agents can sell the same unit and deals collapse at closing. InventoryLive solves the shared-state problem: one Postgres source of truth, a real-time portal (WebSockets) where every agent sees availability change instantly, and an MCP server exposing the *same* live data Ã¢â‚¬â€ with the *same* access control Ã¢â‚¬â€ as AI-callable tools.

> All inventory is **synthetic** (generated Pakistani housing-society data). No real developer data.

## Architecture
One database, two doors (portal + MCP server) over a shared service layer. _(Diagram added Phase 8.)_

## Tech Stack
FastAPI Ã‚Â· WebSockets Ã‚Â· PostgreSQL Ã‚Â· SQLAlchemy Ã‚Â· React Ã‚Â· Python MCP (FastMCP) Ã‚Â· Docker

## Status
- [x] Phase 1 Ã¢â‚¬â€ Data model, synthetic seed, read-only API
- [ ] Phase 2 Ã¢â‚¬â€ Auth + RBAC
- [ ] Phase 3 Ã¢â‚¬â€ Reservations + concurrency
- [ ] Phase 4 Ã¢â‚¬â€ Real-time WebSocket push
- [ ] Phase 5 Ã¢â‚¬â€ React portal
- [ ] Phase 6 Ã¢â‚¬â€ Deploy
- [ ] Phase 7 Ã¢â‚¬â€ MCP server
- [ ] Phase 8 Ã¢â‚¬â€ Docs + writeup

## Technical Decisions
- **Optimistic locking (`version` column) + `SELECT FOR UPDATE`** for reservation concurrency Ã¢â‚¬â€ prevents double-selling.
- **Shared service layer** so portal and MCP enforce identical logic and permissions.
- **HTTP/SSE MCP transport** (not stdio) so the server is remotely hostable over live data.

## What Didn''t Work / Lessons
- Postgres in Docker only applies credentials on first volume init Ã¢â‚¬â€ stale volumes cause auth failures; `docker compose down -v` resets them.
- A leftover service squatting on a host port (5434) silently intercepts connections; moved the DB mapping to 5440.
- PowerShell here-strings/redirection inject a BOM that corrupts `.env`/YAML; write config with .NET `WriteAllText` + BOM-less UTF-8.