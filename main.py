import os
import logging
import re
import socket
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    Defaults
)
from telegram.utils.request import Request
from telegram.error import NetworkError
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

class CustomRequest(Request):
    """Custom request class with keep-alive settings"""
    def _create_connection(self, *args, **kwargs):
        conn = super()._create_connection(*args, **kwargs)
        sock = conn.sock
        # TCP Keep-Alive settings
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
        return conn

class InstaBot:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.admin_id = os.getenv('ADMIN_ID')
        
        # Configure connection pool
        self.request = CustomRequest(
            con_pool_size=8,
            connect_timeout=30,
            read_timeout=30
        )
        
        # Initialize updater with custom settings
        self.updater = Updater(
            token=self.bot_token,
            request=self.request,
            defaults=Defaults(run_async=True),
            use_context=True
        )
        
        self.dispatcher = self.updater.dispatcher
        self.scraper = InstagramScraper()
        self.db = MongoDB()

        # Register handlers
        self.dispatcher.add_handler(CommandHandler('start', self.start))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_username))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Error handling
        self.dispatcher.add_error_handler(self.error_handler)

    # [Keep all other methods from previous version]
    
    def error_handler(self, update: Update, context: CallbackContext):
        error = context.error
        if isinstance(error, NetworkError):
            logger.error("Network error detected, restarting...")
            time.sleep(5)
            self.restart_bot()
        else:
            logger.error(f"Unhandled error: {error}", exc_info=True)
            if update:
                context.bot.send_message(
                    chat_id=self.admin_id,
                    text=f"Error occurred: {error}"
                )

    def restart_bot(self):
        """Graceful restart mechanism"""
        self.updater.stop()
        self.updater.start_polling()
        logger.info("Bot restarted after network failure")

if __name__ == '__main__':
    bot = InstaBot()
    bot.updater.start_polling()
    logger.info("Bot is running...")
    bot.updater.idle()
