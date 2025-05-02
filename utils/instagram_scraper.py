import os
import requests
from bs4 import BeautifulSoup
import instaloader
from datetime import datetime
from urllib.parse import urlparse
import time
from dotenv import load_dotenv
from utils.helpers import db_manager

load_dotenv()

class InstagramScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.loader = instaloader.Instaloader(
            quiet=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False
        )
        
    # ... [Keep all the instagram_scraper.py code from previous answer] ...

    def download_post(self, shortcode):
        try:
            # ... [existing download code] ...
            db_manager.log_download(user_id, post.owner_username)
            return filename
        except Exception as e:
            db_manager.downloads.update_one(
                {'shortcode': shortcode},
                {'$inc': {'errors': 1}},
                upsert=True
            )
            raise
