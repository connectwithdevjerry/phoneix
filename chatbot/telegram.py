import os
from .aisetup import generate_smart_recommendation
from .flood import floodAnalysis
from .drought import droughtAnalysis
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup, KeyboardButton, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ChatAction
from .gee_engine import lstAnalysis
from django.utils import timezone
from asgiref.sync import sync_to_async

BOT_TOKEN ="8496710291:AAH76wzl7zPh0p23QS4Ya8NDVhxYYpTuT6o"

# Create the Application object
application = Application.builder().token(BOT_TOKEN).build()


# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcomeMessage = """<b>👋 Welcome to LandAlert Bot!</b>
    I provide <b>real-time land risk analysis</b>
    Please <b>share your current location</b> with the location button so I can begin your analysis. 🌍
    """

    # get user data
    user = update.effective_user

    #########
    from .models import PhoneixUserData
    #########

    user_data, created = await sync_to_async(PhoneixUserData.objects.get_or_create)(
        username=user.username,
        defaults={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "userId": str(user.id),
        }
    )
    

    print(f"User data: {user_data}, Created: {created}")

    await update.message.reply_text(
        welcomeMessage, parse_mode='HTML'
    )


async def mrecommendation(update, context):
    text = "Please describe your intended usage of the land."

    keyboard = [
        [
            InlineKeyboardButton(
                text="Fill Usage",
                switch_inline_query_current_chat="My Usage: "
            )
        ]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def recommendation(update, context):
    # update.message.text
    provideIntendedUsage = "To provide the most accurate analysis, please share your intended usage of the land at your location (e.g., agriculture, construction, conservation)."
    await update.message.reply_text(provideIntendedUsage, reply_markup=ForceReply(input_field_placeholder="My Usage: "))
    context.user_data["awaiting_usage"] = True

async def aiRecommendation(update, context):
    if context.user_data.get("awaiting_usage"):
        user_text = update.message.text
        if user_text.lower().startswith("my usage:"):
            usage = user_text[len("My Usage:"):].strip()
        else:
            usage = user_text.strip()
            
        context.user_data["awaiting_usage"] = False

        user_input = usage
        user = update.effective_user
        #########
        from .models import PhoneixSpatialData
        #########
        latest_record = await sync_to_async(PhoneixSpatialData.objects.filter(userId=str(user.id)).latest)('created_at')

        # Here you would integrate with an AI service to generate recommendations based on user_input
        ai_response = generate_smart_recommendation(latest_record.longitude, latest_record.latitude, user_intent=user_input, user_name=user.username or user.first_name or "there", flood_susceptibility=latest_record.flood_risk_level, vhi=latest_record.vhi, lst_temp=latest_record.lst_temp, lst_category=latest_record.lst_category, drought=latest_record.drought)
        

        # Save AI recommendation and user intent to the database 
        
        # if latest_record:
        latest_record.ai_recommendation = ai_response
        latest_record.user_intent = user_input
        await sync_to_async(latest_record.save)(update_fields=['ai_recommendation', 'user_intent'])

        await update.message.reply_text(ai_response, reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("Unrecognized Command!\n Kindly share your location to proceed!", reply_markup=ReplyKeyboardRemove())

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles incoming messages that contain location data.
    The location object is available at update.message.location.
    """
    print("Handling location update...")

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    await update.message.reply_text("🔍 I'm analyzing your location, please wait...")
    
    user_location = update.message.location
    latitude = user_location.latitude
    longitude = user_location.longitude

    myLst = lstAnalysis(latitude, longitude)
    myDrought = droughtAnalysis(latitude, longitude)
    myFlood = floodAnalysis(latitude, longitude)

    temp = myLst['Temperature (°C)']
    vhi = myDrought['VHI']
    category = myLst['Category']
    temp_str = f"{temp}°C" if temp else "N/A"
    suceptibility_class = myFlood['Flood_Susceptibility_Class']
    description = myFlood['Description']

    #########
    from .models import PhoneixSpatialData
    #########

    # Save data to the database
    await sync_to_async(PhoneixSpatialData.objects.create)(
        longitude=longitude,
        latitude=latitude,
        vhi=vhi,
        lst_temp=temp,
        lst_category=category,
        drought=myDrought['Drought_Class'],
        flood_risk_level=int(suceptibility_class),
        user_intent="unspecified",
        userId=str(update.effective_user.id)
    )

    reply = f"""
        <b>🛰️ LandAlert Report 🛰️</b>
        <i>Real-time analysis by Team Phoenix</i>

        ---
        <b>Geographic Data</b>
        <b>🌍 Coordinates:</b> lat: {latitude}, lon: {longitude}
        ---

        <b>Environmental Status</b>
        <b>🌡️ Surface Temperature:</b> <b>{category.capitalize()}!</b> ({temp_str})
        <b>💧 Drought Risk:</b> <b>{myDrought['Drought_Class']}</b>
            - VHI (Vegetation Health Index): {vhi}
        <b>🌊 Flood Susceptibility:</b> <b>Level {suceptibility_class} of 5 - {description}</b>
        ---
    """
    print("Received location:", latitude, longitude)
    print("Full update object:", update)

    await update.message.reply_text("Thanks for sharing your location! Here's your analysis:\n\n")

    keyboard = [
        [KeyboardButton("/recommendation")]
    ]

    await update.message.reply_text(
        reply, parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("recommendation", recommendation))
# application.add_handler(CommandHandler("mrecommendation", mrecommendation))
application.add_handler(MessageHandler(filters.LOCATION, handle_location))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, aiRecommendation))