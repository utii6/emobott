import requests
import json
import random
from fastapi import FastAPI, Request

# ---------- إعدادات البوت ----------
TOKEN = "7541808565:AAFzfigvQbZk7wOAS7hqZdzpwyItvuV3xK4"
ADMIN_ID = 5581457665
CHANNEL = "qd3qd"       # القناة المطلوبة للاشتراك (بدون @)
EMOJIS = ["❤️", "🔥", "🎉", "👏", "🤩", "💯"]

bot_url = f"https://api.telegram.org/bot{TOKEN}"

# ---------- FastAPI ----------
app = FastAPI()

# ---------- دالة ارسال أي أمر للـ Telegram ----------
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
        keyboard = {"inline_keyboard":[[{"text":"📢 اشترك بالقناة أولاً","url":f"https://t.me/{CHANNEL}"}]]}
        bot("sendMessage", {
            "chat_id": chat_id,
            "text": "🚨 لازم تشترك بالقناة حتى تستخدم البوت.",
            "reply_markup": json.dumps(keyboard)
        })
        return

    # /start
    if text == "/start":
        keyboard = {
            "inline_keyboard":[
                [{"text":"My channel ✌","url":f"https://t.me/{CHANNEL}"}],
                [
                    {"text":"ضيف البوت للقناة ✨","url":f"t.me/{TOKEN}?startgroup=new"},
                    {"text":"ضيف البوت للكروب 🎶","url":f"t.me/{TOKEN}?startchannel=new"}
                ],
                [{"text":"المطور 🎧","url":f"tg://user?id={ADMIN_ID}"}]
            ]
        }
        bot("sendMessage", {
            "chat_id": chat_id,
            "text": f"Hi {name}! 🌸\nالبوت جاهز للتفاعل مع رسائلك باستخدام الإيموجيات.",
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

# ضع رابط مشروعك على Render مع /webhook في آخره
# مثال: https://اسم-مشروعك.onrender.com/webhook
WEBHOOK_URL = "ضع_رابط_مشروعك_هنا/webhook"
set_webhook(WEBHOOK_URL)
