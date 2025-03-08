# AI Chatbot - CustomFriend

CustomFriend is an AI-powered chatbot built with OpenAI, Telegram Bot API, and Stripe for subscriptions. This bot provides a fun, interactive roleplaying experience and handles subscriptions, voice messages, and text chats.

![Demo Video](cf.mp4)

## Features

- **Chat with an AI-powered friend:** Chat via text or voice.
- **Customizable personality:** Tailor your chatbot’s traits.
- **Subscription Management:** Integrated with Stripe for recurring billing.
- **Voice Processing:** Uses OpenAI’s Whisper and ElevenLabs for voice-to-text and text-to-speech.
- **Telegram Integration:** Works as a Telegram bot for seamless interactions.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-chatbot-customfriend.git
cd ai-chatbot-customfriend
2. Create and Configure the Environment File
Create a .env file in the project root with the following content:

dotenv
Copy
TELEGRAM_TOKEN=your_telegram_bot_token
STRIPE_SECRET_KEY=your_stripe_secret_key
OPENAI_KEY=your_openai_api_key
ELEVEN_LABS_API_KEY=your_eleven_labs_api_key
DB_USERNAME=your_database_username
DB_PASSWORD=your_database_password
stripe_webhook_secret=your_stripe_webhook_secret
Replace the placeholder values with your actual API keys and database credentials.

3. Install Dependencies
Make sure you have Python 3.6 or later installed. Then install the required packages using pip:

bash
Copy
pip install -r requirements.txt
If you don’t have a requirements.txt file, you can manually install the packages:

bash
Copy
pip install python-dotenv openai python-telegram-bot requests playsound stripe sqlalchemy pytz python-dateutil
4. Run the Bot
Run the main script:

bash
Copy
python3 a.py
The bot will start polling for messages on Telegram. You can interact with it by messaging your bot on Telegram.

5. Additional Files
cf.mp4: A demo video of the chatbot in action. Open this file to see a live demonstration of CustomFriend.
CustomFriend Database Models: The models.py file contains SQLAlchemy models for managing user data and subscriptions.
Stripe Webhook: The Flask app in stripe_webhook.py handles Stripe events (ensure your webhook endpoint is set up correctly).
Usage
/start: Begin a conversation with the bot.
/getId: Retrieve your Telegram ID.
/addw /clearw: Manage the whitelist for testing.
Voice and Text Chat: Send voice messages or text to interact with the AI.
Subscription: Follow in-chat prompts to subscribe via Stripe.
Google API Keys and Third-Party Services
Make sure you have valid API keys and proper billing enabled for:

Telegram Bot API
OpenAI API
Stripe API
ElevenLabs API
Contributing
Feel free to submit issues or pull requests if you have suggestions or improvements.

License
This project is licensed under the MIT License.

yaml
Copy

---

Simply update the placeholder API keys in your `.env` file, install the dependencies, and run the bot. The demo video (`cf.mp4`) is displayed in the README so users can quickly see the chatbot in action.
