from flask import Flask, render_template, request, jsonify
import requests
import os
from datetime import datetime, timedelta
from database import init_db, schedule_interview, get_interview_by_token
from email_utils import send_interview_email
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
init_db()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

@app.route("/")
def dashboard():
    return render_template("index.html")

@app.route("/schedule", methods=["POST"])
def schedule():
    name = request.form.get("name")
    email = request.form.get("email")
    time = request.form.get("time")
    
    # time format: YYYY-MM-DDTHH:MM
    token = schedule_interview(name, email, time)
    base_url = "http://localhost:8000" # Change if deploying
    link = f"{base_url}/interview?token={token}"
    
    success = send_interview_email(email, name, time, link)
    
    return jsonify({"message": "Interview scheduled", "link": link, "email_sent": success})

@app.route("/interview")
def interview_room():
    token = request.args.get("token")
    if not token:
        return "Missing token", 400
        
    interview = get_interview_by_token(token)
    if not interview:
        return "Interview not found", 404
    
    # Time window check
    now = datetime.now()
    interview_time = datetime.strptime(interview['interview_time'], "%Y-%m-%dT%H:%M")
    
    # Allowed to join 5 mins before and 30 mins after
    slot_start = interview_time - timedelta(minutes=5)
    slot_end = interview_time + timedelta(minutes=30)
    
    if now < slot_start:
        return f"<h1>Too early!</h1><p>Your interview starts at {interview['interview_time']}. Please return then.</p>", 403
    if now > slot_end:
        return f"<h1>Interview Expired</h1><p>The interview slot for {interview['interview_time']} has expired.</p>", 403

    return render_template("interview.html", name=interview['candidate_name'], token=token)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("prompt")
    context = data.get("context", [])
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "context": context
        })
        return response.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
