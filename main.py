import os
import logging
from telegram import Update, Bot
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class InstaBot:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.admin_id = os.getenv('ADMIN_ID')
        
        # Configure custom request with connection pool
        self.request = Request(
            con_pool_size=8,
            connect_timeout=30,
            read_timeout=30
        )
        
        # Create Bot instance with custom request
        self.bot = Bot(
            token=self.bot_token,
            request=self.request
        )
        
        # Initialize Updater with the custom Bot
        self.updater = Updater(
            bot=self.bot,
            use_context=True
        )
        
        self.dispatcher = self.updater.dispatcher
        self.scraper = InstagramScraper()
        self.db = MongoDB()

        # Register handlers
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_username))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Error handling
        self.dispatcher.add_error_handler(self.error_handler)

    # [Keep all other methods unchanged]

    def run(self):
        self.updater.start_polling()
        logger.info("Bot is running...")
        self.updater.idle()

if __name__ == '__main__':
    bot = InstaBot()
    bot.run()
