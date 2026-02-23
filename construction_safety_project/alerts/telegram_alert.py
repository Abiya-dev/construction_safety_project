import requests

BOT_TOKEN = "8290100783:AAEkOZ-gW-M_4cIhEptqCw9_KgAnjcSVHkk"
CHAT_ID = "6463023700"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)








    







