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
from .models import PhoneixSpatialData, PhoneixUserData

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

@csrf_exempt
def get_all_coordinates_with_users(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)
    
    spatial_records = PhoneixSpatialData.objects.all()

    results = []

    # Build response by manually joining using userId
    for record in spatial_records:
        user = PhoneixUserData.objects.filter(userId=record.userId).first()

        results.append({
            "latitude": record.latitude,
            "longitude": record.longitude,
            "username": user.username if user else None,
            "first_name": user.first_name if user else None,
            "last_name": user.last_name if user else None,
            "userId": record.userId,
            "land_use": record.user_intent,
            "flood_risk_level": record.flood_risk_level,
            "created_at": record.created_at,
            "ai_recommendation": record.ai_recommendation,
            "vhi": record.vhi,
            "lst_temp": record.lst_temp,
            "lst_category": record.lst_category,
            "drought": record.drought,
        })

    return JsonResponse({"data": results}, safe=False)