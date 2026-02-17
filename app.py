from flask import Flask, request, jsonify
import requests
from openai import OpenAI
import os
import sys
import warnings

warnings.filterwarnings("ignore")

app = Flask(__name__)

# ----------------------------
# Environment variables
# ----------------------------
BESTCRM_API_URL = "https://app.bestcrmapp.in/api/v2/whatsapp-business/messages"
ACCESS_TOKEN = os.environ.get("BESTCRM_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GROK_API_KEY = os.environ.get("GROK_API_KEY")

# Check required environment variables
missing_vars = []
if not ACCESS_TOKEN:
    missing_vars.append("BESTCRM_ACCESS_TOKEN")
if not PHONE_NUMBER_ID:
    missing_vars.append("PHONE_NUMBER_ID")
if not GROK_API_KEY:
    missing_vars.append("GROK_API_KEY")

if missing_vars:
    print(f"[ERROR] Missing environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# ----------------------------
# Configure Grok (xAI)
# ----------------------------
client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1"
)

# ----------------------------
# Functions
# ----------------------------
def send_whatsapp_message(to_number, message):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": to_number,
        "phoneNoId": PHONE_NUMBER_ID,
        "type": "text",
        "text": message
    }
    try:
        response = requests.post(
            BESTCRM_API_URL,
            headers=headers,
            json=payload,
            verify=False
        )
        print(f"[WhatsApp] Status: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[WhatsApp] Request Error: {e}")

def get_grok_response(prompt_text):
    try:
        completion = client.chat.completions.create(
            model="grok-2-latest",
            messages=[
                {"role": "system", "content": "You are Cyber Genie, a helpful cybersecurity assistant."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Grok] Error: {e}")
        return "Sorry, AI service is temporarily unavailable."

# ----------------------------
# Routes
# ----------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"[Webhook] Received: {data}")

    try:
        phone_number = data['data']['senderPhoneNumber']
        message_text = data['data']['content']['text'].strip()

        if message_text.lower().startswith("cyber genie,"):
            user_prompt = message_text[len("cyber genie,"):].strip()
            reply = get_grok_response(user_prompt)
        else:
            reply = "Please start your message with 'Cyber Genie,'"

        send_whatsapp_message(phone_number, reply)

    except Exception as e:
        print(f"[Webhook] Error: {e}")

    return jsonify(status="success"), 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Cyber Genie is running", 200
