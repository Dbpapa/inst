import os
import logging
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)
from utils.scraper import InstagramScraper
from dotenv import load_dotenv

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
        self.updater = Updater(token=self.bot_token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.scraper = InstagramScraper()
        
        # Register handlers
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_username))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Error handling
        self.dispatcher.add_error_handler(self.error_handler)

    def start(self, update: Update, context: CallbackContext):
        user = update.effective_user
        update.message.reply_text(
            f"👋 Hello {user.first_name}!\n"
            "Send me a public Instagram username to download their posts.\n\n"
            "⚠️ Works only with public accounts!"
        )

    def handle_username(self, update: Update, context: CallbackContext):
        username = update.message.text.strip().replace('@', '')
        
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
            update.message.reply_text("⚠️ Failed to fetch posts. Try again later.")

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
                    video=post['video_url'],
                    caption=f"🎥 {post['caption']}\n📅 {post['date']}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                update.message.reply_photo(
                    photo=post['image_url'],
                    caption=f"📸 {post['caption']}\n📅 {post['date']}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        except Exception as e:
            logger.error(f"Error displaying post: {e}")
            update.message.reply_text("⚠️ Failed to load media. Trying next post...")
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
            media_url = post['video_url'] if post['is_video'] else post['image_url']
            
            if post['is_video']:
                context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=media_url,
                    caption=f"✅ Downloaded from @{post['username']}"
                )
            else:
                context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=media_url,
                    caption=f"✅ Downloaded from @{post['username']}"
                )
            
            query.edit_message_caption(caption="☑️ Download complete!")

        except Exception as e:
            logger.error(f"Download failed: {e}")
            query.edit_message_caption(caption="❌ Failed to download")

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
