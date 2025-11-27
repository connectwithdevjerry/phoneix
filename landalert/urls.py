from django.urls import path
from chatbot.views import get_all_coordinates_with_users, telegram_webhook

urlpatterns = [
    path("telegram/webhook/", telegram_webhook, name="telegram-webhook"),
    path("coordinates-with-users/", get_all_coordinates_with_users, name="coordinates-with-users"),
]