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

SERVICE_ACCOUNT = "phoenix@ee-street-guide.iam.gserviceaccount.com"
KEY_FILE = "ee.json"
PROJECT_ID = "ee-street-guide"

APP_INITIALIZED = False

@csrf_exempt
async def telegram_webhook(request):
    global APP_INITIALIZED
    
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        update = Update.de_json(data, application.bot)

        # Initialize the application only once
        if not APP_INITIALIZED:
            await application.initialize()
            APP_INITIALIZED = True

        await application.process_update(update)
        return JsonResponse({"status": "ok"})
    
    return JsonResponse({"error": "GET not allowed"})
