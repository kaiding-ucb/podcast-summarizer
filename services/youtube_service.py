from googleapiclient.discovery import build
import yaml
import re
from typing import List, Dict, Any
from datetime import datetime, timedelta

class YouTubeService:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        self.api_key = config['youtube_api_key']
        self.discovery_days_back = config.get('discovery_days_back', 7)
        self.video_length_excluded = config.get('video_length_excluded', 10) * 60  # Convert minutes to seconds
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return url  # Return as-is if no pattern matches

    def should_exclude_from_analysis(self, duration_seconds: int) -> bool:
        """Check if video should be excluded from Gemini analysis due to length"""
        return duration_seconds < self.video_length_excluded

    def get_video_info(self, video_url: str) -> Dict[str, Any]:
        """Get video information including title and duration"""
        video_id = self.extract_video_id(video_url)
        
        try:
            response = self.youtube.videos().list(
                part='snippet,contentDetails',
                id=video_id
            ).execute()
            
            if response['items']:
                video = response['items'][0]
                snippet = video['snippet']
                content_details = video['contentDetails']
                
                # Parse duration (PT4M13S -> 253 seconds)
                duration_str = content_details['duration']
                duration_seconds = self._parse_duration(duration_str)
                
                return {
                    'video_id': video_id,
                    'title': snippet['title'],
                    'channel_name': snippet['channelTitle'],
                    'duration': duration_seconds,
                    'published_at': snippet['publishedAt'],
                    'url': video_url,
                    'excluded_from_analysis': self.should_exclude_from_analysis(duration_seconds)
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

    def get_channel_videos(self, channel_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get recent videos from a channel"""
        try:
            # First, get the channel's uploads playlist ID
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if not channel_response['items']:
                return []
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from the uploads playlist
            playlist_response = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=max_results
            ).execute()
            
            videos = []
            for item in playlist_response['items']:
                video_id = item['snippet']['resourceId']['videoId']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                # Get additional video details
                video_info = self.get_video_info(video_url)
                if video_info:
                    videos.append(video_info)
            
            return videos
            
        except Exception as e:
            print(f"Error getting channel videos: {e}")
            return []

    def discover_new_videos(self, channels: List[Dict[str, str]], max_per_channel: int = 5) -> List[Dict[str, Any]]:
        """Discover new videos from trusted channels"""
        all_videos = []
        
        for channel in channels:
            channel_id = channel['channel_id']
            channel_name = channel['name']
            
            videos = self.get_channel_videos(channel_id, max_per_channel)
            for video in videos:
                video['channel_name'] = channel_name  # Override with our friendly name
                video['channel_id'] = channel_id  # Add channel ID
                all_videos.append(video)
        
        # Sort by published date (newest first)
        all_videos.sort(key=lambda x: x['published_at'], reverse=True)
        
        return all_videos
    
    def get_recent_channel_videos(self, channels: List[Dict[str, str]], days_back: int = None) -> List[Dict[str, Any]]:
        """Get recent videos from channels within specified days"""
        if days_back is None:
            days_back = self.discovery_days_back
            
        all_videos = []
        published_after = (datetime.now() - timedelta(days=days_back)).isoformat() + 'Z'
        
        for channel in channels:
            channel_id = channel['channel_id']
            channel_name = channel['name']
            
            try:
                # Use search API to get recent videos with date filter
                search_response = self.youtube.search().list(
                    part='snippet',
                    channelId=channel_id,
                    type='video',
                    order='date',
                    publishedAfter=published_after,
                    maxResults=50  # Get more videos since we're filtering by date
                ).execute()
                
                for item in search_response['items']:
                    video_id = item['id']['videoId']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Get additional video details
                    video_info = self.get_video_info(video_url)
                    if video_info:
                        video_info['channel_name'] = channel_name
                        video_info['channel_id'] = channel_id
                        all_videos.append(video_info)
                
            except Exception as e:
                print(f"Error getting recent videos for channel {channel_name}: {e}")
                continue
        
        # Sort by published date (newest first)
        all_videos.sort(key=lambda x: x['published_at'], reverse=True)
        
        return all_videos

    def _parse_duration(self, duration_str: str) -> int:
        """Parse YouTube duration format (PT4M13S) to seconds"""
        import re
        
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(duration_str)
        
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            
            return hours * 3600 + minutes * 60 + seconds
        
        return 0