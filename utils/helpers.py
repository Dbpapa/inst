from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client.instagram_bot
        self.users = self.db.users
        self.downloads = self.db.downloads

    def save_user_data(self, user_id, username, first_name):
        self.users.update_one(
            {'user_id': user_id},
            {'$set': {
                'username': username,
                'first_name': first_name,
                'last_activity': datetime.utcnow()
            }},
            upsert=True
        )

    def get_user_data(self, user_id):
        return self.users.find_one({'user_id': user_id})

    def log_download(self, user_id, instagram_user):
        self.downloads.update_one(
            {'user_id': user_id},
            {'$inc': {'download_count': 1},
             '$set': {
                 'last_download': datetime.utcnow(),
                 'instagram_user': instagram_user
             }},
            upsert=True
        )

# Initialize database connection
db_manager = DatabaseManager()
