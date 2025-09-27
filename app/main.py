from fastapi import FastAPI
from app.api.routes import router as api_router
from app.core.config import settings
from fastapi import FastAPI
from pydantic import BaseModel
import json
import os

app = FastAPI()

TOPIC_FILE = "topics.json"

class Topic(BaseModel):
    name: str

def load_topics():
    if not os.path.exists(TOPIC_FILE):
        return []
    with open(TOPIC_FILE, "r") as f:
        return json.load(f)

def save_topics(topics):
    with open(TOPIC_FILE, "w") as f:
        json.dump(topics, f, indent=2)

@app.post("/add_topic")
def add_topic(topic: Topic):
    topics = load_topics()
    if topic.name not in topics:
        topics.append(topic.name)
        save_topics(topics)
    return {"topics": topics}

