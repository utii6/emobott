import requests
import json
import random
from fastapi import FastAPI, Request
from pathlib import Path

# ---------- إعدادات البوت ----------
TOKEN = "7541808565:AAFzfigvQbZk7wOAS7hqZdzpwyItvuV3xK4"
ADMIN_ID = 5581457665
CHANNEL = "qd3qd"  # القناة المطلوبة للاشتراك (بدون @)
WEBHOOK_URL = "https://emobott-1.onrender.com/webhook"
EMOJIS = ["❤️", "🔥", "🎉", "👏", "🤩", "💯"]
GROUPS_FILE = "groups.json"

bot_url = f"https://api.telegram.org/bot{TOKEN}"

# ---------- FastAPI ----------
app = FastAPI()

# ---------- إدارة ملف المجموعات / القنوات ----------
def load_groups():
    if Path(GROUPS_FILE).exists():
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"groups": [], "channels": []}

def save_groups(data):
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_group(chat_id, title, members_count, admins_count, added_by):
    data = load_groups()
    if chat_id not in [g["id"] for g in data["groups"]]:
        data["groups"].append({
            "id": chat_id,
            "title": title,
            "members_count": members_count,
            "admins_count": admins_count,
            "added_by": added_by
        })
        save_groups(data)

def add_channel(chat_id, title, members_count, admins_count, added_by):
    data = load_groups()
    if chat_id not in [c["id"] for c in data["channels"]]:
        data["channels"].append({
            "id": chat_id,
            "title": title,
            "members_count": members_count,
            "admins_count": admins_count,
            "added_by": added_by
        })
        save_groups(data)

def get_counts():
    data = load_groups()
    return len(data["groups"]), len(data["channels"])

# ---------- إرسال أوامر للبوت ----------
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

# ---------- معلومات البوت ----------
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

    # تمييز إذا الرسالة من مستخدم أو قناة
    if 'from' in message:
        name = message['from']['first_name']
        user_id = message['from']['id']
    else:
        name = message['chat'].get('title', 'القناة')
        user_id = None

    # الاشتراك الإجباري للمستخدمين فقط
    if user_id and not check_subscription(user_id):
        keyboard = {"inline_keyboard":[[{"text":"📢مَـدار ","url":f"https://t.me/{CHANNEL}"}]]}
        bot("sendMessage", {
            "chat_id": chat_id,
            "text": "🚨اشترك حبيبي وأرسل /start .",
            "reply_markup": json.dumps(keyboard)
        })
        return

    # /start للمستخدمين
    if text == "/start" and user_id:
        keyboard = {
            'inline_keyboard': [
                [{'text': "channel ✌", 'url': f"https://t.me/{CHANNEL}"}],
                [
                    {'text': "ضيفني لمجموعتك ✨", 'url': f"https://t.me/{bot_username}?startgroup=new"},
                    {'text': "ضيفني لقناتك 🎶", 'url': f"https://t.me/{bot_username}?startchannel=new"}
                ],
                [{'text': "Div 🎧", 'url': f"tg://user?id={ADMIN_ID}"}]
            ]
        }
        bot("sendMessage", {
            "chat_id": chat_id,
            "text": f"• أهلاً بك {name} في بوت EMO 💁\n"
                    f"• البوت مختص للتفاعلات التلقائية..\n"
                    f"- داخل قناتك او مجموعتك 💎.",
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

# ---------- Webhook ----------
@app.post("/webhook")
async def webhook(request: Request):
    update = await request.json()

    # رسائل ومجموعات/قنوات
    if "message" in update:
        handle_message(update["message"])
    if "channel_post" in update:
        handle_message(update["channel_post"])

    # إضافة البوت لمجموعة أو قناة
    if "my_chat_member" in update:
        member_update = update["my_chat_member"]
        chat = member_update["chat"]
        new_status = member_update["new_chat_member"]["status"]
        if new_status in ["administrator", "member"]:
            chat_id = chat["id"]
            title = chat.get("title", "المجموعة / القناة")
            added_by = member_update.get("from", {}).get("first_name", "Unknown")
            # افتراض عدد الأعضاء والإدمنية صفر مؤقتاً (يمكن جلبهم لاحقاً)
            members_count = 0
            admins_count = 0
            if chat["type"] == "supergroup":
                add_group(chat_id, title, members_count, admins_count, added_by)
            else:
                add_channel(chat_id, title, members_count, admins_count, added_by)

            groups_count, channels_count = get_counts()
            bot("sendMessage", {
                "chat_id": ADMIN_ID,
                "text": f"✅😂تم تفعيل مجموعة / قناة جديدة!\n"
                        f"بواسطة الريس 😎: {added_by}\n"
                        f"معلومات المجموعة / القناة:\n"
                        f"عدد المواطنين 💁: {members_count}\n"
                        f"عدد الوزراء 😂: {admins_count}\n"
                        f"الرابط😂: ...\n\n"
                        f"عدد المجموعات 16: {groups_count}\n"
                        f"عدد القنوات 18: {channels_count}"
            })

    return {"ok": True}

# ---------- ضبط Webhook ----------
def set_webhook(url):
    requests.get(f"{bot_url}/setWebhook?url={url}")

set_webhook(WEBHOOK_URL)
