from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "yukina_verify_token")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
LLM_API_URL = os.environ.get("LLM_API_URL", "http://localhost:1234/v1/chat/completions")

@app.route('/', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Unauthorized', 403

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                if "message" in event and "text" in event["message"]:
                    user_msg = event["message"]["text"]
                    reply_text = get_bot_response(user_msg)
                    send_reply(sender_id, reply_text)
    return "OK", 200

def get_bot_response(message):
    try:
        response = requests.post(
            LLM_API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "messages": [{"role": "user", "content": message}],
                "temperature": 0.7,
                "max_tokens": 200,
                "stream": False,
                "model": "local-model"
            }
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("LLM error:", e)
        return "Sorry, I couldn't understand that."

def send_reply(recipient_id, text):
    url = f"https://graph.facebook.com/v18.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    r = requests.post(url, params=params, headers=headers, json=data)
    print("FB Response:", r.status_code, r.text) 