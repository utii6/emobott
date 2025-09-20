import requests
import json
import random
from fastapi import FastAPI, Request

# ---------- إعدادات البوت ----------
TOKEN = "7541808565:AAFzfigvQbZk7wOAS7hqZdzpwyItvuV3xK4"
ADMIN_ID = 5581457665
CHANNEL = "qd3qd"       # القناة المطلوبة للاشتراك (بدون @)
WEBHOOK_URL = "https://emobott-1.onrender.com/webhook"
WELCOME_PHOTO = "https://i.ibb.co/6ZsT3kM/welcome.jpg"  # رابط خارجي للصورة
EMOJIS = ["❤️", "🔥", "🎉", "👏", "🤩", "💯"]

bot_url = f"https://api.telegram.org/bot{TOKEN}"

# ---------- FastAPI ----------
app = FastAPI()

# ---------- دالة إرسال أوامر للـ Telegram ----------
def bot(method, data=None):
    if data is None:
        data = {}
    url = f"{bot_url}/{method}"
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Bot error ({method}): {e}")
        return None

# ---------- جلب معلومات البوت ----------
def get_bot_info():
    try:
        res = requests.get(f"{bot_url}/getMe").json()
        if res.get("ok"):
            return res["result"]
        return None
    except:
        return None

bot_info = get_bot_info()
if not bot_info:
    print("Failed to get bot info. Exiting...")
    exit(1)

bot_username = bot_info['username']
bot_name = bot_info['first_name']

# ---------- تحقق الاشتراك ----------
def check_subscription(user_id):
    try:
        res = requests.get(f"{bot_url}/getChatMember",
                           params={"chat_id": f"@{CHANNEL}", "user_id": user_id}).json()
        if res.get("ok"):
            status = res["result"]["status"]
            return status in ["member", "creator", "administrator"]
        return False
    except:
        return False

# ---------- معالجة الرسائل ----------
def handle_message(message):
    chat_id = message['chat']['id']
    message_id = message['message_id']
    text = message.get('text', '')
    name = message['from']['first_name']
    user_id = message['from']['id']

    # تحقق الاشتراك الإجباري
    if not check_subscription(user_id):
        keyboard = {"inline_keyboard":[[{"text":"📢مَـدار ","url":f"https://t.me/{CHANNEL}"}]]}
        bot("sendMessage", {
            "chat_id": chat_id,
            "text": "🚨 اشترك حبيبي وأرسل /start .",
            "reply_markup": json.dumps(keyboard)
        })
        return

    # /start
    if text == "/start":
        keyboard = {
            'inline_keyboard': [
                [{'text': "My channel ✌", 'url': f"https://t.me/{CHANNEL}"}],
                [
                    {'text': "ضيف البوت للقناة ✨", 'url': f"https://t.me/{bot_username}?startgroup=new"},
                    {'text': "ضيف البوت للكروب 🎶", 'url': f"https://t.me/{bot_username}?startchannel=new"}
                ],
                [{'text': "المطور 🎧", 'url': f"tg://user?id={ADMIN_ID}"}]
            ]
        }
        bot("sendPhoto", {
            "chat_id": chat_id,
            "photo": WELCOME_PHOTO,
            "caption": f"أهلاً {name}!\nالبوت {bot_name} جاهز للتفاعل 🍓",
            "reply_markup": json.dumps(keyboard)
        })
    else:
        # تفاعل عشوائي
        emoji = random.choice(EMOJIS)
        bot("setMessageReaction", {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": json.dumps([{"type":"emoji","emoji":emoji}])
        })

# ---------- نقطة الدخول Webhook ----------
@app.post("/webhook")
async def webhook(request: Request):
    update = await request.json()
    if "message" in update:
        handle_message(update["message"])
    if "channel_post" in update:
        handle_message(update["channel_post"])
    return {"ok": True}

# ---------- ضبط Webhook (تشغّل مرة واحدة) ----------
def set_webhook(url):
    requests.get(f"{bot_url}/setWebhook?url={url}")

set_webhook(WEBHOOK_URL)
