import requests
import json
import random
from fastapi import FastAPI, Request
import os

# ---------- إعدادات البوت ----------
TOKEN = "7541808565:AAFzfigvQbZk7wOAS7hqZdzpwyItvuV3xK4"
ADMIN_ID = 5581457665
CHANNEL = "qd3qd"       # القناة المطلوبة للاشتراك (بدون @)
WEBHOOK_URL = "https://emobott-1.onrender.com/webhook"
EMOJIS = [
    "❤️", "🔥", "🎉", "👏", "🤩", "💯", "😎", "🥳", "🤖", "💥",
    "✨", "🎶", "🫶", "🙌", "🟢", "🔵", "⚡", "🌟", "🍀", "🥰"
]
GROUPS_FILE = "groups.json"

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

# ---------- تحميل بيانات المجموعات والقنوات ----------
if os.path.exists(GROUPS_FILE):
    with open(GROUPS_FILE, "r") as f:
        chats_data = json.load(f)
else:
    chats_data = {"groups": [], "channels": []}

def save_chats():
    with open(GROUPS_FILE, "w") as f:
        json.dump(chats_data, f)

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

# ---------- إشعار المالك عند إضافة بوت لمجموعة/قناة ----------
def notify_owner(chat, from_user):
    chat_id = chat["id"]
    chat_type = chat["type"]
    title = chat.get("title", "بدون اسم")
    user_name = from_user.get("first_name", "مستخدم")

    if chat_type in ["supergroup", "group", "channel"]:
        try:
            member_count = bot("getChatMembersCount", {"chat_id": chat_id})["result"]
            admins_count = len(bot("getChatAdministrators", {"chat_id": chat_id})["result"])
            invite_link = bot("exportChatInviteLink", {"chat_id": chat_id})["result"]

            if chat_type in ["group", "supergroup"] and chat_id not in chats_data["groups"]:
                chats_data["groups"].append(chat_id)
            if chat_type == "channel" and chat_id not in chats_data["channels"]:
                chats_data["channels"].append(chat_id)
            save_chats()

            text = (
                f"😂✅ تم تفعيل {'قناة' if chat_type=='channel' else 'مجموعة'} جديدة\n\n"
                f"- بواسطةالسيد 😎: {user_name}\n"
                f"- معلوماته {'القناة' if chat_type=='channel' else 'المجموعة'}:\n"
                f"- عدد المواطنين 😂 : {member_count}\n"
                f"- عدد الوزراء : {admins_count}\n"
                f"- الرابط : {invite_link}\n\n"
                f"📊😂 المجموعات الحالية: {len(chats_data['groups'])}\n"
                f"📊😑 القنوات الحالية: {len(chats_data['channels'])}"
            )

            bot("sendMessage", {
                "chat_id": ADMIN_ID,
                "text": text
            })

        except Exception as e:
            print("خطأ بإرسال إشعار:", e)

# ---------- معالجة الرسائل ----------
def handle_message(message):
    chat_id = message['chat']['id']
    message_id = message['message_id']
    text = message.get('text', '')
    name = message['from']['first_name']
    user_id = message['from']['id']
    chat_type = message['chat']['type']

    # تحقق الاشتراك الإجباري
    if not check_subscription(user_id):
        keyboard = {"inline_keyboard":[[{"text":"📢مَـدار","url":f"https://t.me/{CHANNEL}"}]]}
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
                    {'text': "ضيفني لقناتك ✨", 'url': f"https://t.me/{bot_username}?startgroup=new"},
                    {'text': "ضيفني لگروبك 🎶", 'url': f"https://t.me/{bot_username}?startchannel=new"}
                ],
                [{'text': "Div 🎧", 'url': f"tg://user?id={ADMIN_ID}"}]
            ]
        }
        # رسالة الترحيب
        bot("sendMessage", {
            "chat_id": chat_id,
            "text": (
                f"• أهلاً بك *{name}* في بوت EMO 💁\n"
                f"• البوت مختص للتفاعلات التلقائية..\n"
                f"- داخل قناتك او مجموعتك 💎."
            ),
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(keyboard)
        })

    # تفاعل عشوائي
    else:
        emoji = random.choice(EMOJIS)
        bot("setMessageReaction", {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": json.dumps([{"type":"emoji","emoji":emoji}])
        })

    # إشعار المالك إذا بوت تمت إضافته لمجموعة/قناة
    if chat_type in ["supergroup", "group", "channel"]:
        notify_owner(message["chat"], message["from"])

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
