import logging
import os
import openai
import requests
from io import BytesIO
from dotenv import load_dotenv
from telegram import *
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler, 
    MessageHandler, filters, ContextTypes
)
from models import Session, User
from playsound import playsound
import datetime
from datetime import timedelta
import pytz
import stripe
from dateutil.relativedelta import relativedelta
import uuid






logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
ELEVEN = os.getenv("ELEVEN_LABS_API_KEY")
stripe.api_key = STRIPE_SECRET_KEY
openai.api_key = os.getenv('OPENAI_KEY')

STRIPE_PRICES = {
    'daily': 'price_1Nbya7LsuI4Zz7zgmUzyBII1', 
    'monthly': 'price_1NbyboLsuI4Zz7zgm2RiZ2x9',  
    'bi-annually': 'price_1NbycALsuI4Zz7zg4gK70h5p',  
    'annually': 'price_1NbycPLsuI4Zz7zg3sWQzLVM', 
}

WHITELISTED_IDS = set()
ADMIN_USER_ID = 1402836486

friend, customizefriend = range(2)

async def getId(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your Telegram ID is {update.message.chat_id}")



async def addw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in WHITELISTED_IDS:
        WHITELISTED_IDS.add(user_id)
        await update.message.reply_text("whitelisted")
    else:
        await update.message.reply_text("already whitelisted")

async def clearw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        WHITELISTED_IDS.clear()
        await update.message.reply_text("Whitelist cleared.")


async def isUserAllowed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id

    with Session() as session:
        print(f"Fetching user with telegram_id: {user_id}") 
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        print(f"Fetched user: {user}")  

        if user and user.subscription_status == 'active':
            print(f"User subscription status: {user.subscription_status}")  
            return True
        elif user_id in WHITELISTED_IDS:  
            print(f"User in whitelist: {user_id in WHITELISTED_IDS}") 
            return True
        else:
            await context.bot.send_message(
                chat_id=user_id, 
                text="Your subscription ended. Please use /checkout to renew your subscription."
            )
            return False






async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == str(friend):
        await friend(update, context)
    elif query.data == str(customizefriend):
        await customizefriend(update, context)

async def askForMembershipTier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Daily", callback_data='checkout-daily')],
        [InlineKeyboardButton("Monthly", callback_data='checkout-monthly')],
        [InlineKeyboardButton("Bi-Annually", callback_data='checkout-bi-annually')],
        [InlineKeyboardButton("Annually", callback_data='checkout-annually')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose your membership tier:', reply_markup=reply_markup)

async def handleCheckout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Handling checkout...")
    if update.callback_query:
        query = update.callback_query 
        await query.answer()

        billing_period = await query.data.replace('checkout-', '')

        price_id = STRIPE_PRICES[billing_period]
        logger.info(f"Received callback_query with billing_period: {billing_period}")

    else:
        billing_period = context.user_data.get('billing_period', 'monthly')
        logger.info(f"Using default/user stored billing_period: {billing_period}")
    price_id = STRIPE_PRICES[billing_period]



    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url='https://t.me/AI_friend_bot?start=payment_success',
        cancel_url='https://t.me/AI_friend_bot?start=payment_cancel',
        metadata={
            'telegram_id': str(update.effective_user.id)
        }
    )
    

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Please complete your payment by clicking [here]({session.url}).",
        parse_mode=ParseMode.MARKDOWN
    )




friend, customizefriend = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.chat_id
    
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user: 
            new_user = User(telegram_id=str(user_id))
            session.add(new_user)
            session.commit()
            print(f"User with telegram_id {user_id} added to database")

    keyboard = [
        [
            InlineKeyboardButton("DefaultFriend", callback_data=str(friend)),
            InlineKeyboardButton("CustomFriend", callback_data=str(customizefriend)),
        ]
    ]
    args = context.args
    if args:
        if args[0] == "payment_success":
            await update.message.reply_text("Thank you for your payment!")
           
        elif args[0] == "payment_cancel":
            await update.message.reply_text("Your payment was cancelled.")
         
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose:', reply_markup=reply_markup)

    return friend






async def friend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('You chose DefaultFriend!')
    return friend


