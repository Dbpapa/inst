import instaloader
import requests
import re
import os

class InstagramScraper:
    def __init__(self):
        self.loader = instaloader.Instaloader(
            quiet=True,
            download_video_thumbnails=False,
            save_metadata=False
        )
        
    def get_profile_posts(self, username: str) -> list:
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            if profile.is_private:
                return []
                
            return [{
                'url': post.url,
                'caption': post.caption if post.caption else "",
                'is_video': post.is_video,
                'username': username,
                'timestamp': post.date_utc
            } for post in profile.get_posts()][:50]  # Limit to 50 posts
            
        except Exception as e:
            print(f"Scraping error: {e}")
            return []
            
    def download_media(self, url: str) -> str:
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
