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
    tech = request.form.get("technology", "General")
    diff = request.form.get("difficulty", "Medium")
    
    token = schedule_interview(name, email, time, tech, diff)
    base_url = "http://localhost:8000"
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
    
    now = datetime.now()
    interview_time = datetime.strptime(interview['interview_time'], "%Y-%m-%dT%H:%M")
    
    slot_start = interview_time - timedelta(minutes=5)
    slot_end = interview_time + timedelta(minutes=30)
    
    if now < slot_start:
        return f"<h1>Too early!</h1><p>Your interview starts at {interview['interview_time']}. Please return then.</p>", 403
    if now > slot_end:
        return f"<h1>Interview Expired</h1><p>The interview slot for {interview['interview_time']} has expired.</p>", 403

    return render_template("interview.html", 
                         name=interview['candidate_name'], 
                         token=token, 
                         technology=interview['technology'], 
                         difficulty=interview['difficulty'])

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("prompt")
    context = data.get("context", [])
    elapsed_minutes = data.get("elapsed_minutes", 0)
    is_initial = data.get("is_initial", False)
    technology = data.get("technology", "General")
    difficulty = data.get("difficulty", "Medium")
    
    # Guidelines for the AI
    base_instruction = (
        f"You are a professional AI Technical Recruiter. You are conducting an interview for the technology: {technology} "
        f"at a {difficulty} difficulty level. "
        "Ask insightful technical and behavioral questions one at a time. Be polite, professional, and concise. "
    )

    if elapsed_minutes < 10:
        timing_instruction = (
            f"Context: Only {elapsed_minutes:.1f} minutes have passed. The interview MUST last at least 10 minutes. "
            f"Continue asking {difficulty}-level technical questions about {technology} to evaluate the candidate."
        )
    else:
        timing_instruction = (
            f"Context: {elapsed_minutes:.1f} minutes have passed. You may now conclude the interview if you have enough information. "
            "If you decide to end, you MUST start your response with exactly '[CONCLUDE]' and say a warm thank you."
        )

    if is_initial:
        full_prompt = (
            f"{base_instruction} Start the interview now. Introduce yourself and ask the candidate to introduce themselves. "
        )
    else:
        full_prompt = (
            f"{base_instruction} {timing_instruction} The candidate just said: \"{prompt}\" "
            "Respond and ask the next insightful question."
        )
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "context": context
        })
        return response.json()
    except Exception as e:
        print(f"Ollama Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
