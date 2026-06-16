"""Groq-powered natural-language query over live inventory.

Local tool calling: Groq returns structured tool-call requests, we execute
them against the SAME service layer (RBAC-scoped), feed results back, and
return the model''s final answer.
"""
import json
from groq import Groq
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import models as m
from app.services import inventory as inv_svc

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "List available units in the user''s permitted scope. "
                           "Optionally filter by max price (PKR) and minimum size (marla).",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_price_pkr": {"type": "number", "description": "Max price in PKR"},
                    "min_size_marla": {"type": "number", "description": "Min size in marla"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inventory_summary",
            "description": "Counts of available/reserved/sold units for a project "
                           "(matched by partial name) within the user''s scope.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name or part of it"},
                },
            },
        },
    },
]


def _tool_check_availability(db, agent, max_price_pkr=None, min_size_marla=None):
    units = inv_svc.list_units(db, agent, status="available")
    out = []
    for u in units:
        if max_price_pkr is not None and float(u.price_pkr) > max_price_pkr:
            continue
        if min_size_marla is not None and float(u.size_marla) < min_size_marla:
            continue
        block = db.query(m.Block).filter(m.Block.id == u.block_id).first()
        proj = db.query(m.Project).filter(m.Project.id == block.project_id).first()
        out.append({
            "unit_id": u.id, "unit_number": u.unit_number, "project": proj.name,
            "block": block.name, "size_marla": float(u.size_marla),
            "floor": u.floor, "price_pkr": float(u.price_pkr),
        })
    return out[:25]


def _tool_inventory_summary(db, agent, project=None):
    q = db.query(m.Project)
    if project:
        q = q.filter(m.Project.name.ilike(f"%{project}%"))
    proj = q.first()
    if proj is None:
        return {"error": f"No project matching ''{project}''"}
    counts = inv_svc.inventory_summary(db, agent, proj.id)
    return {"project": proj.name, **counts}


def _dispatch(db, agent, name, args):
    args = args if isinstance(args, dict) else {}
    try:
        if name == "check_availability":
            return _tool_check_availability(db, agent, **args)
        if name == "inventory_summary":
            return _tool_inventory_summary(db, agent, **args)
        return {"error": f"Unknown tool {name}"}
    except Exception as e:  # noqa: BLE001
        return {"error": f"Tool {name} failed: {e}"}


def _clean(answer: str, question: str) -> str:
    """Strip the reservation disclaimer unless the user actually asked to reserve."""
    if "reserv" not in question.lower() and "book" not in question.lower():
        for frag in ["Reservations must be made in the portal.",
                     " Reservations must be made in the portal"]:
            answer = answer.replace(frag, "").strip()
    return answer


def ask(db: Session, agent: m.Agent, question: str) -> dict:
    if not settings.groq_api_key:
        return {"answer": "AI is not configured (no GROQ_API_KEY).", "tools_used": []}

    # max_retries=1: don''t let the SDK''s long backoff (14s/40s) hang the request.
    client = Groq(api_key=settings.groq_api_key, timeout=20.0, max_retries=1)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a real-estate inventory assistant. Use the provided tools "
                "to answer from live data scoped to this user. Call each tool AT MOST "
                "ONCE per question. After receiving tool results, ALWAYS write a final "
                "text answer; do not call more tools. You can only READ inventory ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â you "
                "cannot reserve, book, or modify units; if asked to, say reservations "
                "must be made in the portal. Prices are PKR; format as "
                "Lac/Crore (1 Crore = 10,000,000; 1 Lac = 100,000). Be concise."
            ),
        },
        {"role": "user", "content": question},
    ]

    tools_used = []
    try:
        for round_i in range(3):
            use_tools = round_i < 2
            kwargs = {
                "model": settings.groq_model,
                "messages": messages,
                "temperature": 0.2,
            }
            if use_tools:
                kwargs["tools"] = TOOLS
                kwargs["tool_choice"] = "auto"

            resp = client.chat.completions.create(**kwargs)
            msg = resp.choices[0].message

            if not msg.tool_calls:
                return {"answer": _clean(msg.content or "", question),
                        "tools_used": tools_used}

            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except (json.JSONDecodeError, TypeError):
                    args = {}
                if not isinstance(args, dict):
                    args = {}
                result = _dispatch(db, agent, tc.function.name, args)
                tools_used.append({"tool": tc.function.name, "args": args})
                messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str),
                })

        resp = client.chat.completions.create(
            model=settings.groq_model, messages=messages, temperature=0.2,
        )
        return {"answer": _clean(resp.choices[0].message.content or "", question),
                "tools_used": tools_used}
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if "tool_use_failed" in msg or "was not in request.tools" in msg:
            return {
                "answer": "I can only look up inventory (availability and summaries). "
                          "Reservations must be made directly in the portal.",
                "tools_used": tools_used,
            }
        if "429" in msg or "rate" in msg.lower() or "too many" in msg.lower():
            return {
                "answer": "The AI assistant is busy right now (free-tier rate limit). "
                          "Please wait a few seconds and try again.",
                "tools_used": tools_used,
            }
        return {"answer": f"The AI request failed: {msg}", "tools_used": tools_used}


if __name__ == "__main__":
    pass