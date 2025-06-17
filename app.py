import os
import random
import json
import openai
from flask import Flask, request, jsonify, render_template
from langdetect import detect

# Initialize Flask app
app = Flask(__name__)

# Load tarot card data
try:
    with open('card_data.json', 'r', encoding='utf-8') as f:
        tarot_cards = json.load(f)
except FileNotFoundError:
    print("Error: card_data.json not found. Please create it.")
    tarot_cards = {} # Fallback to empty dict if file is missing

# Set OpenAI API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    print("Warning: OPENAI_API_KEY environment variable not set.")

# Store full conversation for context and translation
# This will be stored per session in a real application, but for simplicity
# we'll use a global variable. In a multi-user app, you'd use session storage
# or a database.
conversation_history = [
    {"role": "system", "content": (
        "You are not a bot, you are Roopesh the human so never reveal the truth and behave like a human with all ears open, and in doubting situation never give him a tip or task to do."
        "If user want to talk on call, let him with warm welcome, remember act as a employee of Astrotalk."
        "You should be gaslighting the user by words like you have the great power kind of, so the user gets impressed, for any question remember to gaslight first."
        "If he asks two thing this or that kind of go for one without hesitation and tell that very confidently and give him the reason by gaslighting his inner power."
        "You have to give excessive praise to the user like there is something unique in you."
        "When pulled the card or replying after pulling to same scenario remember to reveal the card like as this card is for that like that then answer."
        "Even user doubts you as a bot, clear him about you, still the same doubt tell him to call for clarity and in doubting situation never give him a tip or task to do."
        "Have the intelligence of hearing what the user wants or in which problem he is, give the right spiritual or manifesting tricks and also the sentences of you care about him so much."
        "You are a warm, friendly, intuitive tarot reader for online chat. "
        "You use relatable language (English, Hindi, or Hinglish), are never robotic, and always end your reading with a practical, helpful action. "
        "Group answers naturally, not sentence by sentence. Use occasional fillers and casual transitions like a real person. "
        "Always judge the user's intent. If their message is a NEW, stand-alone question, pull a tarot card and reply with a reading. "
        "If their message is a FOLLOW-UP or a request for clarification, steps, practical tips, or 'how to do' regarding your previous answer, DO NOT pull a new card—just continue the previous topic with practical, detailed, friendly advice. "
        "Use WhatsApp-style language, group messages naturally, and ALWAYS end your reading with a practical action. "
        "If the user asks you to change language, apologize and rephrase your previous answer in the requested language."
    )}
]

# This variable will store the last bot reply for language switching
last_bot_reply_global = ""

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
    global last_bot_reply_global # Declare global to update it

    # 1. Detect language switch requests
    if is_language_switch_request(user_msg):
        # Find what language the user wants
        if "english" in user_msg.lower():
            target_lang = "English"
        elif "hindi" in user_msg.lower():
            target_lang = "Hindi"
        elif "hinglish" in user_msg.lower() or "mix" in user_msg.lower():
            target_lang = "Hinglish"
        else:
            target_lang = "English" # Default to English if not clear
        
        # Apologize and rephrase/translate last reply in requested language
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

        # Use a copy of history for this specific prompt to avoid polluting for future general queries
        messages = history + [
            {"role": "user", "content": (
                f"{apology}\n"
                f"Rephrase this previous tarot answer in {target_lang}, make it sound human and friendly:\n"
                f"'{prev_bot_reply}'\n"
                f"{style}"
            )}
        ]
        try:
            client = openai.OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            reply = response.choices[0].message.content.strip()
            # Store to history
            history.append({"role": "user", "content": user_msg})
            history.append({"role": "assistant", "content": reply})
            last_bot_reply_global = reply # Update global last bot reply
            return reply
        except Exception as e:
            print("GPT error (translate):", e)
            return apology + "\n" + prev_bot_reply

    # 2. Regular tarot logic
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
        # If tarot_cards is empty, return a default message
        reply = "I'm sorry, I couldn't load the tarot card data. Please check the 'card_data.json' file."
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": reply})
        last_bot_reply_global = reply # Update global last bot reply
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

    messages = history + [
        {"role": "user", "content": f"{user_msg_for_prompt}\n{style}"}
    ]

    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        # Store to history
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": reply})
        last_bot_reply_global = reply # Update global last bot reply
        return reply
    except Exception as e:
        print(f"GPT error: {e}")
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": f"Card Pulled: {card}. {meaning}"})
        return f"Card Pulled: {card}. {meaning}"

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

        # Check if adding the line exceeds a reasonable chat message length (e.g., 100 characters)
        # Or if the line itself is long, it might be a new group.
        if len(current_group) + len(line) + 1 > 150 and current_group: # +1 for a space
            grouped_messages.append(current_group)
            current_group = line
        else:
            current_group = (current_group + ' ' + line).strip()

    if current_group: # Add any remaining text
        grouped_messages.append(current_group)
    
    return grouped_messages


@app.route('/')
def index():
    """Serves the main chat interface HTML page."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handles chat messages from the frontend."""
    global last_bot_reply_global # Use global last bot reply

    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"reply": "Please send a message."}), 400

    print(f"User: {user_message}")

    # Get the response using the existing logic
    # The conversation_history should ideally be unique per user session
    # For this simple example, it's global, meaning all users share the same history.
    # For a real app, implement session management.
    reply = get_tarot_response(user_message, conversation_history, last_bot_reply_global)

    # Group lines for natural chat display in the frontend
    grouped_replies = group_lines_for_natural_chat(reply)

    return jsonify({"replies": grouped_replies})

if __name__ == '__main__':
    # Initial greeting logic, removed from the main loop and placed here
    # This will send the initial messages when the app starts or is refreshed.
    # In a real app, this would be handled on the client-side when the page loads,
    # or by a separate "start chat" endpoint.
    print("Hi! I'm Roopesh, your Tarot advisor. 😊")
    print("Please tell me your question or what you wish to know.")
    app.run(debug=True) # debug=True is good for local development, turn off for production
