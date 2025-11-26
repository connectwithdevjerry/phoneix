# chatbot/views.py
from django.http import JsonResponse
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import json, os
import requests
from django.views.decorators.csrf import csrf_exempt
from .telegram import application

FIREBASE_URL = "https://landalert-2c4eb-default-rtdb.firebaseio.com/queries.json"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# bot = Bot(TELEGRAM_TOKEN)
# application = Application.builder().token(TELEGRAM_TOKEN).build()

def test_location(request):
    lat = 7.798
    lon = 6.742
    result = get_risk_from_point(lat, lon)
    return JsonResponse(result)

@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhook(View):
    def get(self, request):
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == "landalert123":
            return HttpResponse(challenge, content_type="text/plain")
        return JsonResponse({"error": "Forbidden"}, status=403)

    def post(self, request):
        try:
            data = json.loads(request.body)
            msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
            phone = msg["from"]

            lat = lon = name = None

            # === NATIVE LOCATION SHARE ===
            if msg.get("type") == "location":
                lat = msg["location"]["latitude"]
                lon = msg["location"]["longitude"]
                name = msg["location"].get("name", "Unknown location")

            # === TEXT WITH COORDS (fallback) ===
            elif msg.get("type") == "text":
                text = msg["text"]["body"].strip()
                parts = [p.strip() for p in text.replace(',', ' ').split()]
                if len(parts) >= 2:
                    try:
                        lat = float(parts[0])
                        lon = float(parts[1])
                        name = f"{lat}, {lon}"
                    except:
                        pass

            # === NO VALID LOCATION ===
            if not lat or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                reply = "Please share your location using WhatsApp's 'Share Location' button."
            else:
                risk = get_risk_from_point(lat, lon)
                temp = risk['temperature_c']
                temp_str = f"{temp}°C" if temp else "N/A"
                reply = (
                    f"*LandAlert Report*\n"
                    f"Location: `{lat}, {lon}`\n"
                    f"Name: {name}\n\n"
                    f"Flood Risk: {risk['flood_risk']}\n"
                    f"Drought Risk: {risk['drought_risk']}\n"
                    f"Heat Risk: {risk['heat_risk']}\n"
                    f"Temperature: {temp_str}\n\n"
                    f"_Real-time analysis by Google Earth Engine_"
                )
                # Log to Firebase
                requests.post(FIREBASE_URL, json={
                    "phone": phone[-4:], "lat": lat, "lon": lon, "risk": risk
                })

            # === SEND REPLY ===
            url = f"https://graph.facebook.com/v20.0/YOUR_PHONE_ID/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "text",
                "text": {"body": reply}
            }
            headers = {
                "Authorization": "Bearer YOUR_TOKEN",
                "Content-Type": "application/json"
            }
            requests.post(url, json=payload, headers=headers)

            return JsonResponse({"status": "ok"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        

# Create bot + application once

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(
#         chat_id=update.effective_chat.id,
#         text="Hello from Django!"
#     )

# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(
#         chat_id=update.effective_chat.id,
#         text=update.message.text
#     )

# # Register handlers once
# application.add_handler(CommandHandler("start", start))
# application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

@csrf_exempt
async def telegram_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        # print("Received Telegram update:", data)
        update = Update.de_json(data, application.bot)
        if not getattr(application, '_is_initialized', False):
            await application.initialize()
            application._is_initialized = True
        await application.process_update(update)
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "GET not allowed"})