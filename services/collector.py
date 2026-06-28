"""Service for collecting evidence from social media"""
from apify_client import ApifyClient
from config import APIFY_TOKEN, MAX_POSTS_PER_PLATFORM
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class CollectorService:
    """Service for collecting evidence from social media platforms"""

    def __init__(self, apify_token: str = None):
        self.token = apify_token or APIFY_TOKEN
        self.client = ApifyClient(self.token) if self.token else None

    def collect_twitter(self, handle: str) -> list:
        """Collect posts from Twitter/X"""
        if not self.client:
            logger.warning("Apify token not configured, returning empty results")
            return []
        
        try:
            # Run the apidojo/tweet-scraper actor
            run = self.client.actor("apidojo/tweet-scraper").call(run_input={
                "twitterHandles": [handle.lstrip("@")],
                "maxItems": MAX_POSTS_PER_PLATFORM,
                "sort": "Latest"
            })
            
            if not run or not run.get("defaultDatasetId"):
                logger.warning(f"No dataset returned for Twitter @{handle}")
                return []
            
            # Fetch results from the dataset
            dataset_id = run["defaultDatasetId"]
            items = list(self.client.dataset(dataset_id).list_items().items)
            
            logger.info(f"Collected {len(items)} posts from Twitter @{handle}")
            return items
        except Exception as e:
            logger.error(f"Error collecting Twitter posts: {e}")
            return []

    def collect_instagram(self, username: str) -> list:
        """Collect posts from Instagram"""
        if not self.client:
            logger.warning("Apify token not configured, returning empty results")
            return []
        
        try:
            # Run the instagram-scraper actor
            run = self.client.actor("apidojo/instagram-scraper").call(run_input={
                "usernames": [username.lstrip("@")],
                "resultsLimit": MAX_POSTS_PER_PLATFORM,
            })
            
            if not run or not run.get("defaultDatasetId"):
                logger.warning(f"No dataset returned for Instagram @{username}")
                return []
            
            dataset_id = run["defaultDatasetId"]
            items = list(self.client.dataset(dataset_id).list_items().items)
            
            logger.info(f"Collected {len(items)} posts from Instagram @{username}")
            return items
        except Exception as e:
            logger.error(f"Error collecting Instagram posts: {e}")
            return []

    def collect_tiktok(self, username: str) -> list:
        """Collect posts from TikTok"""
        if not self.client:
            logger.warning("Apify token not configured, returning empty results")
            return []
        
        try:
            # Run the tiktok-scraper actor
            run = self.client.actor("clockworks/tiktok-scraper").call(run_input={
                "usernames": [username.lstrip("@")],
                "resultsLimit": MAX_POSTS_PER_PLATFORM,
            })
            
            if not run or not run.get("defaultDatasetId"):
                logger.warning(f"No dataset returned for TikTok @{username}")
                return []
            
            dataset_id = run["defaultDatasetId"]
            items = list(self.client.dataset(dataset_id).list_items().items)
            
            logger.info(f"Collected {len(items)} posts from TikTok @{username}")
            return items
        except Exception as e:
            logger.error(f"Error collecting TikTok posts: {e}")
            return []

    def collect_from_official(self, official_data: dict) -> dict:
        """Collect evidence from all social media accounts for an official"""
        collections = {
            "twitter": [],
            "instagram": [],
            "tiktok": [],
            "facebook": [],  # Placeholder - not implemented yet
        }
        
        try:
            # Collect from each platform
            if official_data.get("twitter"):
                collections["twitter"] = self.collect_twitter(official_data["twitter"])
            
            if official_data.get("instagram"):
                collections["instagram"] = self.collect_instagram(official_data["instagram"])
            
            if official_data.get("tiktok"):
                collections["tiktok"] = self.collect_tiktok(official_data["tiktok"])
            
            # Total posts collected
            total = sum(len(v) for v in collections.values())
            logger.info(f"Total {total} posts collected for {official_data.get('name')}")
            
            return collections
        except Exception as e:
            logger.error(f"Error collecting from official: {e}")
            return collections

    @staticmethod
    def normalize_post_data(post: dict, platform: str) -> dict:
        """Normalize post data across platforms"""
        return {
            "platform": platform,
            "url": post.get("url") or post.get("link"),
            "text": post.get("text") or post.get("caption"),
            "author": post.get("author") or post.get("username"),
            "created_at": post.get("created_at") or post.get("timestamp"),
            "likes": post.get("likes") or post.get("engagement_count", {}).get("likes", 0),
            "comments": post.get("comments") or post.get("engagement_count", {}).get("comments", 0),
            "shares": post.get("shares") or post.get("engagement_count", {}).get("shares", 0),
            "raw": post
        }
