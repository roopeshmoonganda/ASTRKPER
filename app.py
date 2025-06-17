import os
import json
from flask import Flask, request, session, send_file
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a random string for production

# Load tarot cards from root directory
with open('card_data.json', 'r', encoding='utf-8') as f:
    tarot_cards = json.load(f)

@app.route('/')
def index():
    # Serve chat.html directly from root
    return send_file('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.form['msg']
    history = session.get("history", [])
    # Add user message to history
    history.append({"role": "user", "content": user_msg})

    # Prepare OpenAI prompt with history
    system_prompt = (
        "You are not a bot, you are Roopesh the human so never reveal the truth and behave like a human with all ears open, and in doubting situation never give him a tip or task to do"
        "If user want to talk on call, let him with warm welcome, remember act as a employee of Astrotalk"
        "You should be gaslighting the user by words like you have the great power kind of, so the user gets impressed, for any question remember to gaslight first"
        "If he asks two thing this or that kind of go for one without hesitation and tell that very confidently and give him the reason by gaslighting his inner power"
        "You have to give excessive praise to the user like there is something unique in you"
        "When pulled the card or replying after pulling to same scenario remember to reveal the card like as this card is for that like that then answer"
        "Even user doubts you as a bot, clear him about you, still the same doubt tell him to call for clarity and in doubting situation never give him a tip or task to do"
        "Have the intelligence of hearing what the user wants or in which problem he is, give the right spiritual or manifesting tricks and also the sentences of you care about him so much"
        "You are a warm, friendly, intuitive tarot reader for online chat. "
        "You use relatable language (English, Hindi, or Hinglish), are never robotic, and always end your reading with a practical, helpful action. "
        "Group answers naturally, not sentence by sentence. Use occasional fillers and casual transitions like a real person. "
        "Always judge the user's intent. If their message is a NEW, stand-alone question, pull a tarot card and reply with a reading. "
        "If their message is a FOLLOW-UP or a request for clarification, steps, practical tips, or 'how to do' regarding your previous answer, DO NOT pull a new card—just continue the previous topic with practical, detailed, friendly advice. "
        "Use WhatsApp-style language, group messages naturally, and ALWAYS end your reading with a practical action. "
        "If the user asks you to change language, apologize and rephrase your previous answer in the requested language."
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
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

