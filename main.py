from fastapi import FastAPI, Form
from datetime import datetime, timedelta
from db import init_db, get_session
from models import Memory
from summarizer import hf_summarize
from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import select
import requests

app = FastAPI()

init_db()

def add_memory(type_, content, source=None):
    with get_session() as db:
        item = Memory(type=type_, content=content, source=source)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

@app.get("/")
def home():
    return {"message": "MyMiniBrain backend running!"}

@app.post("/learn")
async def learn(text: str = Form(...), source: str = Form("user")):
    m = add_memory("user", text, source)
    return {"status": "ok", "id": m.id}

@app.get("/memory")
def all_memory():
    with get_session() as db:
        items = db.exec(select(Memory).order_by(Memory.added_at.desc())).all()
    return items

@app.get("/daily-report")
def report():
    with get_session() as db:
        items = db.exec(select(Memory).where(Memory.type=="internet")).all()

    text = " ".join(i.content for i in items)
    summary = hf_summarize(text)
    return {"summary": summary, "count": len(items)}

# DAILY INTERNET LEARNING
def fetch_daily():
    # Wikipedia
    topics = ["Artificial_intelligence", "Bitcoin", "Stock_market"]
    for t in topics:
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{t}"
            res = requests.get(url).json()
            add_memory("internet", res.get("extract",""), f"wiki:{t}")
        except:
            pass

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_daily, "interval", hours=24)
scheduler.start()