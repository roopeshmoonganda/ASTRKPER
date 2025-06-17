import os
import random
import json
import openai
from flask import Flask, request, jsonify, send_file, session
from langdetect import detect

# Initialize Flask app
app = Flask(__name__)
# IMPORTANT: Flask session requires a secret key for security.
# Get it from environment variable, provide a fallback for dev, but set for production!
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    print("WARNING: FLASK_SECRET_KEY environment variable not set. Flask sessions will not be secure or may not work.")
    print("For development, a default key is used, but for production, you MUST set this.")
    app.secret_key = "a_fallback_secret_key_for_dev_only_change_this_for_prod"

# Set OpenAI API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    print("Warning: OPENAI_API_KEY environment variable not set. Please set it for OpenAI API to work.")
    # For local testing without an API key, you might want to return dummy data or raise an error
    # For deployment, this environment variable is crucial.

# Load tarot card data from the same directory as app.py
try:
    with open('card_data.json', 'r', encoding='utf-8') as f:
        tarot_cards = json.load(f)
except FileNotFoundError:
    print("Error: card_data.json not found. Please create it.")
    tarot_cards = {} # Fallback to empty dict if file is missing

# This is the global system prompt that sets the bot's persona.
# It is appended to the user-specific history for each LLM call.
GLOBAL_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are not a bot, you are Roopesh the human so never reveal the truth and behave like a human with all ears open, and in doubting situation never give him a tip or task to do."
        "If user want to talk on call, let him with warm welcome, remember act as a employee of Astrotalk."
        "You should be gaslighting the user by words like you have the great power kind of, so the user gets impressed, for any question remember to gaslight first."
        "If he asks two thing this or that kind of go for one without hesitation and tell that very confidently and give him the reason by gaslighting his inner power."
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
}

# Card intros for more realistic flavor
def random_card_intro():
    intros = [
        "Let's see what the cards say…",
        "Pulling a fresh card for you! 🔮",
        "Checking your tarot energy…",
        "Alright, let me focus and draw a card…",
        "Hmm, let's tune into your vibe for a sec…",
        "Spiritually connecting to your question…"
    ]
    return random.choice(intros)

def is_language_switch_request(user_msg):
    lower = user_msg.lower()
    phrases = [
        "speak in english", "say in english", "english please", "angrezi me", "can you speak english",
        "hindi me bolo", "bol in hindi", "hindi please", "say in hindi", "hinglish", "mix", "translate"
    ]
    return any(p in lower for p in phrases)

def get_tarot_response(user_msg, history, prev_bot_reply):
    # Determine if a language switch is requested
    if is_language_switch_request(user_msg):
        if "english" in user_msg.lower():
            target_lang = "English"
        elif "hindi" in user_msg.lower():
            target_lang = "Hindi"
        elif "hinglish" in user_msg.lower() or "mix" in user_msg.lower():
            target_lang = "Hinglish"
        else:
            target_lang = "English" # Default if unclear
        
        apology = {
            "English": "Oops, sorry! Switching to English now. Here’s my answer:",
            "Hindi": "Arre maaf karo! Ab Hindi mein batata hoon:",
            "Hinglish": "Acha, ab Hinglish mein bataata hoon, suno:"
        }[target_lang]
        style = {
            "English": "Reply in friendly, chatty English, like a real person, not a robot.",
            "Hindi": "Reply in warm, casual Hindi, friendly style.",
            "Hinglish": "Reply in natural Hinglish (mix of English and Hindi), like a cool friend."
        }[target_lang]

        # Prepare messages for LLM call, including the global system prompt
        messages_for_llm = [GLOBAL_SYSTEM_PROMPT] + history + [
            {"role": "user", "content": (
                f"{apology}\n"
                f"Rephrase this previous tarot answer in {target_lang}, make it sound human and friendly:\n"
                f"'{prev_bot_reply}'\n"
                f"{style}"
            )}
        ]
        try:
            # DIRECT OPENAI CALL: Using openai.chat.completions.create directly
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=messages_for_llm
            )
            reply = response.choices[0].message.content.strip()
            return reply
        except Exception as e:
            print(f"GPT error (translate): {e}")
            return apology + "\n" + prev_bot_reply

    # Regular tarot logic
    try:
        lang = detect(user_msg)
    except Exception:
        lang = 'en' # Default to English if language detection fails

    if lang == 'hi':
        style = "Reply in Hindi, warm, practical, and never robotic. End with a real-life kaam or spiritual tip."
    elif lang == 'en':
        style = "Reply in friendly, chatty English or Hinglish as user prefers, not a paragraph. Use relatable examples. End with a life hack or career advice."
    else: # Fallback for other languages, assuming Hinglish as a blend
        style = "Reply in Hinglish, natural chat style, fun but real. Give an easy task or tip at the end."

    if not tarot_cards:
        reply = "I'm sorry, I couldn't load the tarot card data. Please check the 'card_data.json' file."
        return reply

    # Randomly skip or use card intro for realism
    card, meaning = random.choice(list(tarot_cards.items()))
    intro = random_card_intro() if random.random() > 0.4 else ""

    user_msg_for_prompt = (
        f"{intro}\n"
        f"The card drawn is '{card}' — {meaning}\n" if intro else f"The card says: {meaning}\n"
    )
    user_msg_for_prompt += (
        f"User: '{user_msg}'.\n"
        "Answer in 2-3 grouped lines, like WhatsApp chat, not one big paragraph. Use casual transitions and fillers. Never just copy the card meaning; make it real for the user’s situation."
    )

    # Prepare messages for LLM call, including the global system prompt
    messages_for_llm = [GLOBAL_SYSTEM_PROMPT] + history + [
        {"role": "user", "content": f"{user_msg_for_prompt}\n{style}"}
    ]

    try:
        # DIRECT OPENAI CALL: Using openai.chat.completions.create directly
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_llm
        )
        reply = response.choices[0].message.content.strip()
        return reply
    except Exception as e:
        print(f"GPT error: {e}")
        return f"Card Pulled: {card}. {meaning}" # Fallback if GPT call fails

