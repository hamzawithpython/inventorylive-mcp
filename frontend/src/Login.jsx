import { useState } from "react";
import { login } from "./api";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("agent_a@demo.com");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit() {
    setError("");
    setBusy(true);
    try {
      const { access_token, role } = await login(email, password);
      onLogin(access_token, role, email);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <h1>InventoryLive</h1>
        <p className="subtitle">Real-time inventory portal</p>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        />
        {error && <div className="error">{error}</div>}
        <button onClick={handleSubmit} disabled={busy}>
          {busy ? "Signing in..." : "Sign in"}
        </button>
        <div className="hint">
          Demo: agent_a / agent_b / admin @demo.com - demo1234
        </div>
      </div>
    </div>
  );
}