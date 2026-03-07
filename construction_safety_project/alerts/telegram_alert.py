import requests

def send_telegram_alert(message):
    # --- ENTER YOUR CREDENTIALS ---
    apiToken = "8290100783:AAEkOZ-gW-M_4cIhEptqCw9_KgAnjcSVHkk"
    chatID = "6463023700"
    # ------------------------------
    
    apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'
    try:
        payload = {'chat_id': chatID, 'text': message}
        response = requests.post(apiURL, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[SUCCESS] Telegram alert sent.")
        else:
            print(f"[FAILED] Telegram Error {response.status_code}: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Telegram Connection: {e}")
        return False

#BOT_TOKEN = "8290100783:AAEkOZ-gW-M_4cIhEptqCw9_KgAnjcSVHkk"
#CHAT_ID = "6463023700"


















    







