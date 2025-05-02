import instaloader
import requests
import os
import time
from datetime import datetime

class InstagramScraper:
    def __init__(self):
        self.loader = instaloader.Instaloader(
            quiet=True,
            download_video_thumbnails=False,
            save_metadata=False
        )
        
        # Instagram credentials from environment
        self.insta_user = os.getenv('INSTAGRAM_USERNAME')
        self.insta_pass = os.getenv('INSTAGRAM_PASSWORD')
        
        if not self.insta_user or not self.insta_pass:
            raise ValueError("Instagram credentials not found in environment variables")
            
        try:
            self.loader.login(self.insta_user, self.insta_pass)
            print("Successfully logged in to Instagram")
        except Exception as e:
            print(f"Instagram login failed: {e}")
            raise

    def get_profile_posts(self, username: str) -> list:
        """Get recent posts from public profile with rate limiting"""
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            if profile.is_private:
                return []
                
            # Rate limiting
            time.sleep(2)  # 2-second delay between requests
            
            return [{
                'url': post.url,
                'display_url': post.url,
                'thumbnail_url': post.video_url if post.is_video else post.url,
                'caption': post.caption[:2000] if post.caption else "",
                'date': post.date_utc.strftime('%Y-%m-%d %H:%M'),
                'is_video': post.is_video,
                'username': username,
                'shortcode': post.shortcode
            } for post in profile.get_posts()][:6]  # Limit to 6 posts
            
        except instaloader.exceptions.QueryReturnedBadRequestException:
            print("Instagram rate limit exceeded - add delays")
            return []
        except Exception as e:
            print(f"Scraping error: {e}")
            return []
            
    def download_media(self, url: str) -> str:
        """Download media from URL with error handling"""
        try:
            if not os.path.exists('downloads'):
                os.makedirs('downloads')
                
            filename = url.split('/')[-1].split('?')[0]
            filepath = f"downloads/{filename}"
            
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return filepath
            
        except requests.exceptions.RequestException as e:
            print(f"Download error: {e}")
            raise
