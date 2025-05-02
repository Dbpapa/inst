    def handle_username(self, update: Update, context: CallbackContext):
        """Process Instagram username input"""
        username = update.message.text.strip().replace('@', '')
        
        if not self.valid_username(username):
            update.message.reply_text("❌ Invalid Instagram username format!")
            return

        try:
            update.message.reply_text(f"🔍 Searching for @{username}...")
            
            # Get Instagram posts
            posts = self.scraper.get_profile_posts(username)
            if not posts:
                update.message.reply_text("❌ No public posts found or invalid account!")
                return

            # Store posts in user context
            context.user_data['posts'] = posts
            context.user_data['current_index'] = 0
            
            # Show first post
            self.show_post(update, context, 0)

        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            update.message.reply_text("⚠️ Failed to retrieve posts. Please try again later.")

    def show_post(self, update: Update, context: CallbackContext, index: int):
        """Display post with navigation buttons"""
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
                    caption=f"🎥 {post['caption']}\n\n📅 {post['date']}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                update.message.reply_photo(
                    photo=post['display_url'],
                    caption=f"📸 {post['caption']}\n\n📅 {post['date']}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        except Exception as e:
            logger.error(f"Error displaying post: {e}")
            update.message.reply_text("⚠️ Failed to display post. Trying next one...")
            self.show_post(update, context, (index + 1) % len(posts))

    def button_handler(self, update: Update, context: CallbackContext):
        """Handle inline keyboard buttons"""
        query = update.callback_query
        query.answer()
        
        data = query.data.split('_')
        action = data[0]
        index = int(data[1])
        posts = context.user_data.get('posts', [])

        if action == 'dl':
            self.download_post(update, context, index)
        else:
            # Handle navigation
            new_index = index
            if action == 'prev':
                new_index = max(0, index - 1)
            elif action == 'next':
                new_index = min(len(posts) - 1, index + 1)
            
            context.user_data['current_index'] = new_index
            self.show_post(update, context, new_index)

    def download_post(self, update: Update, context: CallbackContext, index: int):
        """Download and send media to user"""
        query = update.callback_query
        posts = context.user_data.get('posts', [])
        post = posts[index]
        
        try:
            query.edit_message_caption(caption="⏳ Downloading...")
            
            # Download media
            file_path = self.scraper.download_media(post['url'])
            
            # Send to user
            if post['is_video']:
                context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=open(file_path, 'rb'),
                    caption=f"✅ Downloaded from @{post['username']}\n📅 {post['date']}"
                )
            else:
                context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=open(file_path, 'rb'),
                    caption=f"✅ Downloaded from @{post['username']}\n📅 {post['date']}"
                )
            
            # Cleanup
            os.remove(file_path)
            query.edit_message_caption(caption=f"☑️ Downloaded!\n{post['caption']}")

        except Exception as e:
            logger.error(f"Download failed: {e}")
            query.edit_message_caption(caption="❌ Download failed. Please try again.")
