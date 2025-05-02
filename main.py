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
    """Minimal health check server for Koyeb port verification"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

def run_health_server():
    """Start health check server in separate thread"""
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

    # [Keep all your existing handler methods here]
    # start(), handle_username(), button_handler(), etc.

    def error_handler(self, update: Update, context: CallbackContext):
        logger.error(msg="Exception:", exc_info=context.error)

    def run(self):
        self.updater.start_polling()
        logger.info("Bot is running...")
        self.updater.idle()

if __name__ == '__main__':
    bot = InstaBot()
    bot.run()
