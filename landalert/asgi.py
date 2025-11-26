"""
ASGI config for landalert project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import asyncio
import os
from django.core.asgi import get_asgi_application
from chatbot.telegram import application as app # Corrected import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landalert.settings')
SERVICE_ACCOUNT = "phoenix@ee-street-guide.iam.gserviceaccount.com"
KEY_FILE = "ee.json"
PROJECT_ID = "ee-street-guide"

# --- Initialization Function ---
async def initialize_telegram_bot(app_instance):
    """Initializes the Telegram bot application only once."""
    if not getattr(app_instance, '_is_initialized', False):
        print("Starting Telegram Application initialization...")
        await app_instance.initialize(project=PROJECT_ID, service_account=SERVICE_ACCOUNT, key_file=KEY_FILE)
        app_instance._is_initialized = True
        print("Telegram Application initialized successfully.")

    if not getattr(app_instance, '_is_running', False):
        print("Starting Telegram Application...")
        await app_instance.start()
        app_instance._is_running = True
        print("Telegram Application started successfully.")

# --- Django ASGI Application ---
application = get_asgi_application()

async def myapplication(scope, receive, send):
    """The main ASGI application, ensuring initialization runs before handling requests."""
    # Run the initialization task (it checks the flag internally)
    await initialize_telegram_bot(app) 
    
    # Hand off to the standard Django handler
    await application(scope, receive, send)
