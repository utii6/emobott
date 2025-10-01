import requests
import json
import random
from fastapi import FastAPI, Request

# ---------- إعدادات البوت ----------
TOKEN = "7541808565:AAHtdo9sZM7wvmW6UQ9-LHFhz0Uo4S5O6no"
ADMIN_ID = 5581457665
CHANNEL = "qd3qd"  # القناة المطلوبة للاشتراك (بدون @)
WEBHOOK_URL = "https://emobott-1.onrender.com/webhook"
EMOJIS = ["❤️", "🔥", "🎉", "👏", "🤩", "💯"]

bot_url = f"https://api.telegram.org/bot{TOKEN}"

# ---------- FastAPI ----------
app = FastAPI()

# ---------- إنشاء ملف groups.json إذا لم يكن موجود ----------
try:
    with open("groups.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"groups": [], "channels": []}
    with open("groups.json", "w") as f:
        json.dump(data, f)

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
    message_id = message.get('message_id', 0)
    text = message.get('text', '')
    name = message['from']['first_name']
    user_id = message['from']['id']

    # تحقق الاشتراك الإجباري
    if not check_subscription(user_id):
        keyboard = {"inline_keyboard":[[{"text":"📢 مَـدار","url":f"https://t.me/{CHANNEL}"}]]}
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
                    {'text': "ضيفني لگروبك  ✨", 'url': f"https://t.me/{bot_username}?startgroup=new"},
                    {'text': "ضيفني لقناتك  🎶", 'url': f"https://t.me/{bot_username}?startchannel=new"}
                ],
                [{'text': "المطور 🎧", 'url': f"tg://user?id={ADMIN_ID}"}]
            ]
        }
        bot("sendMessage", {
            "chat_id": chat_id,
            "text": f"• أهلاً بك {name} في بوت **{bot_name}** 💁\n"
                    "• البوت مختص للتفاعلات التلقائية..\n"
                    "- داخل قناتك او مجموعتك 💎",
            "parse_mode": "Markdown",
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

    # ---------- إشعار المالك عند إضافة مجموعة/قناة جديدة ----------
    known_chats = data["groups"] + data["channels"]
    if chat_id not in known_chats:
        # جلب معلومات المجموعة/القناة
        chat_info = requests.get(f"{bot_url}/getChat", params={"chat_id": chat_id}).json()
        members_count = requests.get(f"{bot_url}/getChatMembersCount", params={"chat_id": chat_id}).json().get("result", 0)
        admins_count = len([x for x in requests.get(f"{bot_url}/getChatAdministrators", params={"chat_id": chat_id}).json().get("result", [])])

        # تحديد إذا كانت مجموعة أو قناة
        if chat_info['result']['type'] == "supergroup" or chat_info['result']['type'] == "group":
            data["groups"].append(chat_id)
        else:
            data["channels"].append(chat_id)

        # حفظ في groups.json
        with open("groups.json", "w") as f:
            json.dump(data, f)

        # إرسال إشعار للمالك
        bot("sendMessage", {
            "chat_id": ADMIN_ID,
            "text": f"✅😂 تم تفعيل مجموعة / قناة جديدة!\n"
                    f"بواسطة الريس 😎: {name}\n"
                    f"معلومات المجموعة / القناة:\n"
                    f"العنوان: {chat_info['result'].get('title','لا يوجد')}\n"
                    f"عدد المواطنين 💁: {members_count}\n"
                    f"عدد الوزراء 😂: {admins_count}\n"
                    f"الرابط 😂: https://t.me/{chat_info['result'].get('username','لا يوجد')}\n\n"
                    f"عدد المجموعات : {len(data['groups'])}\n"
                    f"عدد القنوات : {len(data['channels'])}"
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
