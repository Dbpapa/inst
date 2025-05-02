import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv
from utils.instagram_scraper import InstagramScraper
from utils.database import MongoDB

# Load environment variables
load_dotenv()

# Initialize components
db = MongoDB()
scraper = InstagramScraper()

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
        
        # Register handlers
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_username))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Error handling
        self.dispatcher.add_error_handler(self.error_handler)

    def start(self, update: Update, context: CallbackContext):
        user = update.effective_user
        update.message.reply_text(f"👋 Hello {user.first_name}!\nSend me an Instagram username to download their posts.")
        db.log_user(user.id, user.username)

    def handle_username(self, update: Update, context: CallbackContext):
        username = update.message.text.strip()
        
        if not self.validate_username(username):
            update.message.reply_text("❌ Invalid username. Use only letters, numbers and underscores.")
            return
            
        try:
            update.message.reply_text("⏳ Fetching profile...")
            posts = scraper.get_profile_posts(username)
            
            if not posts:
                update.message.reply_text("❌ No posts found or account is private.")
                return
                
            context.user_data['posts'] = posts
            context.user_data['current_index'] = 0
            
            self.show_post(update, context, 0)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            update.message.reply_text("⚠️ Service unavailable. Try again later.")

    def show_post(self, update: Update, context: CallbackContext, index: int):
        posts = context.user_data['posts']
        
        if index >= len(posts):
            update.callback_query.answer()
            update.callback_query.edit_message_text("✅ Reached end of posts!")
            return
            
        post = posts[index]
        keyboard = [
            [
                InlineKeyboardButton("⬅️", callback_data=f"prev_{index}"),
                InlineKeyboardButton("⬇️ Download", callback_data=f"dl_{index}"),
                InlineKeyboardButton("➡️", callback_data=f"next_{index}"),
            ]
        ]
        
        try:
            if post['is_video']:
                update.effective_message.reply_video(
                    video=post['url'],
                    caption=f"🎥 {post['caption']}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
            else:
                update.effective_message.reply_photo(
                    photo=post['url'],
                    caption=f"📸 {post['caption']}",
                    reply_markup=InlineKeyboardMarkup(keyboard))
                    
        except Exception as e:
            logger.error(f"Media error: {e}")
            update.effective_message.reply_text("⚠️ Failed to load media.")

    def button_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        data = query.data.split('_')
        action = data[0]
        index = int(data[1])
        
        posts = context.user_data.get('posts', [])
        
        if action == 'prev':
            new_index = max(0, index-1)
        elif action == 'next':
            new_index = min(len(posts)-1, index+1)
        elif action == 'dl':
            self.download_post(update, context, index)
            return
            
        context.user_data['current_index'] = new_index
        self.show_post(update, context, new_index)

    def download_post(self, update: Update, context: CallbackContext, index: int):
        post = context.user_data['posts'][index]
        
        try:
            file_path = scraper.download_media(post['url'])
            db.log_download(update.effective_user.id, post['username'])
            
            if post['is_video']:
                context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=open(file_path, 'rb'),
                    caption="✅ Download complete!"
                )
            else:
                context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=open(file_path, 'rb'),
                    caption="✅ Download complete!"
                )
                
            os.remove(file_path)
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            update.effective_message.reply_text("❌ Download failed. Try again.")

    def validate_username(self, username: str) -> bool:
        return bool(re.match(r'^[a-zA-Z0-9_.]{1,30}$', username))

    def error_handler(self, update: Update, context: CallbackContext):
        logger.error(msg="Exception:", exc_info=context.error)
        update.effective_message.reply_text("⚠️ Bot encountered an error. Try again.")

    def run(self):
        self.updater.start_polling()
        logger.info("Bot running...")
        self.updater.idle()

if __name__ == '__main__':
    bot = InstaBot()
    bot.run()
