"""
Apify Client for Social Media Scraping
Integrates with Apify API for X (Twitter), Instagram, TikTok scraping
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import time


class ApifyClient:
    """Client for Apify API social media scraping"""
    
    def __init__(self, api_token: str):
        """Initialize Apify client with API token"""
        self.api_token = api_token
        self.base_url = "https://api.apify.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_twitter_posts(self, handle: str, max_posts: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape Twitter/X posts for a given handle
        Uses Apify's Twitter scraper actor
        """
        try:
            actor_id = "61RPP7dywgRE7fNSL"  # Apify's Twitter Scraper
            
            input_data = {
                "handles": [handle.lstrip("@")],
                "maxPostsPerHandle": max_posts,
                "includeReplies": False,
                "includeRetweets": True,
                "sort": "Latest"
            }
            
            # Start actor run
            run_data = {
                "actId": actor_id,
                "waitForFinish": 300,  # Wait up to 5 minutes
                "memory": 4096,
                "timeout": 3600,
                "input": input_data
            }
            
            response = self.session.post(
                f"{self.base_url}/acts/{actor_id}/runs",
                json=input_data,
                timeout=30
            )
            
            if response.status_code != 201:
                return []
            
            run_info = response.json()
            run_id = run_info.get("data", {}).get("id")
            
            if not run_id:
                return []
            
            # Poll for completion
            posts = self._wait_and_fetch_results(run_id)
            return posts
            
        except Exception as e:
            print(f"Error scraping Twitter: {str(e)}")
            return []
    
    def scrape_instagram_posts(self, username: str, max_posts: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape Instagram posts for a given username
        Uses Apify's Instagram scraper actor
        """
        try:
            actor_id = "sKjT8jvw92wZj7c3N"  # Apify's Instagram Scraper
            
            input_data = {
                "usernames": [username.lstrip("@")],
                "resultsLimit": max_posts,
                "resultsType": "posts"
            }
            
            response = self.session.post(
                f"{self.base_url}/acts/{actor_id}/runs",
                json=input_data,
                timeout=30
            )
            
            if response.status_code != 201:
                return []
            
            run_info = response.json()
            run_id = run_info.get("data", {}).get("id")
            
            if not run_id:
                return []
            
            posts = self._wait_and_fetch_results(run_id)
            return posts
            
        except Exception as e:
            print(f"Error scraping Instagram: {str(e)}")
            return []
    
    def scrape_tiktok_posts(self, username: str, max_posts: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape TikTok posts for a given username
        Uses Apify's TikTok scraper actor
        """
        try:
            actor_id = "cjW3bNzV9J7z7c3F"  # Apify's TikTok Scraper
            
            input_data = {
                "usernames": [username.lstrip("@")],
                "resultsLimit": max_posts,
                "resultsType": "posts"
            }
            
            response = self.session.post(
                f"{self.base_url}/acts/{actor_id}/runs",
                json=input_data,
                timeout=30
            )
            
            if response.status_code != 201:
                return []
            
            run_info = response.json()
            run_id = run_info.get("data", {}).get("id")
            
            if not run_id:
                return []
            
            posts = self._wait_and_fetch_results(run_id)
            return posts
            
        except Exception as e:
            print(f"Error scraping TikTok: {str(e)}")
            return []
    
    def _wait_and_fetch_results(self, run_id: str, timeout: int = 300) -> List[Dict[str, Any]]:
        """Wait for actor run to complete and fetch results"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Get run status
                status_response = self.session.get(
                    f"{self.base_url}/actor-runs/{run_id}",
                    timeout=10
                )
                
                if status_response.status_code != 200:
                    time.sleep(2)
                    continue
                
                run_status = status_response.json()
                status = run_status.get("data", {}).get("status")
                
                if status == "SUCCEEDED":
                    # Fetch results from dataset
                    dataset_id = run_status.get("data", {}).get("defaultDatasetId")
                    if dataset_id:
                        items = self._fetch_dataset_items(dataset_id)
                        return items
                    return []
                
                elif status in ["FAILED", "TIMED_OUT", "ABORTED"]:
                    return []
                
                # Still running, wait and retry
                time.sleep(3)
                
            except Exception as e:
                print(f"Error checking run status: {str(e)}")
                time.sleep(2)
        
        return []
    
    def _fetch_dataset_items(self, dataset_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch items from an Apify dataset"""
        try:
            response = self.session.get(
                f"{self.base_url}/datasets/{dataset_id}/items",
                params={"limit": limit, "format": "json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            return []
            
        except Exception as e:
            print(f"Error fetching dataset: {str(e)}")
            return []
    
    def verify_handle_exists(self, handle: str, platform: str = "twitter") -> bool:
        """Verify if a handle exists on social media platform"""
        try:
            if platform.lower() == "twitter":
                # Try to fetch a small sample to verify handle exists
                posts = self.scrape_twitter_posts(handle, max_posts=1)
                return len(posts) > 0
            
            elif platform.lower() == "instagram":
                posts = self.scrape_instagram_posts(handle, max_posts=1)
                return len(posts) > 0
            
            elif platform.lower() == "tiktok":
                posts = self.scrape_tiktok_posts(handle, max_posts=1)
                return len(posts) > 0
            
            return False
            
        except Exception:
            return False
    
    def normalize_post_data(self, posts: List[Dict], platform: str) -> List[Dict[str, Any]]:
        """Normalize post data to standard format across platforms"""
        normalized = []
        
        for post in posts:
            try:
                if platform.lower() == "twitter":
                    norm_post = {
                        "platform": "twitter",
                        "post_id": post.get("id_str") or post.get("id"),
                        "username": post.get("author", {}).get("name") or post.get("user", {}).get("screen_name"),
                        "text": post.get("full_text") or post.get("text"),
                        "timestamp": post.get("created_at"),
                        "likes": post.get("favorite_count", 0),
                        "retweets": post.get("retweet_count", 0),
                        "replies": post.get("reply_count", 0),
                        "url": f"https://twitter.com/{post.get('user', {}).get('screen_name')}/status/{post.get('id_str')}",
                        "media_urls": [m.get("media_url_https") for m in post.get("entities", {}).get("media", [])],
                        "verified": post.get("user", {}).get("verified", False),
                        "raw_data": post
                    }
                
                elif platform.lower() == "instagram":
                    norm_post = {
                        "platform": "instagram",
                        "post_id": post.get("id"),
                        "username": post.get("owner", {}).get("username") or post.get("username"),
                        "text": post.get("caption"),
                        "timestamp": post.get("timestamp"),
                        "likes": post.get("likes_count", 0),
                        "comments": post.get("comments_count", 0),
                        "url": post.get("url"),
                        "media_urls": [post.get("display_url")] if post.get("display_url") else [],
                        "verified": post.get("owner", {}).get("is_verified", False),
                        "raw_data": post
                    }
                
                elif platform.lower() == "tiktok":
                    norm_post = {
                        "platform": "tiktok",
                        "post_id": post.get("id"),
                        "username": post.get("author", {}).get("uniqueId") or post.get("author_name"),
                        "text": post.get("description"),
                        "timestamp": post.get("createTime"),
                        "likes": post.get("digg_count", 0),
                        "comments": post.get("comment_count", 0),
                        "shares": post.get("share_count", 0),
                        "url": post.get("video", {}).get("downloadAddr"),
                        "media_urls": [post.get("video", {}).get("downloadAddr")] if post.get("video") else [],
                        "verified": post.get("author", {}).get("verified", False),
                        "raw_data": post
                    }
                
                else:
                    continue
                
                normalized.append(norm_post)
                
            except Exception as e:
                print(f"Error normalizing post: {str(e)}")
                continue
        
        return normalized
