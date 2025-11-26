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

print("views page, 1")

def test_location(request):
    lat = 7.798
    lon = 6.742
    result = get_risk_from_point(lat, lon)
    return JsonResponse(result)


SERVICE_ACCOUNT = "phoenix@ee-street-guide.iam.gserviceaccount.com"
KEY_FILE = "ee.json"
PROJECT_ID = "ee-street-guide"

@csrf_exempt
async def telegram_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        # print("Received Telegram update:", data)
        update = Update.de_json(data, application.bot)
        if not getattr(application, '_is_initialized', False):
            await application.initialize(project=PROJECT_ID, service_account=SERVICE_ACCOUNT, key_file=KEY_FILE)
            application._is_initialized = True
        await application.process_update(update)
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "GET not allowed"})