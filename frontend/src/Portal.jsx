import { useEffect, useState, useCallback } from "react";
import { fetchUnits, reserveUnit } from "./api";
import { useLiveUpdates } from "./useLiveUpdates";
import AskAI from "./AskAI";

function formatPKR(n) {
  const num = Number(n);
  if (num >= 1e7) return `${(num / 1e7).toFixed(2)} Cr`;
  if (num >= 1e5) return `${(num / 1e5).toFixed(1)} Lac`;
  return num.toLocaleString();
}

export default function Portal({ token, role, email, onLogout }) {
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [flash, setFlash] = useState(null);

  useEffect(() => {
    fetchUnits(token)
      .then(setUnits)
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, [token]);

  const handleLiveEvent = useCallback((evt) => {
    setUnits((prev) =>
      prev.map((u) =>
        u.id === evt.unit_id
          ? { ...u, status: evt.status, version: evt.version }
          : u
      )
    );
    setFlash(evt.unit_id);
    setTimeout(() => setFlash((f) => (f === evt.unit_id ? null : f)), 1200);
  }, []);

  useLiveUpdates(token, handleLiveEvent);

  async function handleReserve(unitId) {
    try {
      await reserveUnit(token, unitId);
    } catch (e) {
      alert(e.message);
    }
  }

  const counts = units.reduce(
    (acc, u) => ((acc[u.status] = (acc[u.status] || 0) + 1), acc),
    {}
  );

  return (
    <div className="portal">
      <header>
        <div>
          <strong>InventoryLive</strong>
          <span className="role-badge">{role}</span>
        </div>
        <div className="header-right">
          <span className="who">{email}</span>
          <button className="logout" onClick={onLogout}>
            Log out
          </button>
        </div>
      </header>

      <div className="summary">
        <span className="pill available">{counts.available || 0} available</span>
        <span className="pill reserved">{counts.reserved || 0} reserved</span>
        <span className="pill sold">{counts.sold || 0} sold</span>
        <span className="live-dot">live</span>
      </div>

      <AskAI token={token} />

      {loading ? (
        <p className="loading">Loading inventory...</p>
      ) : (
        <div className="grid">
          {units.map((u) => (
            <div
              key={u.id}
              className={`unit ${u.status} ${flash === u.id ? "flash" : ""}`}
            >
              <div className="unit-num">{u.unit_number}</div>
              <div className="unit-meta">
                {Number(u.size_marla)} marla - floor {u.floor}
              </div>
              <div className="unit-price">PKR {formatPKR(u.price_pkr)}</div>
              <div className="unit-status">{u.status}</div>
              {u.status === "available" && (
                <button onClick={() => handleReserve(u.id)}>Reserve</button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}