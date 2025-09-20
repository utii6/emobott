import requests
import json
import random
import time

# تعريف المتغيرات
token = "7541808565:AAFzfigvQbZk7wOAS7hqZdzpwyItvuV3xK4"
A = 5581457665            # ايدي المطور
ch = "qd3qd"             # يوزر القناة بدون @
emojis = ["❤️", "🔥", "🎉", "👏", "🤩", "💯"]  # قائمة الايموجيات للتفاعل

# دالة عامة لاستدعاء API
def bot(method, datas=None):
    if datas is None:
        datas = {}
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        response = requests.post(url, data=datas)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error in bot method {method}: {e}")
        return None

# التحقق من الاشتراك الإجباري
def check_subscription(user_id):
    url = f"https://api.telegram.org/bot{token}/getChatMember"
    params = {"chat_id": f"@{ch}", "user_id": user_id}
    try:
        res = requests.get(url, params=params).json()
        if res.get("ok"):
            status = res["result"]["status"]
            return status in ["member", "administrator", "creator"]
        return False
    except Exception as e:
        print("Error in check_subscription:", e)
        return False

# الحصول على معلومات البوت
def get_bot_info():
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get('ok'):
            return data['result']
        else:
            print(f"Error: {data.get('description')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return None

bot_info = get_bot_info()
if bot_info is None:
    print("Failed to fetch bot info. Exiting...")
    exit(1)

bot_name = bot_info['first_name']
bot_username = bot_info['username']

# التعامل مع الرسائل
def handle_message(message):
    chat_id = message['chat']['id']
    message_id = message['message_id']
    text = message.get('text', '')
    name = message['from']['first_name']
    from_id = message['from']['id']

    # تحقق من الاشتراك
    if not check_subscription(from_id):
        keyboard = {
            "inline_keyboard": [
                [{"text": "📢 مَـدار", "url": f"https://t.me/{ch}"}]
            ]
        }
        bot("sendMessage", {
            "chat_id": chat_id,
            "text": "🚨 اشترك حبيبي وارسل /start .",
            "reply_markup": json.dumps(keyboard)
        })
        return

    # إذا مشترك
    if text == '/start':
        emojis_str = ' '.join(emojis)
        keyboard = {
            'inline_keyboard': [
                [{'text': "My channel ✌", 'url': f"https://t.me/{ch}"}],
                [
                    {'text': "ضـيـف البـوت للـقنـاة ✨", 'url': f"t.me/{bot_username}?startgroup=new"},
                    {'text': "ضـيـف الـبوت للكـروب 🎶", 'url': f"t.me/{bot_username}?startchannel=new"}
                ],
                [{'text': 'الـمـطور 🎧 ', 'url': f"tg://user?id={A}"}]
            ]
        }
        reply_markup = json.dumps(keyboard)
        bot('sendPhoto', {
            'chat_id': chat_id,
            'photo': "https://zecora0.serv00.net/photo/photo.jpg",
            'caption': f"Hi dear, [{name}](tg://user?id={from_id})\n\n"
                       f"I'm a reaction bot 🍓, my name is {bot_name}\n"
                       f"My job is to interact with messages using {emojis_str}\n"
                       f"I can interact in groups, channels and private chats 🌼\n"
                       f"Just add me to your group or channel and make me an admin with simple permissions ☘️\n"
                       f"And I will interact with every message you send. Try me now 💗",
            'parse_mode': "Markdown",
            'reply_to_message_id': message_id,
            'reply_markup': reply_markup
        })
    else:
        random_emoji = random.choice(emojis)
        bot('setMessageReaction', {
            'chat_id': chat_id,
            'message_id': message_id,
            'reaction': json.dumps([{'type': 'emoji', 'emoji': random_emoji}])
        })

# جلب التحديثات
def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {'timeout': 30, 'offset': offset}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('result', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching updates: {e}")
        return []

def main():
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update['update_id'] + 1
            if 'message' in update:
                handle_message(update['message'])
            if 'channel_post' in update:
                handle_message(update['channel_post'])
        time.sleep(1)

if __name__ == '__main__':
    print("Bot is running...")
    main()
