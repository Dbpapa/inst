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
        self.updater = Updater(token=self.bot_token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.scraper = InstagramScraper()
        self.db = MongoDB()
        
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()

        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_username))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_handler))
        
        self.dispatcher.add_error_handler(self.error_handler)

    # --- Properly Indented Methods ---
    def start(self, update: Update, context: CallbackContext):
        user = update.effective_user
        update.message.reply_text(
            f"👋 Hello {user.first_name}!\n"
            "Send me an Instagram username to download posts."
        )
        self.db.log_user(user.id, user.username)

    def handle_username(self, update: Update, context: CallbackContext):
        username = update.message.text.strip().replace('@', '')
        
        if not self.valid_username(username):
            update.message.reply_text("❌ Invalid Instagram username!")
            return

        try:
            update.message.reply_text(f"🔍 Searching for @{username}...")
            posts = self.scraper.get_profile_posts(username)
            
            if not posts:
                update.message.reply_text("❌ No public posts found!")
                return

            context.user_data['posts'] = posts
            context.user_data['current_index'] = 0
            self.show_post(update, context, 0)

        except Exception as e:
            logger.error(f"Error: {e}")
            update.message.reply_text("⚠️ Service unavailable. Try later.")

    def show_post(self, update: Update, context: CallbackContext, index: int):
        posts = context.user_data['posts']
        post = posts[index]
        
        keyboard = [
            [
                InlineKeyboardButton("⬅️", callback_data=f"prev_{index}"),
                InlineKeyboardButton("Download", callback_data=f"dl_{index}"),
                InlineKeyboardButton("➡️", callback_data=f"next_{index}"),
            ]
        ]
        
        try:
            if post['is_video']:
                update.message.reply_video(
                    video=post['thumbnail_url'],
                    caption=f"🎥 {post['caption']}\n📅 {post['date']}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                update.message.reply_photo(
                    photo=post['display_url'],
                    caption=f"📸 {post['caption']}\n📅 {post['date']}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        except Exception as e:
            logger.error(f"Display error: {e}")
            self.show_post(update, context, (index + 1) % len(posts))

    def button_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        data = query.data.split('_')
        action = data[0]
        index = int(data[1])
        posts = context.user_data.get('posts', [])

        if action == 'dl':
            self.download_post(update, context, index)
        else:
            new_index = index
            if action == 'prev':
                new_index = max(0, index - 1)
            elif action == 'next':
                new_index = min(len(posts) - 1, index + 1)
            
            context.user_data['current_index'] = new_index
            self.show_post(update, context, new_index)

    def download_post(self, update: Update, context: CallbackContext, index: int):
        query = update.callback_query
        posts = context.user_data.get('posts', [])
        post = posts[index]
        
        try:
            query.edit_message_caption(caption="⏳ Downloading...")
            file_path = self.scraper.download_media(post['url'])
            
            if post['is_video']:
                context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=open(file_path, 'rb'),
                    caption=f"✅ Downloaded from @{post['username']}"
                )
            else:
                context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=open(file_path, 'rb'),
                    caption=f"✅ Downloaded from @{post['username']}"
                )
            
            os.remove(file_path)
            query.edit_message_caption(caption="☑️ Download complete!")

        except Exception as e:
            logger.error(f"Download failed: {e}")
            query.edit_message_caption(caption="❌ Download failed")

    def error_handler(self, update: Update, context: CallbackContext):
        logger.error(msg="Exception:", exc_info=context.error)
        if update:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ An error occurred. Please try again."
            )

    def run(self):
        self.updater.start_polling()
        logger.info("Bot is running...")
        self.updater.idle()

if __name__ == '__main__':
    bot = InstaBot()
    bot.run()
