from django.urls import path
from chatbot.views import WhatsAppWebhook
from chatbot.views import test_location, telegram_webhook

urlpatterns = [
    # path('webhook/', WhatsAppWebhook.as_view(), name='webhook'),
    path('webhook/', WhatsAppWebhook.as_view(), name='webhook'),
    path("telegram/webhook/", telegram_webhook, name="telegram-webhook"),
    path('test/', test_location),
]