import { useState, useEffect } from "react";
import { askAI } from "./api";

const EXAMPLES = [
  "What 5-marla units are available under 3 crore?",
  "Give me a summary of Bahria Town Phase 8",
  "Show available 10-marla units",
];

const COOLDOWN_SECONDS = 6;

export default function AskAI({ token }) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [tools, setTools] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [cooldown, setCooldown] = useState(0);

  // Tick the cooldown down each second.
  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const locked = busy || cooldown > 0;

  async function run(q) {
    const query = q ?? question;
    if (!query.trim() || locked) return;
    setBusy(true);
    setError("");
    setAnswer(null);
    setTools([]);
    try {
      const data = await askAI(token, query);
      setAnswer(data.answer);
      setTools(data.tools_used || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
      setCooldown(COOLDOWN_SECONDS); // throttle the next query
    }
  }

  const buttonLabel = busy
    ? "Thinking..."
    : cooldown > 0
    ? `Wait ${cooldown}s`
    : "Ask";

  return (
    <div className="askai">
      <button className="askai-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? "Hide AI Assistant" : "Ask the AI Assistant"}
      </button>

      {open && (
        <div className="askai-panel">
          <p className="askai-hint">
            Ask in plain English. The AI queries live inventory using your
            permissions (powered by Groq + this project''s tools).
          </p>
          <div className="askai-examples">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                className="chip"
                disabled={locked}
                onClick={() => { setQuestion(ex); run(ex); }}
              >
                {ex}
              </button>
            ))}
          </div>
          <div className="askai-input">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. cheapest available unit in Block A"
              onKeyDown={(e) => e.key === "Enter" && run()}
              disabled={locked}
            />
            <button onClick={() => run()} disabled={locked}>
              {buttonLabel}
            </button>
          </div>

          {error && <div className="error">{error}</div>}

          {answer && (
            <div className="askai-answer">
              <div className="answer-text">{answer}</div>
              {tools.length > 0 && (
                <div className="tools-trace">
                  Tools called:{" "}
                  {tools.map((t, i) => (
                    <code key={i}>{t.tool}({JSON.stringify(t.args)})</code>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}