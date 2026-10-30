import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import telebot
import requests

BOT_TOKEN = os.environ.get('BOT_TOKEN')
NEXTDNS_API_KEY = os.environ.get('NEXTDNS_API_KEY')

if not BOT_TOKEN or not NEXTDNS_API_KEY:
    print("Error: Missing BOT_TOKEN or NEXTDNS_API_KEY environment variables.")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# --- ITO ANG BAGONG LINYA PARA MA-FIX ANG 409 ERROR ---
bot.delete_webhook()
# ------------------------------------------------------

HEADERS = {
    "X-Api-Key": NEXTDNS_API_KEY,
    "Content-Type": "application/json"
}

# --- DUMMY WEB SERVER PARA SA RENDER ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), BaseHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()
# ---------------------------------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome boss! I-type mo ang /getdns para makuha ang VIP Private DNS mo para sa MLBB.")

@bot.message_handler(commands=['getdns'])
def give_dns(message):
    user_id = message.from_user.id
    
    bot.reply_to(message, "Wait lang boss, ginagawa ko pa yung VIP DNS mo. Mag-hintay ka ng mga 5-10 seconds...")

    profile_name = f"MLBB-VIP-{user_id}"
    
    try:
        res = requests.post("https://api.nextdns.io/profiles", headers=HEADERS, json={"name": profile_name})
        
        if res.status_code != 200:
            bot.reply_to(message, f"Error boss: {res.text}")
            return
        
        profile_id = res.json()['data']['id']
        
        domains = ["appsflyer.com", "umeng.com", "gcloud.tencent.com"]
        for domain in domains:
            requests.post(f"https://api.nextdns.io/profiles/{profile_id}/denylist", 
                          headers=HEADERS, json={"id": domain, "active": True})
        
        requests.patch(f"https://api.nextdns.io/profiles/{profile_id}/settings", 
                       headers=HEADERS, json={"blockPage": {"enabled": False}})
        
        dns_string = f"{profile_id}.dns.nextdns.io"
        
        msg = (
            f"✅ **Success!** Ito na ang VIP Private DNS mo:\n\n"
            f"`{dns_string}`\n\n"
            f"Paano gamitin:\n"
            f"1. Punta sa Settings ng phone mo.\n"
            f"2. Connections > More connection settings > Private DNS.\n"
            f"3. Piliin ang 'Private DNS provider hostname' at i-paste ito.\n"
            f"4. Save!"
        )
        bot.reply_to(message, msg, parse_mode='Markdown')
        
    except Exception as e:
        bot.reply_to(message, f"May error na nangyari boss. Try again later.")

print("Bot is running...")
bot.infinity_polling()
