from fastapi import FastAPI, Form, HTTPException
from db import init_db, get_session
from models import Memory
from summarizer import hf_summarize
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from sqlmodel import select

app = FastAPI(title="MyMiniBrain Backend")

init_db()

def add_memory(type_, content, source=None):
    with get_session() as session:
        mem = Memory(type=type_, content=content, source=source)
        session.add(mem)
        session.commit()
        session.refresh(mem)
        return mem

@app.post("/learn")
def learn(text: str = Form(...), source: str = Form("user")):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty text not allowed")
    mem = add_memory("user", text.strip(), source)
    return {"status": "ok", "id": mem.id, "added_at": mem.added_at.isoformat()}

@app.get("/memory")
def memory(limit: int = 200):
    with get_session() as session:
        items = session.exec(select(Memory).order_by(Memory.added_at.desc()).limit(limit)).all()
    return {
        "count": len(items),
        "items": [
            {
                "id": m.id,
                "type": m.type,
                "content": m.content,
                "source": m.source,
                "added_at": m.added_at.isoformat()
            } for m in items
        ]
    }

@app.get("/daily-report")
def daily_report(days: int = 1):
    since = datetime.utcnow() - timedelta(days=days)
    with get_session() as session:
        items = session.exec(select(Memory).where(Memory.added_at >= since)).all()

    internet_text = " ".join([m.content for m in items if m.type == "internet"])[:4000]
    summary = hf_summarize(internet_text) if internet_text else "No internet learning today."

    user_items = [
        {"id": m.id, "content": m.content, "at": m.added_at.isoformat()}
        for m in items if m.type == "user"
    ]

    return {
        "summary": summary,
        "user_teachings": user_items,
        "total_items": len(items)
    }

@app.get("/")
def home():
    return {"message": "MyMiniBrain backend running!"}

# ---------------- DAILY FETCHER ----------------

def fetch_daily_sources():
    # Wikipedia Topics
    topics = ["Artificial_intelligence", "Bitcoin", "Human_brain"]
    for t in topics:
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{t}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                summary = r.json().get("extract", "")
                short = hf_summarize(summary)
                add_memory("internet", short, source=f"wiki:{t}")
        except:
            pass

    # Crypto from CoinGecko (Top coins)
    try:
        cg = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 3, "page": 1},
            timeout=10
        )
        if cg.status_code == 200:
            arr = cg.json()
            text = "Crypto update: " + ", ".join([f"{c['id']} = ${c['current_price']}" for c in arr])
            add_memory("internet", text, source="coingecko")
    except:
        pass

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_daily_sources, 'interval', hours=24, next_run_time=datetime.utcnow())
scheduler.start()