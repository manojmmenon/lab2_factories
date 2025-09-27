# main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import os, json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI(title="Lab2 Factories - Topics & Email Similarity Classifier")

TOPIC_FILE = "topics.json"
EMAIL_FILE = "emails.json"

# ----------------------
# Utilities for JSON files
# ----------------------
def load_json_file(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json_file(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ----------------------
# Data models
# ----------------------
class TopicModel(BaseModel):
    name: str

class EmailModel(BaseModel):
    text: str
    ground_truth: Optional[str] = None

class ClassifyRequest(BaseModel):
    text: str

# ----------------------
# Endpoints
# ----------------------

@app.get("/topics", response_model=List[str])
def get_topics():
    return load_json_file(TOPIC_FILE)

@app.post("/add_topic")
def add_topic(topic: TopicModel):
    topics = load_json_file(TOPIC_FILE)
    if topic.name in topics:
        return {"message": "topic already exists", "topics": topics}
    topics.append(topic.name)
    save_json_file(TOPIC_FILE, topics)
    return {"message": "topic added", "topics": topics}

@app.get("/emails")
def get_emails():
    return load_json_file(EMAIL_FILE)

@app.post("/add_email")
def add_email(email: EmailModel):
    emails = load_json_file(EMAIL_FILE)
    emails.append(email.dict())
    save_json_file(EMAIL_FILE, emails)
    return {"message": "email added", "emails_count": len(emails)}

@app.post("/classify")
def classify(req: ClassifyRequest, method: str = Query("topics", regex="^(topics|similarity)$")):
    """
    method:
      - topics: simple keyword match with stored topics
      - similarity: find most similar stored email and return its ground_truth
    """
    text = req.text
    if method == "topics":
        # Simple topic matching: if topic name appears in text -> return it
        topics = load_json_file(TOPIC_FILE)
        text_lower = text.lower()
        for t in topics:
            if t.lower() in text_lower:
                return {"method": "topics", "classification": t}
        return {"method": "topics", "classification": "unknown"}

    # similarity branch
    emails = load_json_file(EMAIL_FILE)
    if not emails:
        raise HTTPException(status_code=400, detail="No stored emails available for similarity.")
    stored_texts = [e.get("text", "") for e in emails]
    # vectorize
    vectorizer = TfidfVectorizer()
    try:
        vectors = vectorizer.fit_transform(stored_texts + [text])
    except ValueError:
        # when texts are empty or invalid
        raise HTTPException(status_code=400, detail="Unable to vectorize texts.")
    query_vec = vectors[-1]
    stored_vecs = vectors[:-1]
    sims = cosine_similarity(query_vec, stored_vecs).flatten()
    best_idx = int(sims.argmax())
    best_score = float(sims[best_idx])
    best_email = emails[best_idx]
    classification = best_email.get("ground_truth", "unknown")
    return {
        "method": "similarity",
        "classification": classification,
        "score": best_score,
        "most_similar": best_email
    }