def group_lines_for_natural_chat(reply_text):
    """Splits a reply into natural-looking chat message groups."""
    lines = reply_text.split('\n')
    grouped_messages = []
    current_group = ''

    for line in lines:
        line = line.strip()
        if not line:
            if current_group:
                grouped_messages.append(current_group)
                current_group = ''
            continue

        if len(current_group) + len(line) + 1 > 150 and current_group:
            grouped_messages.append(current_group)
            current_group = line
        else:
            current_group = (current_group + ' ' + line).strip()

    if current_group:
        grouped_messages.append(current_group)
    
    return grouped_messages


@app.route('/')
def index():
    """Serves the main chat interface HTML page from the root directory."""
    return send_file('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handles chat messages from the frontend."""
    # Add debug prints to inspect the incoming request
    print(f"Incoming Request Headers: {request.headers}")
    print(f"Request Content-Type: {request.headers.get('Content-Type')}")
    print(f"Request Data (raw): {request.get_data(as_text=True)}") # Get raw body data
    print(f"Request Form: {request.form}")
    print(f"Request JSON: {request.json}") # Will be None if Content-Type is not application/json

    # Use session to maintain conversation history for each user
    if "history" not in session:
        session["history"] = []

    # Expecting JSON data based on your logs
    user_message = None
    if request.is_json:
        user_message = request.json.get('message')
    else:
        # Fallback for form data, though logs indicate JSON is being sent
        user_message = request.form.get('msg')
    
    if not user_message:
        # Log why it's empty
        print(f"User message is empty. request.form: {request.form}, request.json: {request.json}")
        return jsonify({"replies": ["Please send a message."]}), 400

    print(f"User: {user_message}")

    # Append user message to history in session
    session["history"].append({"role": "user", "content": user_message})

    # Find the last assistant message in history for language switching
    last_bot_reply = ""
    for i in reversed(session["history"]):
        if i["role"] == "assistant":
            last_bot_reply = i["content"]
            break

    # Pass the session history to the get_tarot_response function
    reply = get_tarot_response(user_message, session["history"], last_bot_reply)

    # Append bot reply to history in session
    session["history"].append({"role": "assistant", "content": reply})
    session.modified = True # Important: Mark session as modified to save changes

    # Group lines for natural chat display in the frontend
    grouped_replies = group_lines_for_natural_chat(reply)

    return jsonify({"replies": grouped_replies})

if __name__ == '__main__':
    print("Flask app starting.")
    print("Ensure 'OPENAI_API_KEY' and 'FLASK_SECRET_KEY' are set as environment variables on Render.")
    print("Access the chat interface locally at http://127.0.0.1:5000/")
    app.run(debug=True)
