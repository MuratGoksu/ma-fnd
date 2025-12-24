"""
Twitter/X Crawler Agent
Fetches tweets from X (Twitter) platform for fake news detection
"""
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False


class TwitterCrawlerAgent:
    """
    Twitter/X Crawler Agent
    Fetches tweets using Twitter API v2
    """
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Twitter API client"""
        if not TWEEPY_AVAILABLE:
            raise ImportError(
                "tweepy is required for Twitter crawler. "
                "Install it with: pip install tweepy"
            )
        
        # Twitter API v2 credentials
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        if bearer_token:
            # Use Bearer Token (simpler, read-only)
            self.client = tweepy.Client(bearer_token=bearer_token)
        elif api_key and api_secret and access_token and access_token_secret:
            # Use OAuth 1.0a (full access)
            auth = tweepy.OAuth1UserHandler(
                api_key, api_secret, access_token, access_token_secret
            )
            self.client = tweepy.API(auth)
        else:
            raise ValueError(
                "Twitter API credentials not found. "
                "Set TWITTER_BEARER_TOKEN or TWITTER_API_KEY/API_SECRET/ACCESS_TOKEN/ACCESS_TOKEN_SECRET"
            )
    
    def fetch_news(
        self,
        tweet_id: Optional[str] = None,
        username: Optional[str] = None,
        query: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Fetch tweet(s) from Twitter
        
        Args:
            tweet_id: Specific tweet ID to fetch
            username: Username to fetch latest tweets from
            query: Search query (e.g., "fake news")
            max_results: Maximum number of results (default: 10)
        
        Returns:
            Dictionary with tweet data in news item format
        """
        if not self.client:
            raise RuntimeError("Twitter client not initialized")
        
        try:
            if tweet_id:
                # Fetch specific tweet
                tweet = self._fetch_tweet_by_id(tweet_id)
                return self._tweet_to_news_item(tweet)
            
            elif username:
                # Fetch user's latest tweets
                tweets = self._fetch_user_tweets(username, max_results)
                if tweets:
                    # Return the most recent tweet
                    return self._tweet_to_news_item(tweets[0])
                else:
                    raise ValueError(f"No tweets found for user: {username}")
            
            elif query:
                # Search tweets
                tweets = self._search_tweets(query, max_results)
                if tweets:
                    return self._tweet_to_news_item(tweets[0])
                else:
                    raise ValueError(f"No tweets found for query: {query}")
            
            else:
                raise ValueError("Either tweet_id, username, or query must be provided")
        
        except tweepy.TooManyRequests:
            raise RuntimeError("Twitter API rate limit exceeded. Please wait and try again.")
        except tweepy.Unauthorized:
            raise RuntimeError("Twitter API authentication failed. Check your credentials.")
        except tweepy.NotFound:
            raise ValueError("Tweet or user not found")
        except Exception as e:
            raise RuntimeError(f"Twitter API error: {str(e)}")
    
    def _fetch_tweet_by_id(self, tweet_id: str) -> Any:
        """Fetch a specific tweet by ID"""
        if isinstance(self.client, tweepy.Client):
            # Twitter API v2
            tweet = self.client.get_tweet(
                tweet_id,
                tweet_fields=["created_at", "author_id", "public_metrics", "text", "entities"]
            )
            return tweet.data
        else:
            # Twitter API v1.1
            return self.client.get_status(tweet_id, tweet_mode="extended")
    
    def _fetch_user_tweets(self, username: str, max_results: int = 10) -> List[Any]:
        """Fetch user's latest tweets"""
        if isinstance(self.client, tweepy.Client):
            # Twitter API v2
            # First get user ID
            user = self.client.get_user(username=username)
            if not user.data:
                raise ValueError(f"User not found: {username}")
            
            user_id = user.data.id
            
            # Fetch tweets
            tweets = self.client.get_users_tweets(
                user_id,
                max_results=min(max_results, 100),  # API limit
                tweet_fields=["created_at", "author_id", "public_metrics", "text", "entities"]
            )
            return tweets.data if tweets.data else []
        else:
            # Twitter API v1.1
            tweets = self.client.user_timeline(
                screen_name=username,
                count=max_results,
                tweet_mode="extended"
            )
            return tweets
    
    def _search_tweets(self, query: str, max_results: int = 10) -> List[Any]:
        """Search tweets by query"""
        if isinstance(self.client, tweepy.Client):
            # Twitter API v2
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),  # API limit
                tweet_fields=["created_at", "author_id", "public_metrics", "text", "entities"]
            )
            return tweets.data if tweets.data else []
        else:
            # Twitter API v1.1
            tweets = self.client.search_tweets(
                q=query,
                count=max_results,
                tweet_mode="extended"
            )
            return tweets
    
    def _tweet_to_news_item(self, tweet: Any) -> Dict[str, Any]:
        """Convert tweet object to news item format"""
        if isinstance(self.client, tweepy.Client):
            # Twitter API v2 format
            text = tweet.text if hasattr(tweet, 'text') else str(tweet)
            tweet_id = tweet.id if hasattr(tweet, 'id') else str(tweet)
            created_at = tweet.created_at if hasattr(tweet, 'created_at') else datetime.utcnow()
            author_id = tweet.author_id if hasattr(tweet, 'author_id') else None
            
            # Build URL
            link = f"https://twitter.com/i/web/status/{tweet_id}"
            
            # Extract media if available
            image_url = None
            if hasattr(tweet, 'entities') and tweet.entities:
                if 'media' in tweet.entities:
                    media = tweet.entities['media']
                    if media and len(media) > 0:
                        image_url = media[0].get('media_url_https') if isinstance(media[0], dict) else None
            
        else:
            # Twitter API v1.1 format
            text = tweet.full_text if hasattr(tweet, 'full_text') else tweet.text
            tweet_id = tweet.id_str
            created_at = tweet.created_at
            author_id = tweet.user.id_str if hasattr(tweet, 'user') else None
            
            # Build URL
            username = tweet.user.screen_name if hasattr(tweet, 'user') else "unknown"
            link = f"https://twitter.com/{username}/status/{tweet_id}"
            
            # Extract media
            image_url = None
            if hasattr(tweet, 'entities') and 'media' in tweet.entities:
                media = tweet.entities['media']
                if media and len(media) > 0:
                    image_url = media[0].get('media_url_https')
        
        # Clean text (remove URLs, mentions, etc.)
        cleaned_text = self._clean_tweet_text(text)
        
        # Create headline from first part of tweet
        headline = cleaned_text[:100] + "..." if len(cleaned_text) > 100 else cleaned_text
        
        return {
            "id": f"twitter-{tweet_id}",
            "headline": headline,
            "text": cleaned_text,
            "link": link,
            "source": "twitter",
            "author_id": author_id,
            "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
            "image_url": image_url,
            "platform": "twitter"
        }
    
    def _clean_tweet_text(self, text: str) -> str:
        """Clean tweet text - remove URLs, RT prefixes, etc."""
        import re
        
        # Remove RT prefix
        text = re.sub(r'^RT\s+@\w+:\s+', '', text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()