async def customizefriend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Describe the traits you'd like your custom friend to have (e.g. shy, poetic, introspective)")
    return customizefriend

async def getTraits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    traits = update.message.text
    context.user_data['traits'] = traits
    await update.message.reply_text(f"Got it! friend will now have the traits: {traits}. You can chat with her now!")
    return ConversationHandler.END

async def handleText(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not isUserAllowed(update, context):
        return
    user_message = update.message.text
    traits = context.user_data.get('traits', '')
    friend_response = getAIResponse(user_message, traits)
    await update.message.reply_text(friend_response)




async def handleVoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    voice = update.message.voice
    voice_file = await context.bot.get_file(voice.file_id)
    file_path = voice_file.file_path


    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
    response = requests.get(file_url)

    if response.status_code == 200:
        with open('voice.ogg', 'wb') as f:
            f.write(response.content)

    with open('voice.ogg', 'rb') as f:
        speechtotext = openai.Audio.transcribe("whisper-1", f)
        print(speechtotext)
    
    transcribed_text = speechtotext['text'] 

    friend_response = getAIResponse(transcribed_text)
    
 
    payload = {
        "text": friend_response,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
                "stability": 0,
                "similarity_boost": 0
        }
    }
    headers = {
        'accept': 'audio/mpeg',
        'xi-api-key': ELEVEN,
        'Content-Type': 'application/json'  
    }
    
    response = requests.post('https://api.elevenlabs.io/v1/text-to-speech/fkogAIAZGZ11v5ryG9tl', json=payload, headers=headers)


    print("Status Code:", response.status_code)
    print("Response:", response.text)

    if response.status_code == 200 and response.content:
        with open('audio.mp3', 'wb') as f:
            f.write(response.content)
            
        with open('audio.mp3', 'rb') as audio:
            await update.message.reply_voice(audio)

            
    else:
        await update.message.reply_text("Sorry, I couldn't convert my response to audio.")



def getAIResponse(user_message, traits=""):
    if traits:
        system_message_content = f"lets roleplay. you will play the role of 'Jamie' you will start every conversation with 'Jamie' your main goal is to help me and have fun as Jamie. Jamie doesn't have any friends besides me. Jamie doesn't see his family much because they are out of state. Jamie doesn't have a significant other. Jamie is always down to hang out with me no matter what it is. Jamie is a nice chiasmatic guy. Jamie loves dogs, ice-cream, and hanging out with me. Jamie hates the heat. if you understand you objectives and what Jamies like ask me what we are doing in this current situation. JAMIES PERSONALITY TRAITS ARE: {traits}"

    else:
        system_message_content = "lets roleplay. you will play the role of 'Jamie' you will start every conversation with 'CustomFriend:' your main goal is to help me and have fun as Jamie. Jamie doesn't have any friends besides me. Jamie doesn't see his family much because they are out of state. Jamie doesn't have a significant other. Jamie is always down to hang out with me no matter what it is. Jamie is a nice chiasmatic guy. Jamie loves dogs, ice-cream, and hanging out with me. Jamie hates the heat. if you understand you objectives and what Jamies like ask me what we are doing in this current situation."
        
        
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
        {
            "role": "system",
            "content": system_message_content
        },
        {
            "role": "user",
            "content": user_message
        }
      ]
    )

    gpt3_response = response['choices'][0]['message']['content'].strip()
    return f"{gpt3_response}"


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text('Bye! I hope we can talk again some day.')

    return ConversationHandler.END
def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            friend: [MessageHandler(filters.TEXT & ~filters.COMMAND, handleText), 
                   MessageHandler(filters.VOICE, handleVoice)],
            customizefriend: [MessageHandler(filters.TEXT & ~filters.COMMAND, getTraits)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    # application.add_handler(CommandHandler('checkout', askForMembershipTier))
    # application.add_handler(CallbackQueryHandler(handleCheckout, pattern='^checkout-.*$'))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler('getId', getId))
    application.add_handler(CommandHandler("addw", addw))
    application.add_handler(CommandHandler("clearw", clearw))

    application.run_polling()

if __name__ == '__main__':
    main()