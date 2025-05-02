from pymongo import MongoClient
from datetime import datetime
import os

class MongoDB:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client.instagram_bot
        
    def log_user(self, user_id: int, username: str):
        self.db.users.update_one(
            {'user_id': user_id},
            {'$set': {
                'last_seen': datetime.utcnow(),
                'username': username
            }},
            upsert=True
        )
        
    def log_download(self, user_id: int, insta_username: str):
        self.db.downloads.insert_one({
            'user_id': user_id,
            'instagram_user': insta_username,
            'timestamp': datetime.utcnow()
        })
