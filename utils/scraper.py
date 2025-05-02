import instaloader
import requests
import os
from datetime import datetime

class InstagramScraper:
    def __init__(self):
        self.loader = instaloader.Instaloader(
            quiet=True,
            download_video_thumbnails=False,
            save_metadata=False
        )
        
    def get_profile_posts(self, username: str) -> list:
        """Get recent posts from public profile"""
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            if profile.is_private:
                return []
                
            return [{
                'url': post.url,
                'display_url': post.url,
                'thumbnail_url': post.video_url if post.is_video else post.url,
                'caption': post.caption[:2000] if post.caption else "",
                'date': post.date_utc.strftime('%Y-%m-%d %H:%M'),
                'is_video': post.is_video,
                'username': username,
                'shortcode': post.shortcode
            } for post in profile.get_posts()][:12]  # Get first 12 posts
            
        except Exception as e:
            print(f"Scraping error: {e}")
            return []
            
    def download_media(self, url: str) -> str:
        """Download media from URL"""
        try:
            if not os.path.exists('downloads'):
                os.makedirs('downloads')
                
            filename = url.split('/')[-1].split('?')[0]
            filepath = f"downloads/{filename}"
            
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return filepath
            
        except Exception as e:
            print(f"Download error: {e}")
            raise
