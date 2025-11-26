# chatbot/utils.py
def extract_lga(text):
    # Simple: match known LGA list
    lgas = ['lokoja', 'yenagoa', 'maiduguri', 'kano', 'enugu', 'ikeja']
    text_lower = text.lower()
    for lga in lgas:
        if lga in text_lower:
            return lga.capitalize()
    return None

def format_reply(risk):
    return (
        f"Location: {risk['lga']}\n\n"
        f"Flood Risk: {risk['flood_risk']}\n"
        f"Drought Risk: {risk['drought_risk']}\n"
        f"Erosion Risk: {risk['erosion_risk']}\n\n"
        f"Recommendation: Avoid building in low-lying areas if flood risk is High."
    )

def send_whatsapp_reply(to, text):
    # Use Meta Graph API
    url = f"https://graph.facebook.com/v20.0/YOUR_PHONE_ID/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",
        "Content-Type": "application/json"
    }
    requests.post(url, json=payload, headers=headers)

def log_query(phone, lga, risk):
    data = {
        "phone": phone[-4:],  # anonymized
        "lga": lga,
        "risk": risk,
        "timestamp": requests.get("http://worldtimeapi.org/api/timezone/UTC").json()['datetime']
    }
    requests.post(FIREBASE_URL, json=data)