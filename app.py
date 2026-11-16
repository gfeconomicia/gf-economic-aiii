import os, sqlite3
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import requests

load_dotenv()
app = Flask(__name__)
DB_PATH = os.getenv("DATABASE_PATH", "gf_economic_ai.db")
CALENDAR_URL = "https://showmytrades.com/api/public/calendar/v1"
PAIRS = ["EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD", "EUR/JPY", "AUD/CAD"]
CURRENCIES = "USD,EUR,GBP,JPY,AUD,CAD,CHF,NZD,CNY"

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            event TEXT NOT NULL,
            currency TEXT,
            pair TEXT,
            direction TEXT NOT NULL,
            horizon TEXT NOT NULL,
            rationale TEXT,
            outcome TEXT DEFAULT 'PENDENTE',
            source TEXT
        )""")

def get_calendar():
    try:
        response = requests.get(
            CALENDAR_URL,
            params={"currency": CURRENCIES, "impact": "high,medium", "days": 7, "format": "json"},
            headers={"Accept": "application/json"},
            timeout=15
        )
        response.raise_for_status()
        payload = response.json()
        raw_events = payload.get("events", [])
        events = []
        for item in raw_events:
            events.append({
                "date": item.get("time", ""),
                "currency": item.get("currency", ""),
                "country": item.get("currency", ""),
                "event": item.get("title", ""),
                "actual": item.get("actual", ""),
                "forecast": item.get("forecast", ""),
                "previous": item.get("previous", ""),
                "impact": item.get("impact", ""),
                "status": item.get("status", ""),
                "confidence": item.get("confidence", ""),
                "source": "ShowMyTrades"
            })
        return events, payload.get("server_time_iso"), None
    except requests.RequestException as exc:
        return [], None, f"Falha ao consultar o calendário econômico: {exc}"
    except (ValueError, TypeError, AttributeError) as exc:
        return [], None, f"Resposta inesperada do calendário econômico: {exc}"

def event_assessment(event):
    actual, forecast = event.get("actual"), event.get("forecast")
    if actual in (None, "", "-") or forecast in (None, "", "-"):
        return "AGUARDAR", "Sem resultado e consenso comparáveis; não há base para inferir direção."
    return "REVISÃO NECESSÁRIA", (
        "Resultado recebido. A direção depende do tipo de indicador, do impacto sobre a política "
        "monetária, de revisões e da reação observada no preço. Não é um sinal automático."
    )

@app.route("/")
def dashboard():
    events, server_time, warning = get_calendar()
    for event in events:
        event["direction"], event["rationale"] = event_assessment(event)
    with db() as conn:
        recent = conn.execute("SELECT * FROM analyses ORDER BY id DESC LIMIT 15").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        wins = conn.execute("SELECT COUNT(*) FROM analyses WHERE outcome='WIN'").fetchone()[0]
        losses = conn.execute("SELECT COUNT(*) FROM analyses WHERE outcome='LOSS'").fetchone()[0]
    decided = wins + losses
    win_rate = round((wins / decided) * 100, 1) if decided else None
    return render_template("index.html", events=events[:80], warning=warning,
        pairs=PAIRS, recent=recent, total=total, wins=wins, losses=losses,
        win_rate=win_rate, updated=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        server_time=server_time)

@app.post("/api/analysis")
def save_analysis():
    payload = request.get_json(silent=True) or {}
    if any(not payload.get(k) for k in ["event", "direction", "horizon"]):
        return jsonify(error="Informe evento, direção e horizonte."), 400
    if payload["direction"] not in ["COMPRA", "VENDA", "AGUARDAR"]:
        return jsonify(error="Direção inválida."), 400
    if payload["horizon"] not in ["2 min", "5 min", "15 min"]:
        return jsonify(error="Horizonte inválido."), 400
    with db() as conn:
        cur = conn.execute("""INSERT INTO analyses
            (created_at,event,currency,pair,direction,horizon,rationale,source)
            VALUES (?,?,?,?,?,?,?,?)""",
            (datetime.now(timezone.utc).isoformat(), payload["event"],
             payload.get("currency"), payload.get("pair"), payload["direction"],
             payload["horizon"], payload.get("rationale",""), payload.get("source","manual")))
    return jsonify(id=cur.lastrowid, status="registrado")

@app.post("/api/outcome/<int:analysis_id>")
def update_outcome(analysis_id):
    payload = request.get_json(silent=True) or {}
    outcome = payload.get("outcome")
    if outcome not in ["WIN", "LOSS", "EMPATE", "CANCELADO"]:
        return jsonify(error="Resultado inválido."), 400
    with db() as conn:
        cur = conn.execute("UPDATE analyses SET outcome=? WHERE id=?", (outcome, analysis_id))
        if cur.rowcount == 0:
            return jsonify(error="Análise não encontrada."), 404
    return jsonify(status="atualizado")

@app.get("/health")
def health():
    return jsonify(status="ok", app="GF ECONOMIC AI", calendar_source="ShowMyTrades")

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","5000")))
