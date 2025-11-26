from django.apps import AppConfig
import asyncio
from .telegram import application

class ChatbotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chatbot"

    def ready(self):
        # Run the async initialize once
        asyncio.get_event_loop().create_task(application.initialize())
