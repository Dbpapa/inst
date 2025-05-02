import os
import logging
import threading
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)
from telegram.utils.request import Request
from dotenv import load_dotenv
from utils.scraper import InstagramScraper
from utils.database import MongoDB

load_dotenv()

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
        
        # Configure stable Telegram connection
        self.request = Request(
            con_pool_size=8,
            connect_timeout=30.0,
            read_timeout=30.0,
            proxy_url=None
        )
        
        self.bot = Bot(token=self.bot_token, request=self.request)
        self.updater = Updater(bot=self.bot, use_context=True)
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
        
        self.dispatcher.add_error_handler(self.error_handler)

    def valid_username(self, username: str) -> bool:
        """Validate Instagram username format"""
        return bool(re.match(r'^[a-zA-Z0-9._]{1,30}$', username))

    def start(self, update: Update, context: CallbackContext):
        user = update.effective_user
        update.message.reply_text(
            f"👋 Hello {user.first_name}!\n"
            "Send me an Instagram username to download public posts.\n\n"
            "⚠️ Note: Only works with public accounts"
        )
        self.db.log_user(user.id, user.username)

    def handle_username(self, update: Update, context: CallbackContext):
        username = update.message.text.strip().replace('@', '')
        
        if not self.valid_username(username):
            update.message.reply_text("❌ Invalid username format!\n"
                                    "Use only letters, numbers, . and _")
            return

        try:
            update.message.reply_text(f"🔍 Searching for @{username}...")
            posts = self.scraper.get_profile_posts(username)
            
            if not posts:
                update.message.reply_text("❌ No public posts found!\n"
                                        "Account may be private or have no posts.")
                return

            context.user_data['posts'] = posts
            context.user_data['current_index'] = 0
            self.show_post(update, context, 0)

        except Exception as e:
            logger.error(f"Error: {e}")
            update.message.reply_text("⚠️ Service unavailable. Try again later.")

    # [Keep all other methods from previous version unchanged]
    # show_post(), button_handler(), download_post(), etc.

if __name__ == '__main__':
    bot = InstaBot()
    bot.run()
