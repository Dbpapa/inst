import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv
from utils.instagram_scraper import InstagramScraper
from utils.helpers import db_manager

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class InstagramDownloaderBot:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.admin_id = os.getenv('ADMIN_ID')
        self.updater = Updater(token=self.bot_token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.scraper = InstagramScraper()
        
        # Register handlers
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CommandHandler("help", self.help))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Error handler
        self.dispatcher.add_error_handler(self.error_handler)

    # ... [Keep all the main.py code from previous answer exactly as is] ...

if __name__ == '__main__':
    bot = InstagramDownloaderBot()
    bot.run()
