import os
import json
from flask import Flask, render_template, request, session
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a random string for production

# Load tarot cards
with open('card_data.json', 'r', encoding='utf-8') as f:
    tarot_cards = json.load(f)

@app.route('/')
def index():
    session.setdefault("history", [])
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.form['msg']
    history = session.get("history", [])
    # Add user message to history
    history.append({"role": "user", "content": user_msg})

    # Prepare OpenAI prompt with history
    system_prompt = (
        "You are a warm, friendly tarot reader for chat. "
        "If the user's message is a NEW, stand-alone question, pull a tarot card and give a reading. "
        "If the message is a FOLLOW-UP or asking for more steps, tips, or clarification, do NOT pull a new card, just elaborate helpfully."
        "Always end with a practical, helpful action. "
        "Use simple English, Hinglish, or Hindi as the user prefers. Group sentences like chat, not big paragraphs."
    )
    messages = [{"role": "system", "content": system_prompt}] + history
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    bot_reply = response.choices[0].message.content.strip()
    # Add bot reply to history
    history.append({"role": "assistant", "content": bot_reply})
    session["history"] = history
    return bot_reply

if __name__ == '__main__':
    app.run(debug=True)
