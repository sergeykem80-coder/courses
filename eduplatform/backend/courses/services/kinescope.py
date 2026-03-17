"""
Kinescope video service integration.

Provides methods for generating embed URLs and managing videos.
"""
import requests
from django.conf import settings


class KinescopeService:
    """Service for interacting with Kinescope.io API."""
    
    BASE_URL = "https://api.kinescope.io/2.0"
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or settings.KINESCOPE_API_TOKEN
        self.headers = {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
    
    def get_video_info(self, video_id: str) -> dict:
        """Get video metadata from Kinescope."""
        if not self.api_token:
            return {"error": "API token not configured"}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/videos/{video_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    @staticmethod
    def generate_embed_url(video_id: str, options: dict = None) -> str:
        """
        Generate embed URL for Kinescope video.
        
        Args:
            video_id: Kinescope video ID
            options: Optional parameters like autoplay, controls, etc.
        
        Returns:
            Full embed URL with query parameters
        """
        base_url = f"https://kinescope.io/embed/{video_id}"
        
        params = {
            "autoplay": "0",
            "controls": "1",
            **(options or {})
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query_string}"
    
    @staticmethod
    def generate_embed_html(video_id: str, options: dict = None, 
                           additional_attrs: dict = None) -> str:
        """
        Generate complete iframe HTML for embedding.
        
        Args:
            video_id: Kinescope video ID
            options: Embed URL parameters
            additional_attrs: Additional iframe attributes
        
        Returns:
            Complete iframe HTML string
        """
        embed_url = KinescopeService.generate_embed_url(video_id, options)
        
        attrs = {
            'frameborder': '0',
            'allow': 'autoplay; fullscreen; picture-in-picture',
            'allowfullscreen': '',
            'loading': 'lazy',
            'style': 'width:100%; aspect-ratio:16/9; border:0;',
            'referrerpolicy': 'strict-origin-when-cross-origin',
            **(additional_attrs or {})
        }
        
        attrs_string = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
        return f'<iframe src="{embed_url}" {attrs_string}></iframe>'
    
    @staticmethod
    def extract_video_id(url: str) -> str:
        """
        Extract video ID from Kinescope URL.
        
        Supports formats:
        - https://kinescope.io/VIDEO_ID
        - https://kinescope.io/embed/VIDEO_ID
        - https://kinescope.io/embed/VIDEO_ID?...
        """
        if '/embed/' in url:
            # Extract from embed URL
            parts = url.split('/embed/')
            video_id = parts[1].split('?')[0].split('/')[0]
        elif 'kinescope.io/' in url:
            # Extract from regular URL
            parts = url.split('kinescope.io/')
            video_id = parts[1].split('?')[0].split('/')[0]
        else:
            # Assume it's already just the ID
            video_id = url
        
        return video_id.strip('/')
