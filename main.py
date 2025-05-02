import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)
from dotenv import load_dotenv
from utils.scraper import InstagramScraper
from utils.database import MongoDB

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

def run_health_server():
    server = HTTPServer(('0.0.0.0', 3000), HealthCheckHandler)
    logger.info("Health check server running on port 3000")
    server.serve_forever()

class InstaBot:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.updater = Updater(token=self.bot_token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.scraper = InstagramScraper()
        self.db = MongoDB()
        
        # Start health server
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()

        # Register handlers
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_username))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Error handling
        self.dispatcher.add_error_handler(self.error_handler)

    # ------ ADD MISSING HANDLERS HERE ------
    def start(self, update: Update, context: CallbackContext):
        """Handle /start command"""
        user = update.effective_user
        update.message.reply_text(
            f"👋 Hello {user.first_name}!\n"
            "Send me an Instagram username to download posts."
        )
        self.db.log_user(user.id, user.username)

    def handle_username(self, update: Update, context: CallbackContext):
        """Process Instagram username input"""
        username = update.message.text.strip()
        # Add your Instagram processing logic here
        update.message.reply_text(f"🔍 Searching for @{username}...")

    def button_handler(self, update: Update, context: CallbackContext):
        """Handle inline keyboard buttons"""
        query = update.callback_query
        query.answer()
        # Add your button handling logic here
        query.edit_message_text(text="Button pressed!")

    def error_handler(self, update: Update, context: CallbackContext):
        """Handle errors"""
        logger.error(msg="Exception:", exc_info=context.error)
        if update:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ An error occurred. Please try again."
            )

    def run(self):
        """Start the bot"""
        self.updater.start_polling()
        logger.info("Bot is running...")
        self.updater.idle()

if __name__ == '__main__':
    bot = InstaBot()
    bot.run()
