# InventoryLive-MCP

**Real-time real estate inventory portal + MCP server — two interfaces, one live source of truth.**

Property developers'' in-house agents lack live shared visibility of unit inventory, so two agents can sell the same unit and deals collapse at closing. InventoryLive solves the shared-state problem: one Postgres source of truth, a real-time portal (WebSockets) where every agent sees availability change instantly, and an MCP server exposing the *same* live data — with the *same* access control — as AI-callable tools.

> All inventory is **synthetic** (generated Pakistani housing-society data). No real developer data.

## Architecture
One database, two doors (portal + MCP server) over a shared service layer. _(Diagram added Phase 8.)_

## Tech Stack
FastAPI · WebSockets · PostgreSQL · SQLAlchemy · React · Python MCP (FastMCP) · Docker

## Status
- [x] Phase 1 — Data model, synthetic seed, read-only API
- [ ] Phase 2 — Auth + RBAC
- [ ] Phase 3 — Reservations + concurrency
- [ ] Phase 4 — Real-time WebSocket push
- [ ] Phase 5 — React portal
- [ ] Phase 6 — Deploy
- [ ] Phase 7 — MCP server
- [ ] Phase 8 — Docs + writeup

## Technical Decisions
- **Optimistic locking (`version` column) + `SELECT FOR UPDATE`** for reservation concurrency — prevents double-selling.
- **Shared service layer** so portal and MCP enforce identical logic and permissions.
- **HTTP/SSE MCP transport** (not stdio) so the server is remotely hostable over live data.

## What Didn''t Work / Lessons
- Postgres in Docker only applies credentials on first volume init — stale volumes cause auth failures; `docker compose down -v` resets them.
- A leftover service squatting on a host port (5434) silently intercepts connections; moved the DB mapping to 5440.
- PowerShell here-strings/redirection inject a BOM that corrupts `.env`/YAML; write config with .NET `WriteAllText` + BOM-less UTF-8.