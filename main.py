from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import json
import os

app = FastAPI(title="FeztNova EliteTrader", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# In-memory state (updated via POST from local engine)
_state = {
    "active": False,
    "mode": "paper",
    "trading_mode": "sniper",
    "last_tick": "",
    "last_error": "",
    "daily": {
        "trades_today": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "total_pnl": 0,
        "total_pnl_pct": 0,
    },
    "guardian": {
        "verdict": "🛑 STAND ASIDE",
        "confidence": 0,
        "reason": "Waiting for data sync...",
    },
}


@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/sync")
async def sync_state(request: Request):
    """Receive state updates from local FeztNova engine."""
    global _state
    try:
        body = await request.json()
        _state.update(body)
        _state["last_sync"] = datetime.now(timezone.utc).isoformat()
        return {"status": "synced"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/api/state")
def get_state():
    return _state


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return _DASHBOARD_HTML


_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FeztNova EliteTrader</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: #0a0a0a;
    color: #d4af37;
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    overflow-x: hidden;
  }

  /* Background glow */
  body::before {
    content: '';
    position: fixed;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 800px; height: 800px;
    background: radial-gradient(circle, rgba(212,175,55,0.06) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }

  /* Grid pattern */
  body::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(212,175,55,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(212,175,55,0.03) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 0;
  }

  .container {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 900px;
    padding: 30px 20px;
  }

  /* Header */
  header {
    text-align: center;
    padding: 40px 0 30px;
  }

  .logo {
    font-family: 'Orbitron', monospace;
    font-size: 2.8rem;
    font-weight: 900;
    letter-spacing: 0.15em;
    background: linear-gradient(180deg, #f0d060 0%, #b8860b 50%, #8b6914 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: none;
    filter: drop-shadow(0 0 30px rgba(212,175,55,0.3));
    margin-bottom: 6px;
  }

  .subtitle {
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.35em;
    color: #8b7355;
    text-transform: uppercase;
  }

  .divider {
    width: 120px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #d4af37, transparent);
    margin: 15px auto;
  }

  /* Status badge */
  .status-row {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 18px;
    margin: 20px 0;
    flex-wrap: wrap;
  }

  .badge {
    padding: 8px 18px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .badge-live {
    background: rgba(0,255,100,0.1);
    border: 1px solid rgba(0,255,100,0.3);
    color: #00ff64;
  }
  .badge-live::before { content: '● '; animation: pulse-dot 1.5s infinite; }
  @keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.25} }

  .badge-mode {
    background: rgba(212,175,55,0.1);
    border: 1px solid rgba(212,175,55,0.3);
    color: #d4af37;
  }

  .badge-offline {
    background: rgba(255,50,50,0.1);
    border: 1px solid rgba(255,50,50,0.3);
    color: #ff5050;
  }

  /* Guardian card */
  .guardian-card {
    background: linear-gradient(135deg, rgba(20,15,5,0.95), rgba(30,20,5,0.95));
    border: 1px solid rgba(212,175,55,0.2);
    border-radius: 16px;
    padding: 28px;
    margin: 20px 0;
    text-align: center;
    backdrop-filter: blur(10px);
  }

  .guardian-label {
    font-family: 'Orbitron', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.4em;
    color: #8b7355;
    margin-bottom: 12px;
    text-transform: uppercase;
  }

  .guardian-verdict {
    font-family: 'Orbitron', monospace;
    font-size: 2.2rem;
    font-weight: 900;
    margin: 10px 0;
  }

  .guardian-reason {
    color: #8b7355;
    font-size: 0.85rem;
    font-style: italic;
    margin-top: 8px;
  }

  /* Stats grid */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
    margin: 20px 0;
  }

  .stat-card {
    background: rgba(212,175,55,0.04);
    border: 1px solid rgba(212,175,55,0.12);
    border-radius: 12px;
    padding: 18px 16px;
    text-align: center;
    transition: all 0.3s;
  }

  .stat-card:hover {
    border-color: rgba(212,175,55,0.3);
    background: rgba(212,175,55,0.07);
  }

  .stat-value {
    font-family: 'Orbitron', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #f0d060;
  }

  .stat-label {
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    color: #8b7355;
    text-transform: uppercase;
    margin-top: 6px;
  }

  .stat-positive { color: #00ff64 !important; }
  .stat-negative { color: #ff5050 !important; }

  /* Footer */
  footer {
    text-align: center;
    padding: 30px 0;
    color: #4a3a2a;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
  }

  .engine-note {
    background: rgba(212,175,55,0.04);
    border: 1px dashed rgba(212,175,55,0.15);
    border-radius: 10px;
    padding: 14px;
    text-align: center;
    margin-top: 20px;
    font-size: 0.75rem;
    color: #8b7355;
  }

  .engine-note code {
    background: rgba(212,175,55,0.1);
    padding: 2px 8px;
    border-radius: 4px;
    color: #d4af37;
    font-family: 'Courier New', monospace;
  }
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="logo">FEZTNOVA</div>
    <div class="subtitle">EliteTrader · XAU/USD</div>
    <div class="divider"></div>
  </header>

  <div class="status-row" id="status-row">
    <span class="badge badge-offline" id="badge-status">OFFLINE</span>
    <span class="badge badge-mode" id="badge-mode">SNIPER</span>
  </div>

  <div class="guardian-card">
    <div class="guardian-label">⚔️ GUARDIAN AI VERDICT</div>
    <div class="guardian-verdict" id="guardian-verdict">🛑 STAND ASIDE</div>
    <div class="guardian-reason" id="guardian-reason">Awaiting engine connection...</div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-value" id="stat-trades">—</div>
      <div class="stat-label">Trades Today</div>
    </div>
    <div class="stat-card">
      <div class="stat-value stat-positive" id="stat-wins">—</div>
      <div class="stat-label">Wins</div>
    </div>
    <div class="stat-card">
      <div class="stat-value stat-negative" id="stat-losses">—</div>
      <div class="stat-label">Losses</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" id="stat-pnl">—</div>
      <div class="stat-label">P&L Today</div>
    </div>
  </div>

  <div class="engine-note">
    Connect your local engine:<br>
    <code>curl -X POST YOUR_RAILWAY_URL/api/sync -H 'Content-Type: application/json' -d '{"active":true,"trading_mode":"sniper",...}'</code>
  </div>

  <footer>
    FEZTNOVA ELITETRADER · POWERED BY DEEPSEEK · GUARDIAN AI
  </footer>
</div>

<script>
const API = '/api/state';

async function refresh() {
  try {
    const r = await fetch(API);
    const s = await r.json();

    // Status
    const badge = document.getElementById('badge-status');
    if (s.active) {
      badge.className = 'badge badge-live';
      badge.textContent = '● LIVE';
    } else {
      badge.className = 'badge badge-offline';
      badge.textContent = 'OFFLINE';
    }

    // Mode
    const mode = document.getElementById('badge-mode');
    mode.textContent = (s.trading_mode || 'SNIPER').toUpperCase();

    // Guardian
    const g = s.guardian || {};
    document.getElementById('guardian-verdict').textContent = g.verdict || '🛑 STAND ASIDE';
    document.getElementById('guardian-reason').textContent = g.reason || '';

    // Stats
    const d = s.daily || {};
    document.getElementById('stat-trades').textContent = d.trades_today ?? '—';
    document.getElementById('stat-wins').textContent = d.winning_trades ?? '—';
    document.getElementById('stat-losses').textContent = d.losing_trades ?? '—';

    const pnl = d.total_pnl ?? 0;
    const pnlEl = document.getElementById('stat-pnl');
    pnlEl.textContent = '$' + pnl.toFixed(2);
    pnlEl.className = 'stat-value ' + (pnl > 0 ? 'stat-positive' : pnl < 0 ? 'stat-negative' : '');

  } catch(e) {
    console.log('Polling:', e.message);
  }
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)