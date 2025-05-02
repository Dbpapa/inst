import requests
import json
import re
from datetime import datetime

class InstagramScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/80.0.3987.162 Mobile Safari/537.36'
        }

    def get_profile_posts(self, username: str) -> list:
        """Get public posts using mobile API endpoints"""
        try:
            # Get profile JSON data
            profile_url = f'https://www.instagram.com/{username}/?__a=1'
            response = requests.get(profile_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return []
                
            data = json.loads(re.findall(r'<script type="text/javascript">window\._sharedData = (.*);</script>', response.text)[0])
            user_id = data['entry_data']['ProfilePage'][0]['graphql']['user']['id']
            
            # Get posts JSON
            posts_url = f'https://www.instagram.com/graphql/query/?query_hash=69cba40317214236af40e7efa697781d&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A12%7D'
            posts_response = requests.get(posts_url, headers=self.headers)
            posts_data = posts_response.json()
            
            return [self._parse_post(edge['node'], username) 
                    for edge in posts_data['data']['user']['edge_owner_to_timeline_media']['edges']]
            
        except Exception as e:
            print(f"Scraping error: {e}")
            return []

    def _parse_post(self, post_data: dict, username: str) -> dict:
        """Parse raw post data into usable format"""
        return {
            'username': username,
            'caption': post_data['edge_media_to_caption']['edges'][0]['node']['text'] if post_data['edge_media_to_caption']['edges'] else "",
            'date': datetime.fromtimestamp(post_data['taken_at_timestamp']).strftime('%Y-%m-%d %H:%M'),
            'image_url': post_data['display_url'],
            'video_url': post_data.get('video_url', ''),
            'is_video': post_data['is_video'],
            'shortcode': post_data['shortcode']
        }
